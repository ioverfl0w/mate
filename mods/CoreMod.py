# Declare our VERSION
VERSION = 'python-ircbot v0.1b'

class Module:

    # This mod is primarily an example module, as well as some typical
    # bot compliance features. Things such as '.source' and VERSION
    # requests will be handled here.

    def __init__(self):
        # What IRC triggers will be used for this module. Always put in []
        self.types = ['PRIVMSG']
        # An A E S T H E T I C module name, used for displays
        self.name = 'CoreModule'
        # Whether module is Actively loaded or dormant (able to be loaded)
        self.active = True

    # message - process a PRIVMSG irc message
    # client - the client who received the packet
    # user - array of user values (0-nick,1-user,2-host) - if this is a PM,
    #       this will be set to client's details
    # channel - channel message is from (if PM, this will be the sender)
    # message - the content message
    def message(self, client, user, channel, message):
        args = message.split(" ")

        # version request
        if args[0] == '\001VERSION\001':
            return client.notice(user[0], '\001VERSION ' + VERSION + '\001')

        # source request
        if args[0].lower() == '.source' or args[0].lower() == '.bots':
            return client.msg(channel, 'mate [python] :: Source https://github.com/ioverfl0w/mate/')
