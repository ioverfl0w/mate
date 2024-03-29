import sqlite3

# Default access scale
LEVELS = {'OWNER': 3, 'ADMIN': 2, 'TRUSTED': 1, 'USER': 0, 'BLOCKED': -1, 'UNREG': -2}
TABLE = 'MateAccess'

class Access:

    # Access
    #
    # Levels system per Network
    # 3 - Owner
    # 2 - Admin
    # 1 - Trusted/Mod
    # 0 - Normal user
    # -1 - Ignored/Blocked

    def __init__(self, engine):
        # AccessClock instance
        self.clock = engine.timer.fetchTimeFunc('AccessClock')
        # Sqlite3 database
        self.db = sqlite3.connect('./data/access.db')
        # Create database if not established
        self.db.execute('''
        create table if not exists ''' + TABLE + ''' (
            network text,
            nick text,
            level integer
        );''')

        if engine.debug:
            for e in self.getAccessList(None):
                engine.log.write('(Access List) ' + str(e))

    def getLevel(self, level):
        return LEVELS[level.upper()]

    # Authenticate a user within the system
    def auth(self, client, nick):
        self.clock.authenticate(client, nick)

    # Check it authenticated, and return their granted permission level
    def getCurrentRights(self, client, nick):
        return self.userRights(client, nick) if self.clock.isAuthed(client, nick) > 0 else 0

    # Return the Level of rights for the specified user on the receiving Client
    def userRights(self, client, nick):
        nick = nick.lower()
        cur = self.db.cursor()

        cur.execute('SELECT level FROM ' + TABLE + ' WHERE network=? AND nick=?', [client.profile.network.name, nick])
        try:
            rights = cur.fetchone()[0]
        except:
            rights = None
        cur.close()
        return rights if rights is not None else -2

    # Declare a level of rights for a specific user on a certain network
    def setRights(self, client, nick, level):
        if self.userRights(client, nick) == -2:  # this user does not exist
            return self.createNewUser(client, nick, level)
        nick = nick.lower()
        self.db.execute('UPDATE ' + TABLE + ' SET level=? WHERE network=? AND nick=?', [level, client.profile.network.name, nick])
        self.db.commit()
        return True

    def createNewUser(self, client, nick, level):
        self.db.execute('INSERT INTO ' + TABLE + ' values (?, ?, ?) ', [client.profile.network.name, nick.lower(), level])
        self.db.commit()
        return True

    def getAccessList(self, client=None):
        cur = self.db.cursor()
        if client is None:
            cur.execute('SELECT * FROM ' + TABLE)
        else:
            cur.execute('SELECT * FROM ' + TABLE + ' WHERE network=?', [client.profile.network.name])

        res = cur.fetchall()
        cur.close()
        return res