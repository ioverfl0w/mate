from enum import Enum
import ssl
import socket
import traceback

class Client:

    def __init__(self, engine, profile):
        self.engine = engine
        self.profile = profile
        self.socket = None
        self.status = Status.OFFLINE

    def quit(self):
        try:
            self.send('QUIT')
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
        # wrap our socket for ssl
        if self.profile.network.ssl:
            self.sock = ssl.wrap_socket(self.sock)
        self.sock.setblocking(0)

    def identify(self):
        # we are now establishing our connection
        self.status = Status.CONNECTING

        # establish who we are with server
        self.send('NICK ' + self.profile.nick)
        self.send('USER ' + self.profile.nick[0] + ' * * :' + self.profile.nick)

        # send our server password
        if not self.profile.network.password == None:
            self.send('PASS ' + self.profile.network.password)

    def msg(self, target, content):
        self.send('PRIVMSG ' + target + ' :' + content)

    def join(self, channel):
        self.send('JOIN ' + channel)

    def send(self, content):
        try:
            self.sock.send(bytes(content + '\r\n', 'utf-8'))
            self.engine.log.write('>>> ' + content)
        except Exception:
            if self.sock == None:
                self.engine.log.write('Attempted to send message to disconnected socket')
                return
            self.engine.log.write('error writing')
            print(traceback.format_exc())
            self.engine.dead(self)

    def read(self):
        try:
            return self.sock.recv(4096).decode('utf-8').strip()
        except socket.error:
            return ""

    def __str__(self):
        return "[Nick:" + self.profile.nick + ",Addr:" + self.profile.network.address + \
                ",Port:" + str(self.profile.network.port) + ",SSL:" + str(self.profile.network.ssl) + \
                "," + str(self.status) + "]";

class Status(Enum):
    OFFLINE = 0,
    ONLINE = 1,
    CONNECTING = 2,
    BOOTING = 3
