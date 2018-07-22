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

    def __init__(self, clients):
        # TODO
        # handle: MODE, PMs, Admin Commands, Disconnected messages with cooldown
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

    def message(self, client, user, channel, message):
        # Handle private messages
        # # TODO:
        # Allow for PMing accross network without having to Specify
        # the target with each message
        if (channel == user[0]):
            if (message.lower() == 'list'):
                for n in self.links:
                    ## TODO:
                    # Better check against this. Could be relaying channels on a single network
                    if not n['client'] == client:
                        client.notice(user[0], '\003' + self.getColor(n['client'], n['location']) +
                            'Current users in ' + n['location'] + '@' + n['client'].profile.network.name + ': ' + (', '.join(n['nicks'])))

        if (self.isRelayed(client, channel)):
            self.relay(client, self.constructHeading(client, channel, user[0]) + message)

    def notice(self, client, user, location, message):
        pass

    def join(self, client, user, location):
        if (client.profile.nick == user[0]):
            return client.send('WHO ' + location)
        if (self.isRelayed(client, location)):
            self.addUserToChannel(client, location, user[0])
            self.relay(client, self.constructHeading(client, location, user[0], join_msg_color) + ' has joined ' + location)

    def part(self, client, user, location):
        if (self.isRelayed(client, location)):
            print('trigger part ' + location)
            self.remUserFromChannel(client, location, user[0])
            self.relay(client, self.constructHeading(client, location, user[0], part_msg_color) + ' has left ' + location)

    def kick(self, client, user, location, kicked, msg):
        if (self.isRelayed(client, location)):
            color = self.getColor(client, location)
            self.relay(client, self.constructHeading(client, location, user[0], kick_msg_color) + ' has kicked \003' + color + kicked + '\003' +
                kick_msg_color + ' from ' + location)
            self.remUserFromChannel(client, location, kicked)

    def quit(self, client, user):
        print(user)
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
