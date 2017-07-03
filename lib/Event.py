class Event:

    def __init__(self, engine):
        self.engine = engine
        self.log = self.engine.log
        self.modules = [] # Module storage

    def message(self, client, packet, args):
        user = self.getUser(args[0])
        message = packet[packet[1:].index(' :') + 3:]
        for mod in self.getMods('PRIVMSG'):
            mod.message(client, user, args[2], message)

    def notice(self, client, packet, args):
        pass

    def getUser(self, raw):
        try:
            raw = raw[1:]
            return [raw[:raw.index('!')], who[who.index('!') + 1:who.index('@')],raw[raw.index('@') + 1:]]
        except:
            return raw

    def getMods(self, type):
        mods = []
        for mod in self.modules:
            for t in mod.types:
                if t == type and mod.active:
                    mods.append(mod)
                    continue
        return mods

    def loadMod(self, module):
        self.log.write('(event) loading module ' + module.name)
        self.modules.append(module)
