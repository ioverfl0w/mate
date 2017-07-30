import lib.Access
import lib.Client
import lib.Event
import lib.Logger
import time
from lib.Timer import TimeKeeper

class Engine:

    # Engine
    #
    # This will ensure all clients are processed and managed. will
    # attempt to reconnect disconnected bots (TODO add 'halted' option)

    def __init__(self, DEBUG=0):
        # our clients
        self.clients = []
        # start a log
        self.log = lib.Logger.Logger()
        # start an Event engine
        self.event = lib.Event.Event(self)
        # start a Time Keeper
        self.timer = lib.Timer.TimeKeeper(self)
        # start an Access system
        self.access = lib.Access.Access()
        # Debug MODE
        self.debug = False if DEBUG == 0 else True

    def addClient(self, profile):
        #add a new client to our queue
        self.clients.append(lib.Client.Client(self, profile))

    def dead(self, client):
        # a client has reported a dead connection,
        # we need to fix this be reconnecting
        self.log.write('! client reported dead !')
        client.status = lib.Client.Status.OFFLINE
        pass

    def cycle(self):
        for e in self.clients:
            # A client that is offline
            if e.status == lib.Client.Status.OFFLINE:
                if self.debug:
                    self.log.write('Connecting ' + str(e))
                e.connect()
                continue

            # we are expecting something
            incoming = str(e.read())
            if incoming == '':
                continue # screw off, blank lines

            # split different messages read at a single time
            queue = incoming.split('\n')
            for packet in queue:
                args = packet.split(' ')

                # check for pong, dont waste time
                if args[0] == 'PING':
                    e.send('PONG ' + args[1])
                    continue

                # something went wrong server-side
                if args[0] == 'ERROR':
                    self.dead(e)
                    return

                # A healthy client, check for module triggers
                if e.status == lib.Client.Status.ONLINE:
                    if args[1] == 'PRIVMSG':
                        self.event.message(e, packet, args)
                    elif args[1] == 'NOTICE':
                        self.event.notice(e, packet, args)
                    elif args[1] == 'JOIN':
                        self.event.join(e, args)
                    elif args[1] == 'PART':
                        self.event.part(e, packet, args)
                    elif args[1] == 'INVITE':
                        self.event.invite(e, args[3][1:])
                    elif args[1] == 'PONG':
                        # we've been replied to
                        e.pingAttempts = 0
                    elif args[1] == 'INVITE':
                        self.event.invite(e, args[3][1:])
                    # (CoreMod Hook) Returning an identified user response from WHOIS
                    elif args[1] == '307':
                        self.event.authenticate(e, args[3])
                    else:
                        if self.debug:
                            self.log.write('(unhandled packet) ' + packet)

                # A client still CONNECTING
                if e.status == lib.Client.Status.CONNECTING:
                    if args[1] == '433': # nick in use
                        e.quit() # close this connection
                        self.log.write('!! error - nick in use with bot:\n'+ str(e))
                        quit() # quit the program
                        # TODO - better handle nick in use errors
                    if args[1] == '376' or args[1] == '254': # assume we are connected now
                        # identify with nickserv
                        if not e.profile.nickserv == None:
                            e.msg('NickServ', 'identify ' + e.profile.nickserv)
                        # set our UMODES
                        if not e.profile.umodes == None:
                            e.send('MODE ' + e.profile.nick + ' ' + e.profile.umodes)
                        time.sleep(0.25) # give NickServ time to identify us
                        # check autojoin
                        if not e.profile.ajoin == None:
                            for chan in e.profile.ajoin:
                                e.join(chan)
                        # change our status
                        e.status = lib.Client.Status.ONLINE
                        self.log.write('(Client) ' + e.profile.nick + '@' + e.profile.network.name + ' connected.')
                    continue

                # a client just booting up
                if e.status == lib.Client.Status.BOOTING:
                    if not packet == '':
                        e.identify()
                    continue

    def execute(self):
        # make sure we have clients to be handled
        if len(self.clients) == 0:
            self.log.write('Error: no bots to be connected -- check run.py')
            return

        # Helpful little printout
        self.log.write('(Event) Loaded ' + str(len(self.event.modules)) + ' modules.')
        self.log.write('(Timer) Loaded ' + str(len(self.timer.collection)) + ' timed-functions.')

        # start to handle the clients now
        while True:
            # handle clients now
            self.cycle()

            # check Timed-Functions
            self.timer.cycle()

            # prevent cpu lockup
            time.sleep(0.01)

class Module:
    # Module profile
    # Module name, [types], active
    def __init__(self, name, types, active=True):
        self.name = name
        self.types = types if type(types) is list else [types]
        self.active = active

class Profile:
    # Client profile
    # Nick name, Network (see below), NickServ Password (optional)
    def __init__(self, nick, network, nspw=None):
        self.nick = nick
        self.network = network
        self.nickserv = nspw
        self.umodes = None
        self.ajoin = None

class Network:

    # Network profile
    # Address (IP), port, ssl enabled, server password
    def __init__(self, name, address, port=6667, ssl=False, password=None):
        self.name = name
        self.address = address
        self.port = port
        self.ssl = ssl
        self.password = password

def timedString(seconds):
	m = int(seconds / 60)
	s = int(seconds - (m * 60))
	h = 0 if m < 60 else m / 60
	m = m if h == 0 else m - (h * 60)
	d = 0 if h < 24 else h / 24
	h = h if d == 0 else h - (d * 24)
	return ('' if d == 0 else str(d) + 'd') + ('' if h == 0 else str(h) + 'h') + ('' if m == 0 else str(m) + 'm') + str(s) + 's';
