import lib.Timer
import time

class Pinger:

    # Pinger
    #
    # We don't trust the server, so we're going to ping ourselves :-)

    def __init__(self):
        # every timed-function needs to have a Schedule
        # lib.Timer.Schedule(name, delay (in seconds))
        self.schedule = lib.Timer.Schedule('Pinger', 3 * 60) # 3 mins
        # Pinger attempts allowed
        self.pingsAllowed = 3

    # Timed-Functions are called from the Engine, so you have to determine
    # either to broadcast to all Clients or create a method to remember
    # which client you want. For Pinger, we'll check all Clients
    def execute(self, engine):
        for client in engine.clients:
            if client.pingAttempts >= self.pingsAllowed:
                engine.log.write('Pinger.py | Client being terminated due to no PONG replies!')
                engine.dead(client)
                continue
            client.send('PING ' + str(time.time()))
            client.pingAttempts += 1
