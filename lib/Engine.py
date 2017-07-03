import lib.Client
import lib.Event
import lib.Logger
import time

class Engine:

    # Engine
    #
    # This will ensure all clients are processed and managed. will
    # attempt to reconnect disconnected bots (TODO add 'halted' option)

    def __init__(self):
        # our clients
        self.clients = []
        # start a log
        self.log = lib.Logger.Logger()
        # start an Event engine
        self.event = lib.Event.Event(self)

    def addClient(self, profile):
        #add a new client to our queue
        self.clients.append(lib.Client.Client(self, profile))

    def dead(self, client):
        # a client has reported a dead connection,
        # we need to fix this be reconnecting
        self.log.write('! client reported dead !')
        client.status = lib.Client.Status.OFFLINE
        pass

    def check(self):
        for e in self.clients:
            # A client that is offline
            if e.status == lib.Client.Status.OFFLINE:
                self.log.write('Connecting ' + str(e))
                e.connect()
                continue

            # we are expecting something
            incoming = str(e.read())
            if incoming == "":
                continue # screw off, blank lines

            # split different messages read at a single time
            queue = incoming.split('\n')

            for packet in queue:
                args = packet.split(" ")
                #self.log.write(str(e) + '\t' + packet) # debug

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
                    elif args[1] == 'INVITE':
                        self.event.invite(e, args[3][1:])
                    else:
                        self.log.write("(unhandled packet) " + packet)
                    continue

                # A client still CONNECTING
                if e.status == lib.Client.Status.CONNECTING:
                    if args[1] == '433': # nick in use
                        e.quit() # close this connection
                        self.log.write("!! error - nick in use with bot:\n" + str(e))
                        quit() # quit the program
                        # TODO - better handle nick in use errors
                    if args[1] == '376' or args[1] == '254': # assume we are connected now
                        # identify with nickserv
                        if not e.profile.nickserv == None:
                            e.msg('NickServ', 'identify ' + e.profile.nickserv)
                        # set our UMODES
                        if not e.profile.umodes == None:
                            e.send("MODE " + e.profile.nick + " " + e.profile.umodes)
                        time.sleep(0.25) # give NickServ time to identify us
                        # check autojoin
                        if not e.profile.ajoin == None:
                            for chan in e.profile.ajoin:
                                e.join(chan)
                        # change our status
                        e.status = lib.Client.Status.ONLINE
                    continue

                # a client just booting up
                if e.status == lib.Client.Status.BOOTING:
                    if not packet == "":
                        e.identify()
                    continue

    def execute(self):
        # make sure we have clients to be handled
        if len(self.clients) == 0:
            self.log.write('Error: no bots to be connected -- check run.py')
            return

        # start to handle the clients now
        while True:
            # handle clients now
            self.check()
            time.sleep(0.02) # prevent cpu lockup

class Profile:
    # Client profile
    # Nick name, NickServ Password, Network (see below)
    def __init__(self, nick, network, nspw=None):
        self.nick = nick
        self.network = network
        self.nickserv = nspw
        self.umodes = None
        self.ajoin = None

class Network:

    # Network profile
    # Address (IP), port, ssl enabled, server password
    def __init__(self, address, port=6667, ssl=False, password=None):
        self.address = address
        self.port = port
        self.ssl = ssl
        self.password = password
