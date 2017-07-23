import shelve

# Scrollback limit for hilight events
scrollback_limit = 5
dir = './data/'

class Hilight:

    # Hilight
    #
    # Maintains short message buffer for each channel, and pushes
    # Hilight events to them when they are next active.

    def __init__(self):
        self.module = lib.Engine.Module('Hilight', 'PRIVMSG')
        
        # Start a new scrollback database
        self.start()

    def message(self, client, user, channel, message):
        pass

    def store_message(self, client, user, chan, message):
        pass

    def start(self):
        #load our users
        hilite = shelve.open(dir + 'hilite.db', writeback=True)
        try:

        except:
            pass
        finally:
            hilite.close()
        # TODO need to establish certain constant Things
        # auto hilite users (network name, nick, autocheckout duration, lastSeen)
        # currently checked out users, their hilite events stored with their nick

        #clear the scrollback
        scrollback = shelve.open(dir + 'scrollback.db', writeback=True)
        scrollback.clear()
        scrollback.close()
