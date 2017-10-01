import sqlite3

# Default access scale
LEVELS = {'OWNER': 3, 'ADMIN': 2, 'TRUSTED': 1, 'USER': 0, 'BLOCKED': -1}

class Access:

    # Access
    #
    # Levels system per Network
    # 3 - Owner
    # 2 - Admin
    # 1 - Trusted/Module
    # 0 - Normal user
    # -1 - Ignored/Blocked

    def __init__(self, engine):
        # AccessClock instance
        self.clock = engine.timer.fetchTimeFunc('AccessClock')
        # Sqlite3 database
        self.database = sqlite3.connect('./data/access.db')

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
        db = shelve.open(dir + client.profile.network.name.lower() + '-access.db')
        try:
            rights = db[nick]
        except:
            rights = 0 # no rights
        db.close()
        return rights

    # Declare a level of rights for a specific user on a certain network
    def setRights(self, client, nick, level):
        nick = nick.lower()
        db = shelve.open(dir + client.profile.network.name.lower() + '-access.db', writeback=True)
        try:
            db[nick] = level
        except:
            return False
        db.close()
        return True
