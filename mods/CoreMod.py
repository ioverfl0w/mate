class Module:

    def __init__(self):
        # What IRC triggers will be used for this module
        self.types = ['PRIVMSG', 'NOTICE']
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

        if args[0].lower() == '!test':
            client.msg(channel, 'test completed')
        pass
