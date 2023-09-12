import mods.CoreMod
from lib import Access

class Event:

    # Event
    #
    # Parse incoming packets to be handled by loaded and active Modules.

    def __init__(self, engine):
        self.engine = engine
        self.log = self.engine.log
        self.modules = []  # Module storage
        self.unloaded = []  # Disabled modules

        # We can ensure some modules are loaded here
        self.loadMod(mods.CoreMod.CoreMod())  # CoreModule

    def message(self, client, packet, args):
        user = self.getUser(args[0])
        message = packet[packet[1:].index(' :') + 3:]
        for mod in self.getMods('PRIVMSG'):
            if mod.module.clients is None or client in mod.module.clients:
                mod.message(client, user, args[2] if args[2].startswith('#') else user[0], message)

    def notice(self, client, packet, args):
        user = self.getUser(args[0])
        message = packet[packet[1:].index(' :') + 3:]
        for mod in self.getMods('NOTICE'):
            if mod.module.clients is None or client in mod.module.clients:
                mod.notice(client, user, args[2], message)

    def join(self, client, args):
        user = self.getUser(args[0])
        for mod in self.getMods('JOIN'):
            if mod.module.clients is None or client in mod.module.clients:
                mod.join(client, user, args[2][1:])

    def kick(self, client, packet, args):
        print(packet)
        user = self.getUser(args[0])
        try:
            message = packet[packet.index(args[4]) + 1:]
        except:
            message = None
        for mod in self.getMods('KICK'):
            if mod.module.clients is None or client in mod.module.clients:
                # [0] client, [1] user(kicker), [2] location, [3] kicked, [4+] msg
                mod.kick(client, user, args[2], args[3], message)

    def part(self, client, packet, args):
        user = self.getUser(args[0])
        # TODO - fix the message argument for parts
        # message = packet[packet.index(args[3]) + 1:]
        for mod in self.getMods('PART'):
            if mod.module.clients is None or client in mod.module.clients:
                mod.part(client, user, args[2])

    def mode(self, client, packet, args):
        user = self.getUser(args[0])
        for mod in self.getMods('MODE'):
            if mod.module.clients is None or client in mod.module.clients:
                mod.mode(client, user, args[2],
                (packet[packet.index(args[2]) + len(args[2]) + 1:] if len(args) > 3 else ''))

    def nick(self, client, args):
        oldNick = self.getUser(args[0])
        for mod in self.getMods('NICK'):
            if mod.module.clients is None or client in mod.module.clients:
                mod.nick(client, oldNick, args[2][1:] if args[2].startswith(':') else args[2])

    def quit(self, client, args):
        user = self.getUser(args[0])
        for mod in self.getMods('QUIT'):
            if mod.module.clients is None or client in mod.module.clients:
                ## TODO:
                # Maybe we should pass on the messages (known to break sometimes)
                mod.quit(client, user)

    def namelist(self, client, packet, args):
        for mod in self.getMods('NAMELIST'):
            if mod.module.clients is None or client in mod.module.clients:
                # Location, User
                mod.namelist(client, args[3], [args[7],args[4], args[5]])
                
    def identify(self, client, nick):
        # we have sent a whois, and this user is currently registered.
        for mod in self.getMods('IDENTIFY'):
            mod.identify(client, nick)

    # We are going to join any channel we are invited to
    def invite(self, client, user, location):
        user = self.getUser(user)
        if client.activeRights(user[0]) >= Access.LEVELS['TRUSTED']:
            client.join(location)

    def getUser(self, raw):
        try:
            raw = raw[1:]
            return [raw[:raw.index('!')], raw[raw.index('!') + 1:raw.index('@')], raw[raw.index('@') + 1:]]
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
        if self.engine.debug:
            self.log.write('(Event) Loading module ' + mod.module.name + ' (' + ('active' if mod.module.active else 'dormant') + ')')
        self.modules.append(mod)

    def get_mod(self, name):
        for mod in self.modules:
            if mod.name == name:
                return mod
        return None
    
    def unload(self, name):
        for mod in self.modules:
            if mod.module.name.lower() == name:
                self.modules.remove(mod)
                self.unloaded.append(mod)
                return True
        return False
    
    def reload(self, name):
        for mod in self.unloaded:
            if mod.module.name.lower() == name:
                self.loadMod(mod)
                self.unloaded.remove(mod)
                return True
        return False
    
    def get_list(self):
        active = []
        for m in self.modules:
            active.append(m.module.name)
        inactive = []
        for m in self.unloaded:
            inactive.append(m.module.name)
        return [active, inactive]
    
    def reload_mods(self):
        if len(self.unloaded) > 0:
            self.modules = self.modules + self.unloaded
            self.unloaded = []
        for mod in self.modules:
            try:
                mod.reload_mod()
            except Exception:
                pass