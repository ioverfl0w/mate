from lib import Access
from lib import Engine

# Colors to distinguish user names to their respective location
color_palette = ['06', '10', '04']
join_msg_color = '03'
part_msg_color = '05'
kick_msg_color = '04'
nick_msg_color = '08'

class Relay:

    # Relay
    #
    # This module is used to link multiple channels together through relaying of all messages
    # It also supports PMing through the use of this module (user -> bot -> recipient)

    def __init__(self, clients=None):
        # TODO
        # handle: Disconnected messages with cooldown
        # PART messages having issues registering as relayed on certain networks, need to diagnose
        self.module = Engine.Module('Relay', ['PRIVMSG', 'JOIN', 'PART', 'KICK', 'NICK', 'QUIT', 'MODE', 'NAMELIST'], clients=clients)
        self.links = []

    # Add a Client and channel to be linked to the relay
    def link(self, client, channel):
        self.links.append({'client': client, 'location': channel, 'nicks': []})

    # Used to relay messages across all links.
    # Host - the host of the content. Will not receive a messages
    # Content - the contents of the message to be sent to the links
    def relay(self, host, content):
        ## TODO:
        # Create a feature that will notify channels when there are issues with relay
        # eg when a client is disconnected. Prevent message spam (cooldown timer)
        for link in self.links:
            if not link['client'] == host:
                link['client'].msg(link['location'], content)

    # Send private messages across networks and clients linked
    # # TODO:
    # - Specify which Network or Client that the true recipient is in the case of duplicates
    # - Specify a target for a duration of time, to eliminate starting messages with nick
    def sendPriv(self, hostClient, sender, recipient, message):
        recipient = recipient.lower()
        sent = 0
        for i in range(0, len(self.links)):
            if not self.links[i]['client'] == hostClient:
                # Because the recipient value is user provided, we will check case insensitive
                for x in range(0, len(self.links[i]['nicks'])):
                    if self.links[i]['nicks'][x].lower() == recipient:
                        c = self.getColor(self.links[i]['client'], self.links[i]['location'])
                        self.links[i]['client'].msg(recipient, '[\003' + c + sender + '\003] ' + message)
                        sent += 1
        return sent

    def message(self, client, user, channel, message):
        # Commands
        if (self.isRelayed(client, channel)):
            #Handle commands only here
            if not message.startswith('!'):
                pass

            args = message.lower().split(' ')

            if args[0] == '!cmd':
                client.notice(user[0], 'Relay Commands: (public )!list -- (PM) \'list\''
                    + (' -- (Admin public) !k[ick] !b[an]' if client.getRights(user[0]) > Access.LEVELS['USER'] else ''))

            elif args[0] == '!list':
                self.sendList(client, user)

            # Trusted users
            elif (args[0] == '!k' or args[0] == '!kick') and client.activeRights(user[0]) >= Access.LEVELS['TRUSTED']:
                if not len(args) == 3:
                    client.notice(user[0], 'Syntax: !k[ick] network user')
                else:
                    self.kickUser(client, user, args)

            # Admin users
            elif (args[0] == '!b' or args[0] == '!ban') and client.activeRights(user[0]) >= Access.LEVELS['ADMIN']:
                if not len(args) == 3:
                    client.notice(user[0], 'Syntax: !b[an] network user')
                else:
                    self.kickUser(client, user, args, ban=True)

    # Public messages inside a Relayed channel are streamed
        if (self.isRelayed(client, channel)):
            # Check for /me
            if message.startswith('\001ACTION'):
                return self.relay(client, self.constructHeading(client, channel, user[0], '\003') + ' ' + message[8:len(message) - 1])
            return self.relay(client, self.constructHeading(client, channel, user[0]) + message)

        # Handle private messages
        # # TODO:
        # Allow for PMing accross network without having to Specify
        # the target with each message
        if (channel == user[0]):
            args = message.split(' ')

            # Ensure we only accept commands from users within the client's channels
            if not self.userInChannel(client, user[0]):
                return print('(Relay) Notice: external message received from ' + user[0] + ' [' + message + ']')

            # List users in linked channels
            if (message.lower() == 'list'):
                return self.sendList(client, user)

            # Check if this message is a Private Message
            if (len(args) > 1):
                message = message[(len(args[0]) + 1):]
                sent = self.sendPriv(client, user[0], args[0], message)
                if sent > 1:
                    return client.notice(user[0], 'Notice: your message had ' + str(sent) + ' recipient' + ('' if sent == 1 else 's')
                        + ' due to same nicks across linked channels.')
                if sent == 0:
                    client.notice(user[0], 'Error: user \'' + args[0] + '\' not found across Relay network.')
                return

            return client.notice(user[0], 'Send \'list\' to get list of online users. Start a message with a connected nick followed by a message to send a PM.')

    def notice(self, client, user, location, message):
        pass

    def kickUser(self, client, user, args, ban=False):
        for link in self.links:
            if link['client'].profile.network.name.lower() == args[1]:
                for n in range(0, len(link['nicks'])):
                    if args[2] == link['nicks'][n].lower():
                        return link['client'].kick(link['location'], args[2], 'Kicked by ' + user[0] + ' via ' + client.profile.network.name, ban=ban)
                return client.notice(user[0], 'That user was not found on ' + link['client'].profile.network.name)
        return client.notice(user[0], 'Network not found, check LIST (/msg ' + client.profile.nick + ' list) for Network names.')

    def sendList(self, client, user):
        for n in self.links:
            ## TODO:
            # Better check against this. Could be relaying channels on a single network
            if not n['client'] == client:
                c = self.getColor(n['client'], n['location'])
                client.notice(user[0], '\00303' + str(len(n['nicks'])) + ' User'
                    + ('' if len(n['nicks']) == 1 else 's') + ' in \003' + c + n['location'] + '\003 '
                    + '(\003' + c + 'via ' + n['client'].profile.network.name + '\003): \003' + c
                    + (('\003, \003' + c).join(n['nicks'])))

    def join(self, client, user, location):
        if (client.profile.nick == user[0]):
            return client.send('WHO ' + location)
        if (self.isRelayed(client, location)):
            self.addUserToChannel(client, location, user[0])
            self.relay(client, self.constructHeading(client, location, user[0], join_msg_color) + ' has joined ' + location)

    def part(self, client, user, location):
        if (self.isRelayed(client, location)):
            self.remUserFromChannel(client, location, user[0])
            self.relay(client, self.constructHeading(client, location, user[0], part_msg_color) + ' has left ' + location)

    def kick(self, client, user, location, kicked, msg):
        if (self.isRelayed(client, location)):
            color = self.getColor(client, location)
            self.relay(client, self.constructHeading(client, location, user[0], kick_msg_color) + ' has kicked \003' + color + kicked + '\003' +
                kick_msg_color + ' from ' + location)
            self.remUserFromChannel(client, location, kicked)

    def mode(self, client, user, location, modes):
        if (self.isRelayed(client, location)):
            self.relay(client, self.constructHeading(client, location, user[0], nick_msg_color) + ' set mode: ' + location + ' ' + modes)

    def quit(self, client, user):
        for i in range(0, len(self.links)):
            if self.links[i]['client'] == client:
                if user[0] in self.links[i]['nicks']:
                    loc = self.links[i]['location']
                    self.remUserFromChannel(client, loc, user[0])
                    self.relay(client, self.constructHeading(client, loc, user[0], part_msg_color) + ' has quit.')

    def nick(self, client, oldNick, newNick):
        oldNick = oldNick[0]
        for i in range(0, len(self.links)):
            if self.links[i]['client'] == client:
                if oldNick in self.links[i]['nicks']:
                    loc = self.links[i]['location']
                    color = self.getColor(client, loc)
                    self.remUserFromChannel(client, loc, oldNick)
                    self.addUserToChannel(client, loc, newNick)
                    self.relay(client, self.constructHeading(client, loc, oldNick, nick_msg_color) + ' is now known as \003' + color + newNick)

    def namelist(self, client, location, user):
        if (self.isRelayed(client, location)):
            self.addUserToChannel(client, location, user[0])

    def userInChannel(self, client, user):
        for i in range(0, len(self.links)):
            if self.links[i]['client'] == client:
                return user in self.links[i]['nicks']

    def addUserToChannel(self, client, location, user):
        for i in range(0, len(self.links)):
            if self.links[i]['client'] == client and self.links[i]['location'] == location:
                if not user in self.links[i]['nicks']:
                    self.links[i]['nicks'].append(user)

    def remUserFromChannel(self, client, location, user):
        for i in range(0, len(self.links)):
            if self.links[i]['client'] == client and self.links[i]['location'] == location:
                self.links[i]['nicks'].remove(user)

    # Create the message heading for a relay message
    # e.g: [overflow] hey everyone!
    # * overflow gasps
    def constructHeading(self, client, location, nick, action=False):
        n = '\003' + self.getColor(client, location) + nick + '\003'
        return '[' + n + '] ' if not action else '\003' + action + '* ' + n + '\003' + action

    # Each link gets a unique color
    def getColor(self, client, location):
        for i in range(0, len(self.links)):
            if self.links[i]['client'] == client and self.links[i]['location'] == location:
                return color_palette[i]
        return None

    # Return whether or not the client and channel combination is configured for relaying
    def isRelayed(self, client, location):
        for link in self.links:
            if link['client'] == client and link['location'] == location:
                return True
        return False
