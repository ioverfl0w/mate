import lib.Engine

# Declare our VERSION
VERSION = 'python-ircbot v0.1b'

class CoreMod:

    # This mod is primarily an example module, as well as some typical
    # bot compliance features. Things such as '.source' and VERSION
    # requests will be handled here.

    def __init__(self):
        # All mods need a Module instance, including name and types
        # types can either be a single string or a list of strings
        # lib.Engine.Module(name, types, active=True)
        self.module = lib.Engine.Module('CoreMod', 'PRIVMSG')

    # message - process a PRIVMSG irc message
    # client - the client who received the packet
    # user - array of user values (0-nick,1-user,2-host) - if this is a PM,
    #       this will be set to client's details
    # channel - channel message is from (if PM, this will be the sender)
    # message - the content message
    def message(self, client, user, channel, message):
        args = message.split(' ')

        # version request
        if args[0] == '\001VERSION\001':
            return client.notice(user[0], '\001VERSION ' + VERSION + '\001')

        # source request
        if args[0].lower() == '.source' or args[0].lower() == '.bots':
            return client.msg(channel, 'mate [python] :: Source https://github.com/ioverfl0w/mate/')
