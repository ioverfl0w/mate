import lib.Engine
import shelve
import time
from decimal import Decimal

# new user format: joins, parts, messages, characters, time last seen
new_user = {'j': 0, 'p': 0, 'm': 0, 'c': 0, 's': 0}
dir = './data/'

class Stats:

    # Stats
    #
    # Record numerical stats for users. Module is stand-alone, meaning you can
    # disable this module and nothing else will break.

    def __init__(self):
        self.module = lib.Engine.Module('Stats', ['PRIVMSG', 'JOIN', 'PART'])

    # Get the user stats for the nick in use on the Client's network
    def getStats(self, client, user, createNew=True):
        # case insensitive
        user = user.lower()
        # open the specific Network's database
        db = shelve.open(dir + client.profile.network.name.lower() + '.db', writeback=True)
        try:
            res = db[user]
        except:
            if createNew:
                #new user we want to create
                db[user] = new_user
                db[user]['s'] = time.time()
                res = db[user]
            else:
                #we're just checking, but dont want to create a user
                return None
        finally:
            db.close()
        return res

    # Record user stats in client's server database for username
    # Key should be the value to be altered by +1
    def recordStats(self, client, user, key):
        # case insensitive
        user = user.lower()
        # open the Network database
        db = shelve.open(dir + client.profile.network.name.lower() + '.db', writeback=True)
        try:
            db[user][key] += 1
            db[user]['s'] = time.time()
        except:
            db[user] = new_user
            client.engine.log.write('Error while writing ' + key + ' stats, assuming new user (' + user + ')')
        finally:
            db.close()

    # Similar to recordStats(..) but we are changing two values
    def recordMsgStats(self, client, user, size):
        user = user.lower()
        db = shelve.open(dir + client.profile.network.name.lower() + '.db', writeback=True)
        try:
            db[user]['m'] += 1
            db[user]['c'] += size
            db[user]['s'] = time.time()
        except:
            db[user] = new_user
            client.engine.log.write('Error while writing message stats, assuming new user (' + user + ')')
        finally:
            db.close()

    def message(self, client, user, channel, message):
        args = message.split(' ')

        # We can quickly determine if this module is either recording stats, or
        # needs to perform a command (commands do not count towards stats)
        if not args[0].startswith('!') and not args[0].startswith('.'):
            return self.recordMsgStats(client, user[0], len(message))

        # show off your stats to the channel
        if args[0].lower() == '!me':
            usr = self.getStats(client, user[0])
            try:
                return client.msg(channel, '\0032(Stats) \003' + user[0] + ' - ' + \
                    '\0033Joins:\003 ' + str(usr['j']) + ' \0033Parts:\003 ' + \
                    str(usr['p']) + ' \0033Messages:\003 ' + str(usr['m']) + \
                    ' \0033Characters:\003 ' + str(usr['c']) + ' \0033Avg CPM:\003 ' + \
                    str(round(Decimal(usr['c']) / Decimal(usr['m']), 2)) )
            except:
                # Users not registered (no stats recorded) will cause an error
                return client.msg(channel, '\0034Error\003 unable to recall stats for ' + user[0])

        # check the last time a specified user was seen doing something
        if args[0].lower() == '!seen':
            # nicks are only 1 word, so here's a reminded of syntax
            if not len(args) == 2:
                return client.notice(user[0], 'Syntax: !seen [nick]')
            if args[1].lower() == user[0].lower():
                return client.msg(channel, 'Looking for yourself, ' + user[0] + '?')
            usr = self.getStats(client, args[1], createNew=False)
            if usr == None: #no user to report
                return client.msg(channel, user[0] + ', I don\'t know who ' + args[1] + ' is.')
            else:
                return client.msg(channel, user[0] + ', ' + args[1] + ' was last seen ' + lib.Engine.timedString((time.time() - usr['s'])) + ' ago.')

    def join(self, client, user, location):
        # Record this user a join
        self.recordStats(client, user[0], 'j')

    def part(self, client, user):
        # Record this user a part
        self.recordStats(client, user[0], 'p')
