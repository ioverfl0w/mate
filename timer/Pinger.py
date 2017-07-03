import lib.Timer
import time

class Pinger:

    # Pinger
    #
    # We don't trust the server, so we're going to ping ourselves :-)

    def __init__(self):
        # every timed-function needs to have a Schedule
        # lib.Timer.Schedule(name, delay (in seconds))
        self.schedule = lib.Timer.Schedule('Pinger', 3 * 60) #

    # Timed-Functions are called from the Engine, so you have to determine
    # either to broadcast to all Clients or create a method to remember
    # which client you want. For Pinger, we'll check all Clients
    def execute(self, engine):
        for client in engine.clients:
            client.send('PING ' + str(time.time()))
