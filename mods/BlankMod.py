from lib import Engine

class BlankMod:

    # BlankMod
    #
    # This module is purely for reference, so you know what
    # functions and arguments are required to integrate with
    # the Event engine.
    # All Modules need to be imported in run.py and an instance
    # created and loaded with engine.event.loadMod(module)

    def __init__(self):
        # module is used to provide a readable module name and either
        # a single event type, or a list of event types. Both lines work, when
        # one is commented out. Event types are raw IRC event types
        #self.module = lib.Engine.Module('ModuleName', 'PRIVMSG')
        self.module = Engine.Module('ModuleName', ['PRIVMSG', 'JOIN', 'PART'])

    # client - the client that is processing the event
    # user - [0] nick , [1] user , [3] host
    # channel - either a channel or the client's nick
    # message - the content of the message
    def message(self, client, user, channel, message):
        pass

    # client - the client that is processing the event
    # user - [0] nick , [1] user , [3] host
    # location - usually notices are sent directly to users, so this should be the client's nick
    # message - the content of the message
    def notice(self, client, location, message):
        pass

    # client - the client that is processing the event
    # user - [0] nick , [1] user , [3] host
    # location - the location the user has joined
    def join(self, client, user, location):
        pass

    # client - the client that is processing the event
    # user - [0] nick , [1] user , [3] host
    # location - the location the user has left
    def part(self, client, user, location):
        pass
