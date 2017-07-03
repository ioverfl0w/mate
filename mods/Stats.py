import lib.Engine

class Stats:

    def __init__(self):
        self.module = lib.Engine.Module('Stats', ['PRIVMSG', 'JOIN', 'PART'])

    def message(self, client, user, channel, message):
        args = message.split(' ')

        if args[0].lower() == '!me':
            return client.msg(channel, 'not ready yet')
