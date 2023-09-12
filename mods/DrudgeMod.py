import random
from lib import Access
from lib import Engine


class DrudgeMod:

    def __init__(self, timer):
        self.module = Engine.Module('DrudgeMod', ['PRIVMSG'])
        self.drudge = timer
        self.engine = self.drudge.engine

    def message(self, client, user, channel, message):
        args = message.lower().split(' ')
        # if not self.drudge.is_subscribed_channel(client, channel) and client.get_access().get_user_rights(user) < 1:
        # 	 return

        if args[0] == '!help':
            client.msg(channel, user[0] + ': [Drudge Report] !size - !top - !last - !random')

        if args[0] == '!size':
            client.msg(channel, 'Headlines cached: ' + str(len(self.drudge.get_headlines())))
            return

        if args[0] == '!top':
            headline = self.drudge.get_headlines()[0]
            client.msg(channel, '' + headline[0] + ' (2' + headline[1] + ')')
            return

        if args[0] == '!last':
            headline = self.drudge.get_headlines()
            headline = headline[len(headline) - 1]
            client.msg(channel, '' + headline[0] + ' (2' + headline[1] + ')')
            return

        if args[0] == '!random' or args[0] == '!rd':
            headline = self.drudge.get_headlines()
            headline = headline[random.randint(0, len(headline) - 1)]
            client.msg(channel, '' + headline[0] + ' (2' + headline[1] + ')')
            return

        if client.activeRights(user[0]) >= Access.LEVELS['ADMIN']:
            if args[0].lower() == '!clear':
                self.drudge.clear()
                client.msg(channel, 'Reports cleared. New cache: ' + str(len(self.drudge.get_headlines()[0])))

            if args[0].lower() == '!del':
                if len(args) == 1:
                    client.notice(user[0], 'Syntax: !del #channel')
                else:
                    if self.drudge.is_subscribed_channel(client, args[1]):
                        self.drudge.rem_subscription(client, args[1])
                        client.part(args[1])
                        client.msg(channel, 'Operations ceased for ' + args[1])
                        self.engine.log.write(
                            'Ops ceased in ' + args[1] + ' by ' + user[0] + '!' + user[1] + '@' + user[
                                2] + ' (client:' + str(client) + ')')
                    else:
                        client.notice(user[0], 'Not operating in that channel')
                return

            if args[0].lower() == '!sub':
                if len(args) == 1:
                    client.notice(user[0], 'Syntax: !sub #channel')
                else:
                    if not self.drudge.is_subscribed_channel(client, args[1]):
                        client.join(args[1])
                        self.drudge.add_subscription(client, args[1])
                        client.msg(args[1],
                                   'I have been requested to update this channel with Drudge Report updates. If this is wrongly done, please join #drudge and request the client be removed.')
                        client.msg(channel, 'Channel ' + args[1] + ' has been added.')
                        self.engine.log.write(
                            'Ops permitted in ' + args[1] + ' by ' + user[0] + '!' + user[1] + '@' + user[
                                2] + ' (client:' + str(client) + ')')
                    else:
                        client.notice(user[0], 'Already operating in that channel')
                return
