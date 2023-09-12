import timer.AccessClock
import timer.Pinger
import time
class TimeKeeper:

    # TimeKeeper
    #
    # Manage all time-related functions and ensure they are called upon
    def __init__(self, engine):
        # storage for timed functions
        self.collection = []
        # the engine we are associated with
        self.engine = engine

        # We can assure some Timed-Functions are automatically loaded
        self.loadTimeFunc(timer.Pinger.Pinger())
        self.loadTimeFunc(timer.AccessClock.AccessClock())

    # Go through and check our functions if they are ready yet
    def cycle(self):
        for func in self.collection:
            if func.schedule.active and func.schedule.check():
                func.execute(self.engine)
                func.schedule.reset()

    # Load our timed-function into the TimeKeeper
    def loadTimeFunc(self, func):
        if self.engine.debug:
            self.engine.log.write('(Timer) Loading timed-function ' + func.schedule.name + ' (' + ('active' if func.schedule.active else 'dormant') + ')')
        self.collection.append(func)

    # Fetch a timed-function based off its name
    def fetchTimeFunc(self, name):
        for func in self.collection:
            if func.schedule.name == name:
                return func
        return None

    def getTimerNames(self):
        res = []
        for c in self.collection:
            res.append(c.schedule.name + '(' + ('active' if c.schedule.active else 'dormant') + ')')
        return ', '.join(res)

class Schedule:

    # Schedule
    #
    # Tool object used with timed-function modules to maintain proper
    # structure for TimeKeeper

    def __init__(self, name, delay, active=True):
        # our A E S T H E T I C name
        self.name = name
        # our delay (in seconds)
        self.delay = delay
        # Time since last called
        self.start = time.time()
        # Toggle to disable the timed-function
        self.active = active

    # check if time is up
    def check(self):
        return self.start + self.delay <= time.time()

    # clear start time
    def reset(self):
        self.start = time.time()
