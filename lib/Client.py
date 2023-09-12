from enum import Enum
import ssl
import socket
import traceback
import time


class Client:

    # Client
    #
    # This is the backbone to each client, providing an interface for
    # communications. Connection info is kept here.

    def __init__(self, engine, profile):
        self.engine = engine
        self.profile = profile
        self.socket = None
        self.status = Status.OFFLINE

        # Hook from Pinger.py timed-function
        self.pingAttempts = 0

    # Return user's permission level regardless if authed
    def getRights(self, nick):
        return self.engine.access.userRights(self, nick)

    # Return user's permissions based on if Authed
    def activeRights(self, nick):
        return self.engine.access.getCurrentRights(self, nick)

    def quit(self, msg='Goodbye .. '):
        try:
            self.send('QUIT :' + msg)
            time.sleep(.5)
            self.sock.close()
        except Exception:
            pass
        # we have closed our own connection
        self.status = Status.OFFLINE

    def connect(self):
        # we're trying to boot up now
        self.status = Status.BOOTING

        # establish our connection
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((self.profile.network.address, self.profile.network.port))
        self.pingAttempts = 0
        # wrap our socket for ssl
        if self.profile.network.ssl:
            self.sock = ssl.wrap_socket(self.sock)
        self.sock.setblocking(0)

    def identify(self):
        # we are now establishing our connection
        self.status = Status.CONNECTING

        # send our server password
        if self.profile.network.password is not None:
            self.send('PASS ' + self.profile.network.password)
            time.sleep(1)

        # establish who we are with server
        self.send('NICK ' + self.profile.nick)
        self.send('USER ' + self.profile.nick + ' * * :m8')

    def msg(self, target, content):
        self.send('PRIVMSG ' + target + ' :' + content)

    def notice(self, target, content):
        self.send('NOTICE ' + target + ' :' + content)

    def join(self, channel):
        self.send('JOIN ' + channel)

    def part(self, channel):
        self.send('PART ' + channel)

    def mode(self, channel, modes):
        self.send('MODE ' + channel + ' ' + modes)

    def whois(self, nick):
        self.send('WHOIS :' + nick)

    def kick(self, channel, target, reason='Goodbye', ban=False):
        if ban:
            # TODO:
            # ban better with host names
            self.mode(channel, '+b ' + target + '!*@*')
        self.send('KICK ' + channel + ' ' + target + ' :' + reason)

    def send(self, content):
        try:
            self.sock.send(bytes(content + '\r\n', 'utf-8'))
            if self.engine.debug:
                self.engine.log.write('>>> ' + content)  # debug (NOTICE - can display sensitive info in Log!)
        except Exception:
            if self.sock is None:
                self.engine.log.write('Attempted to send message to disconnected socket')
                return
            self.engine.log.write('error writing')
            print(traceback.format_exc())
            self.engine.dead(self)

    def read(self):
        try:
            return self.sock.recv(4096).decode('utf-8').strip()
        except socket.error:
            return ''

    def __str__(self):
        return '[Nick:' + self.profile.nick + ',Network:' + self.profile.network.name + \
            ', Addr:' + self.profile.network.address + ',Port:' + \
            str(self.profile.network.port) + ',SSL:' + str(self.profile.network.ssl) + \
            ',' + str(self.status) + ']';


class Status(Enum):
    OFFLINE = 0,
    ONLINE = 1,
    CONNECTING = 2,
    BOOTING = 3,
    HALTED = 4
