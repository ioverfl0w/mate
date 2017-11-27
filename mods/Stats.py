from lib import Engine
import sqlite3
import time
from decimal import Decimal

dir = './data/'
TABLE = 'MateStats'

class Stats:

    # Stats
    #
    # Record numerical stats for users. Module is stand-alone, meaning you can
    # disable this module and nothing else will break.

    def __init__(self):
        self.module = Engine.Module('Stats', ['PRIVMSG', 'JOIN', 'PART'])

        # Connect to our database
        self.db = sqlite3.connect(dir + 'stats.db')
        # Create database if does not exist
        self.db.execute('''
        create table if not exists ''' + TABLE + ''' (
            network text,
            nick text UNIQUE,
            joins integer default 0,
            parts integer default 0,
            msgs integer default 0,
            chars integer default 0,
            seen integer default 0
        );''')

    # Get the user stats for the nick in use on the Client's network
    def getStats(self, client, user):
        # case insensitive
        user = user.lower()
        cur = self.db.cursor()
        cur.execute('SELECT * FROM ' + TABLE + ' WHERE network=? AND nick=?', [client.profile.network.name, user])
        return cur.fetchone()

    # Record user stats in client's server database for username
    # Key should be the value to be altered by +1
    def recordStats(self, client, user, key):
        # case insensitive
        user = user.lower()
        cur = self.db.cursor()
        cur.execute('UPDATE ' + TABLE + ' SET ' + key + '=' + key + '+1, seen=? ' + \
            'WHERE network=? AND nick=?', [time.time(), client.profile.network.name, user])
        cur.execute('INSERT OR IGNORE INTO ' + TABLE + ' (network, nick, ' + key + ', seen) ' + \
            'VALUES (?,?,?,?)', [client.profile.network.name, user, 1, time.time()])
        self.db.commit()
        cur.close()

    # Similar to recordStats(..) but we are changing two values
    def recordMsgStats(self, client, user, size):
        user = user.lower()
        cur = self.db.cursor()
        cur.execute('UPDATE ' + TABLE + ' SET msgs=msgs+1, chars=chars+?, seen=? ' + \
             'WHERE network=? AND nick=?', [size, time.time(), client.profile.network.name, user])
        cur.execute('INSERT OR IGNORE INTO ' + TABLE + ' (network, nick, msgs, chars, seen) ' + \
            'VALUES (?,?,?,?,?)', [client.profile.network.name, user, 1, size, time.time()])
        self.db.commit()
        cur.close()

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
                return client.msg(channel, '\0032(Stats) \003' + user[1] + ' - ' + \
                    '\0033Joins:\003 ' + str(usr[2]) + ' \0033Parts:\003 ' + \
                    str(usr[3]) + ' \0033Messages:\003 ' + str(usr[4]) + \
                    ' \0033Characters:\003 ' + str(usr[5]) + ' \0033Avg CPM:\003 ' + \
                    str(round(Decimal(usr[5]) / Decimal(usr[4]), 2)) )
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
            usr = self.getStats(client, args[1])
            if usr == None: #no user to report
                return client.msg(channel, user[0] + ', I don\'t know who ' + args[1] + ' is.')
            else:
                return client.msg(channel, user[0] + ', ' + args[1] + ' was last seen ' + Engine.timedString((time.time() - usr[6])) + ' ago.')

    def join(self, client, user, location):
        # Record this user a join
        self.recordStats(client, user[0], 'joins')

    def part(self, client, user):
        # Record this user a part
        self.recordStats(client, user[0], 'parts')
