import lib.Engine
import shelve
import time

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
        # append contents of messages to scrollback
        if channel.startswith('#'):
            self.storemsg(client, user, channel, message)

        args = message.split(' ')

    # Store message in scrollback
    def storemsg(self, client, user, chan, message):
        sb = shelve.open(dir + 'hl-sb.db', writeback=True)
        try:
            # add new message contents to scrollback [channel] -> {user, msg, timestamp}
            sb[chan].append({'u': user, 'm': message, 't': client.engine.log.get_timestamp()})
        except:
            # New channel, create and restart storage
            sb[chan] = []
            sb.close()
            return self.storemsg(client, user, chan, message)

        # check if our scrollback is the max size
        if len(sb[chan]) > scrollback_limit:
            del sb[chan][0]

        sb.close()

    def start(self):
        #load our users
        hilite = shelve.open(dir + 'hl-core.db', writeback=True)
        try:
            # validate database integrity
            print
        except:
            # no database found, create one
            # list of users (netName, usrNick, chkoutDuration[mins], timestampLastSeen)
            hilite['#auto'] = []
            # currently checked out users (netName, usrNick, list of events fully processed)
            hilite['#out'] = []
        finally:
            hilite.close()
        # TODO need to establish certain constant Things
        # auto hilite users (network name, nick, autocheckout duration, lastSeen)
        # currently checked out users, their hilite events stored with their nick

        #clear the scrollback
        scrollback = shelve.open(dir + 'hl-sb.db', writeback=True)
        scrollback.clear()
        scrollback.close()
