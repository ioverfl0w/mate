import mods.CoreMod

class Event:

    # Event
    #
    # Parse incoming packets to be handled by loaded and active Modules.
    # TODO - implement core modules to be loaded by default here, not run.py

    def __init__(self, engine):
        self.engine = engine
        self.log = self.engine.log
        self.modules = [] # Module storage

        # We can ensure some modules are loaded here
        self.loadMod(mods.CoreMod.CoreMod()) # CoreModule

    def message(self, client, packet, args):
        user = self.getUser(args[0])
        message = packet[packet[1:].index(' :') + 3:]
        for mod in self.getMods('PRIVMSG'):
            mod.message(client, user, args[2] if args[2].startswith('#') else user[0], message)

    def notice(self, client, packet, args):
        user = self.getUser(args[0])
        message = packet[packet[1:].index(' :') + 3:]
        for mod in self.getMods('NOTICE'):
            mod.notice(client, user, args[2], message)

    def join(self, client, args):
        user = self.getUser(args[0])
        for mod in self.getMods('JOIN'):
            mod.join(client, user, args[2][1:])

    def kick(self, client, packet, args):
        user = self.getUser(args[0])
        try:
            message = packet[packet.index(args[4]) + 1:]
        except:
            message = None
        for mod in self.getMods('KICK'):
            mod.kick(client, args[2], user, args[3], message)

    def part(self, client, packet, args):
        user = self.getUser(args[0])
        message = packet[packet.index(args[3]) + 1:]
        for mod in self.getMods('PART'):
            mod.part(client, user, message)

    def nick(self, client, args):
        oldNick = self.getUser(args[0])
        for mod in self.getMods('NICK'):
            mod.nick(client, oldNick, args[2][1:])

    def authenticate(self, client, user):
        # TODO - create a timed-function that can automatically destory authenticated
        # sessions when duration has expired.
        pass

    # We are going to join any channel we are invited to
    def invite(self, client, location):
        # TODO - better secure from abuse
        client.join(location)

    def getUser(self, raw):
        try:
            raw = raw[1:]
            return [raw[:raw.index('!')], raw[raw.index('!') + 1:raw.index('@')],raw[raw.index('@') + 1:]]
        except:
            return raw

    def getMods(self, type):
        mods = []
        for mod in self.modules:
            for t in mod.module.types:
                if t == type and mod.module.active:
                    mods.append(mod)
                    continue
        return mods

    def loadMod(self, mod):
        #self.log.write('(Event) Loading module ' + mod.module.name + ' (' + ('active' if mod.module.active else 'dormant') + ')')
        self.modules.append(mod)
