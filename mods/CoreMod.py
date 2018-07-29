from lib import Access
from lib import Engine

# Declare our VERSION
VERSION = 'mate py-ircbot v0.2c'

class CoreMod:

    # CoreMod
    #
    # Core Functions always loaded by default within Event engine creation.
    # Key component for Access system

    def __init__(self):
        # All mods need a Module instance, including name and types
        # types can either be a single string or a list of strings
        # lib.Engine.Module(name, types, active=True)
        self.module = Engine.Module('CoreMod', ['PRIVMSG', 'NOTICE', 'PART'])

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
            return client.notice(user[0], 'Access level: ' + str(client.getRights(user[0])) + ' - Current rights: ' + str(client.activeRights(user[0])))

        # Legacy Auth procedure
        if message == '.' and \
            client.getRights(user[0]) > Access.LEVELS['USER'] and \
            client.activeRights(user[0]) == Access.LEVELS['USER']:
            return client.send('WHOIS :' + user[0])

        # Admin Commands
        if client.activeRights(user[0]) >= Access.LEVELS['ADMIN']:
            # Join a channel
            if args[0] == '!join':
                if len(args) == 2 and args[1].startswith('#'):
                    return client.join(args[1])
                return client.notice(user[0], 'Syntax: !join #channel')

            # Leave a channel, or current channel
            if args[0] == '!part':
                if len(args) == 2 and args[1].startswith('#'):
                    return client.part(args[1])
                return client.part(channel)

            # Adjust user access
            # # TODO:
            # Add support to add users to different networks (owner only?)
            if args[0] == '!set':
                if not len(args) == 3:
                    return client.notice(user[0], 'Syntax: !set [nick] [level]')
                try:
                    oLevl = client.getRights(args[1])
                    # Prevent abuse
                    if oLevl >= client.getRights(user[0]):
                        return client.notice(user[0], 'Error - unable to change access.')

                    nLevl = int(args[2])
                    if oLevl == nLevl: # no changed
                        return client.notice(user[0], 'Access unchanged.')
                    if client.engine.access.setRights(client, args[1], nLevl):
                        return client.msg(channel, 'Access changed (' + args[1] + ' ' + ('++' if nLevl - oLevl > 0 else '--') + ' ' + args[2] + ')')
                    return client.notice(user[0], 'Error occured while setting permissions.')
                except:
                    return client.notice(user[0], 'Must be a valid access level.')

    # notice is dealt with similarly to messages, but almost always the target (channel) is the Client
    def notice(self, client, user, target, message):
        if not target.lower() == client.profile.nick.lower():
            return # this module only will deal will NOTICES to the client directly

        # Authenticate the user with the Access system, by checking if they are identified
        if message.lower() == 'auth' and \
            client.getRights(user[0]) > Access.LEVELS['USER'] and \
            client.activeRights(user[0]) == Access.LEVELS['USER']:
            return client.send('WHOIS :' + user[0])

    # This module will attempt to rejoin all AJoin channels whenever left
    def part(self, client, user, location):
        ## TODO:
        # Create a TimedSchedule where misc IRC commands can be performed on a delay
        # Use this new feature to auto reattempt to join a channel every x seconds
        pass
