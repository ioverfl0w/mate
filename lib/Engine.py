from lib import Access
from lib import Client
from lib import Event
from lib import Logger
import time
from lib import Timer

class Engine:

    # Engine
    #
    # This will ensure all clients are processed and managed. will
    # attempt to reconnect disconnected bots (TODO add 'halted' option)

    def __init__(self, DEBUG=0):
        # Debug MODE
        self.debug = False if DEBUG == 0 else True
        # our clients
        self.clients = []
        # start a log
        self.log = Logger.Logger()
        # start an Event engine
        self.event = Event.Event(self)
        # start a Time Keeper
        self.timer = Timer.TimeKeeper(self)
        # start an Access system (must load after Timer)
        self.access = Access.Access(self)

    def addClient(self, profile):
        #add a new client to our queue
        self.clients.append(Client.Client(self, profile))

    def addClients(self, profiles):
        for prof in profiles['clients']:
            # Set globally set UMODES
            try:
                prof.umodes = profiles['umodes']
            except:
                pass
            # Set globally set ajoin
            try:
                prof.ajoin = profiles['ajoin']
            except:
                pass

            # Insert this client
            self.addClient(prof)

    def getClient(self, profile):
        for client in self.clients:
            if client.profile == profile:
                return client
        return None

    def dead(self, client):
        # a client has reported a dead connection,
        # we need to fix this be reconnecting
        self.log.write('! client reported dead ! ' + str(client))
        client.status = Client.Status.OFFLINE
        pass

    def cycle(self):
        halted = 0
        for e in self.clients:
            # A client that is no longer active, Ignored
            if e.status == Client.Status.HALTED:
                halted += 1
                continue

            # A client that is offline
            if e.status == Client.Status.OFFLINE:
                self.log.write('(Engine) Connecting ' + e.profile.nick + ' to ' +\
                            e.profile.network.address + ':' + ('+' if e.profile.network.ssl else '') + str(e.profile.network.port) + ' ...')
                e.connect() #build the socket layers
                e.identify() # communicate with the server and log in
                time.sleep(1)
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
                if e.status == Client.Status.ONLINE and len(args) > 1:
                    if args[1] == 'PRIVMSG':
                        self.event.message(e, packet, args)
                    elif args[1] == 'NOTICE':
                        self.event.notice(e, packet, args)
                    elif args[1] == 'JOIN':
                        self.event.join(e, args)
                    elif args[1] == 'PART':
                        self.event.part(e, packet, args)
                    elif args[1] == 'KICK':
                        self.event.kick(e, packet, args)
                    elif args[1] == 'INVITE':
                        self.event.invite(e, args[3][1:])
                    elif args[1] == 'PONG':
                        # we've been replied to
                        e.pingAttempts = 0
                    elif args[1] == 'NICK':
                        self.event.nick(e, args)
                    elif args[1] == 'QUIT':
                        self.event.quit(e, args)
                    elif args[1] == 'MODE':
                        self.event.mode(e, packet, args)
                    # (Relay Hook) Checks for NAMELIST responses
                    elif args[1] == '352':
                        self.event.namelist(e, packet, args)
                    # (CoreMod Hook) Returning an identified user response from WHOIS
                    elif args[1] == '307' or args[1] == '330':# Rizon uses 307, MITB uses 330
                        self.access.auth(e, args[3])

                    if self.debug:
                        self.log.write('(packet) ' + packet)

                # A client still CONNECTING
                if e.status == Client.Status.CONNECTING:
                    if args[1] == '433': # nick in use
                        e.quit() # close this connection
                        self.log.write('(Engine) !! CLIENT HALTED !! nick in use -> '+ str(e))
                        e.status = Client.Status.HALTED
                        continue
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
                        e.status = Client.Status.ONLINE
                        self.log.write('(Engine) Client ' + e.profile.nick + ' on ' + e.profile.network.name + ' connected.')
                    continue

        # If all of our clients are halted, shutdown program
        if halted == len(self.clients):
            self.log.write('(Engine) No active clients, terminating...')
            return quit()

    def execute(self):
        # make sure we have clients to be handled
        if len(self.clients) == 0:
            self.log.write('(Engine) Error: no bots to be connected -- check run.py')
            return

        # Helpful little printout
        self.log.write('(Engine) Loaded ' + str(len(self.clients)) + ' client' + ('s' if len(self.clients) > 1 else '') + '.')
        self.log.write('(Event) Loaded ' + str(len(self.event.modules)) + ' module' + ('s' if len(self.event.modules) > 1 else '') + '.')
        self.log.write('(Timer) Loaded ' + str(len(self.timer.collection)) + ' timed-function' + ('s' if len(self.timer.collection) > 1 else '') + '.')

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
    def __init__(self, name, types, clients=None, active=True):
        self.name = name #the module name
        self.types = types if type(types) is list else [types] #either a single Type string to array of strings
        self.clients = clients if type(clients) is list or clients == None else [clients] # Specify which client(s) use this module
        self.active = active #module status (active or dormant)

class Profile:
    # Client profile
    # Nick name, Network (see below), NickServ Password (optional)
    def __init__(self, nick, network, nspw=None):
        self.nick = nick #current nick on network
        self.set_nick = nick #nick we want to be
        self.network = network #network associated with the profile
        self.nickserv = nspw #our nickserv ident password
        self.umodes = None #the umodes set upon connect
        self.ajoin = None #autojoin channels

class Network:

    # Network profile
    # Address (IP), port, ssl enabled, server password
    def __init__(self, name, address, port=6667, ssl=False, password=None):
        self.name = name #network name (case sensitive)
        self.address = address #network address
        self.port = port #network port
        self.ssl = ssl #use SSL protocols
        self.password = password #server password

def timedString(seconds):
    m = int(seconds / 60)
    s = int(seconds - (m * 60))
    h = int(0 if m < 60 else m / 60)
    m = int(m if h == 0 else m - (h * 60))
    d = int(0 if h < 24 else h / 24)
    h = int(h if d == 0 else h - (d * 24))
    return ('' if d == 0 else str(d) + 'd') + ('' if h == 0 else str(h) + 'h') + ('' if m == 0 else str(m) + 'm') + str(s) + 's';
