from lib import Access
from lib import Engine

# Declare our VERSION
VERSION = 'mate python-ircbot'


class CoreMod:

    # CoreMod
    #
    # Core Functions always loaded by default within Event engine creation.
    # Key component for Access system

    def __init__(self):
        # All mods need a Module instance, including name and types
        # can either be a single string or a list of strings
        # lib.Engine.Module(name, types, active=True)
        self.module = Engine.Module('CoreMod', ['PRIVMSG', 'NOTICE', 'PART', 'IDENTIFY'])
        self.authReq = []  # track pending auth requests

    # message - process a PRIVMSG irc message
    # client - the client who received the packet
    # user - array of user values (0-nick,1-user,2-host) - if this is a PM,
    #       this will be set to client's details
    # channel - channel message is from (if PM, this will be the sender)
    # message - the content message
    def message(self, client, user, channel, message):
        args = message.lower().split(' ')

        # version request:
        if message == '\001VERSION\001':
            return client.notice(user[0], '\001VERSION ' + VERSION + '\001')

        # source request
        if args[0] == '.source' or args[0] == '.bots':
            return client.msg(channel, 'mate [python] :: Source https://github.com/ioverfl0w/mate/')

        # Share their permission status
        if args[0] == '!rights':
            return client.notice(user[0],
                                 'Access level: ' + str(client.getRights(user[0])) + ' - Current rights: ' + str(
                                     client.activeRights(user[0])))

        # Legacy Auth procedure
        if message == '.' and \
                client.getRights(user[0]) > Access.LEVELS['USER'] and \
                client.activeRights(user[0]) == Access.LEVELS['USER']:
            self.authReq.append(user[0])
            return client.send('WHOIS :' + user[0])

        # Admin Commands beyond this point
        if client.activeRights(user[0]) < Access.LEVELS['ADMIN']:
            return

        if args[0] == '!help':
            client.notice(user[0], '[CoreMod]: .source/.bots !rights !botstats !access !say !join !part !set !cmods !ctimers !lmod !umod !rmods !reboot')

        # Give info about Clients, Modules and Timers
        if args[0] == "!botstats":
            return client.msg(channel, "BotsConnected: " + str(len(client.engine.clients)) + " - " +
                              "Mods Loaded: " + str(len(client.engine.event.modules)) + " - " +
                              "Timers Loaded: " + str(len(client.engine.timer.collection)))

        if args[0] == '!access':
            accessList = client.engine.access.getAccessList(client)
            client.notice(user[0], 'Access List for ' + client.profile.nick + ' connected to ' + client.profile.network.name)
            client.notice(user[0], space('Nick') + space('Network') + space('Level') + space('Authed'))
            for a in accessList:
                client.notice(user[0], space(a[1]) + space(a[0]) + space(str(a[2])) + space(str(client.engine.access.clock.isAuthed(client, a[1]) > 0)))

        # Lets send something on behalf of the client
        if args[0] == '!say':
                if len(args) > 1:
                    return client.msg(channel, message[message.index(args[1]):])
                return client.notice(user[0], 'Syntax: !say anything')

        # Join a channel
        if args[0] == '!join':
                if len(args) == 2 and args[1].startswith('#'):
                    client.join(args[1])
                    return client.notice(user[0], 'I have joined ' + args[1])
                return client.notice(user[0], 'Syntax: !join #channel')

        # Leave a channel, or current channel
        if args[0] == '!part':
                if len(args) == 2 and args[1].startswith('#'):
                    client.part(args[1])
                    return client.notice(user[0], 'I have left ' + args[1])
                return client.part(channel)

        # Print all the modules, active and inactive
        if args[0] == '!cmods':
                mods = client.engine.event.get_list()
                return client.msg(channel, 'Active Mods: ' + (', '.join(mods[0]) if len(mods[0]) > 0 else 'None') +
                                  ' -- Inactive mods: ' + (', '.join(mods[1]) if len(mods[1]) > 0 else 'None'))

        # Print all of our Timers
        if args[0] == '!ctimers':
                return client.msg(channel, 'Loaded Timers: ' + client.engine.timer.getTimerNames())

        # Disable a module
        if args[0] == '!umod' and len(args) > 1:
                if client.engine.event.unload(args[1]):
                    return client.msg(channel, 'Unloaded module ' + args[1])
                else:
                    return client.msg(channel, 'Unable to remove module ' + args[1])

        # Reload a module
        if args[0] == '!lmod' and len(args) > 1:
                if client.engine.event.reload(args[1]):
                    return client.msg(channel, 'Reloaded module ' + args[1])
                else:
                    return client.msg(channel, 'Unable to reload module ' + args[1])

        # Reload all modules
        if args[0] == '!rmod':
                client.engine.event.reload_mods()
                return client.msg(channel, 'Mods reloaded')

        # Restart this client
        if args[0] == '!reboot':
                if len(args) > 1 and args[1] == 'confirm':
                    client.msg(channel, 'Going down now!')
                    client.engine.log.write('Confirmed shutdown by ' + user[0] + ' on ' + client.profile.network.name)
                    return client.quit('*tips fedora*')
                else:
                    return client.notice(user[0], 'To confirm reboot, use ' + args[0] + ' confirm')

        # Adjust user access
        # # TODO Add support to add users to different networks (owner only?)
        if args[0] == '!set':
            if not len(args) == 3:
                return client.notice(user[0], 'Syntax: !set [nick] [level]')
            try:
                oLevl = client.getRights(args[1])
                # Prevent abuse
                if oLevl >= client.getRights(user[0]):
                    return client.notice(user[0], 'Error - unable to change access.')

                nLevl = int(args[2])
            except:
                return client.notice(user[0], 'Must be a valid access level.')
            if oLevl == nLevl:  # no changed
                return client.notice(user[0], 'Access unchanged.')
            if client.engine.access.setRights(client, args[1], nLevl):
                return client.msg(channel, 'Access changed (' + args[1] + ' ' + (
                    '++' if nLevl - oLevl > 0 else '--') + ' ' + args[2] + ')')
            return client.notice(user[0], 'Error occurred while setting permissions.')

    # notice is dealt with similarly to messages, but almost always the target (channel) is the Client
    def notice(self, client, user, target, message):
        if not target.lower() == client.profile.nick.lower():
            return  # this module only will deal will NOTICES to the client directly

        # Authenticate the user with the Access system, by checking if they are identified
        if message.lower() == 'auth' and \
                client.getRights(user[0]) >= Access.LEVELS['USER'] and \
                client.activeRights(user[0]) == Access.LEVELS['USER']:
            self.authReq.append(user[0])
            return client.whois(user[0])

    def identify(self, client, nick):
        if nick in self.authReq:
            client.engine.access.auth(client, nick)  # check for authentication
            client.notice(nick, 'You have been authenticated.')
            i = 0

            # prune name from authReq
            for x in self.authReq:
                if x == nick:
                    del self.authReq[i]
                    return
                i += 1

    # This module will attempt to rejoin all AJoin channels whenever left
    def part(self, client, user, channel):
        ## TODO:
        # Create a TimedSchedule where misc IRC commands can be performed on a delay
        # Use this new feature to auto reattempt to join a channel every x seconds
        pass

def space(string, total_len=12):
    if len(string) > total_len:
        return string

    return string + (" " * (total_len - len(string)))