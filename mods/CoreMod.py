import lib.Engine

# Declare our VERSION
VERSION = 'python-ircbot v0.2b'

class CoreMod:

    # This mod is primarily an example module, as well as some typical
    # bot compliance features. Things such as '.source' and VERSION
    # requests will be handled here.
    def __init__(self):
        # All mods need a Module instance, including name and types
        # types can either be a single string or a list of strings
        # lib.Engine.Module(name, types, active=True)
        self.module = lib.Engine.Module('CoreMod', ['PRIVMSG', 'NOTICE', 'NICK'])

    # message - process a PRIVMSG irc message
    # client - the client who received the packet
    # user - array of user values (0-nick,1-user,2-host) - if this is a PM,
    #       this will be set to client's details
    # channel - channel message is from (if PM, this will be the sender)
    # message - the content message
    def message(self, client, user, channel, message):
        args = message.split(' ')

        # version request:
        if args[0] == '\001VERSION\001':
            return client.notice(user[0], '\001VERSION ' + VERSION + '\001')

        # source request
        if args[0].lower() == '.source' or args[0].lower() == '.bots':
            return client.msg(channel, 'mate [python] :: Source https://github.com/ioverfl0w/mate/')

        if args[0].lower() == '!set' and client.engine.access.userRights(client, user[0]) >= client.engine.access.getLevel('admin'):
            if not len(args) == 3:
                return client.notice(user[0], 'Syntax: !set [nick] [level]')

            try:
                oLevl = client.engine.access.userRights(client, args[1])
                nLevl = int(args[2])
                if oLevl == nLevl: # no changed
                    return client.notice(user[0], 'Access unchanged.')
                if client.engine.access.setRights(client, args[1], nLevl):
                    return client.msg(channel, 'Access changed (' + args[1] + ' ' + ('++' if nLevl - oLevl > 0 else '--') + ' ' + args[2] + ')')
                return client.notice(user[0], 'Error occured while setting permissions.')
            except:
                return client.notice(user[0], 'Must be a valid access level.')

        if args[0].lower() == '!rights': # and client.engine.access.userRights(client, user[0]) > 0:
            return client.notice(user[0], 'Access level: ' + str(client.engine.access.userRights(client, user[0])))

    # notice is dealt with similarly to messages, but almost always the target (channel) is the Client
    def notice(self, client, user, target, message):
        if not target.lower() == client.profile.nick.lower():
            return # this module only will deal will NOTICES to the client directly

        # Authenticate the user with the Access system, by checking if they are identified
        if message.lower() == 'auth':
            return client.send('WHOIS :' + user[0])
