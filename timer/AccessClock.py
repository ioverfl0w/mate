import lib.Timer
import time

# Timeout duration (in minutes)
timeout = 30

class AccessClock:

    # AccessClock
    #
    # Access expiration. Clock is disabled until a user has authenticated

    def __init__(self):
        self.schedule = lib.Timer.Schedule('AccessClock', 1, active=False)  # disable this module until needed
        # Authenticated users
        self.auth = []

    # Insert newly authenticated user into system for duration of time specified above
    def authenticate(self, client, nick):
        # We reference users in a 'nick@network' format for access
        user = nick + '@' + client.profile.network.name

        # Check for duplicate users
        for a in self.auth:
            if a['user'].lower() == user.lower():
                return client.engine.log.write('[AC] Duplicate auth entry attempted.')

        self.auth.append({'user': user, 'exp': (time.time() + (timeout * 60))})
        # make sure the Clock is active with a set time
        # client.notice(nick, 'You have been authenticated.')
        client.engine.log.write('[AC] Added user ' + user + ' to AC.')
        if not self.schedule.active:
            self.schedule.delay = timeout * 60
            self.schedule.active = True
            client.engine.log.write('[AC] Clock enabled.')

    # Returns the amount of time remaining if the user is authenticated, otherwise
    # will return 0
    def isAuthed(self, client, nick):
        nick = (nick + '@' + client.profile.network.name).lower()
        for a in self.auth:
            if a['user'].lower() == nick:
                return a['exp'] - time.time()
        return 0

    def getAuthList(self):
        res = []
        for u in self.auth:
            res.append([u['user'], u['exp'] - time.time()])
        return res

    def execute(self, engine):
        rem = []
        count = 0
        newTime = timeout * 60

        # Cycle through all users checking for expired sessions.
        for usr in self.auth:
            # Check for expired sessions
            if usr['exp'] <= time.time():
                rem.append(count)
            # Change our expiration time to earliest time
            newTime = newTime if usr['exp'] - time.time() > newTime else usr['exp'] - time.time()
            count += 1

        # Delete expired sessions
        count = 0
        for i in rem:
            engine.log.write('[AC] User ' + self.auth[i]['user'] + ' auth expired.')
            del self.auth[i - count]
            count += 1

        # If we have no more authenticated users, disable this module again
        if len(self.auth) == 0:
            self.schedule.active = False
            engine.log.write('[AC] Clock disabled.')
        else:
            self.schedule.delay = newTime
