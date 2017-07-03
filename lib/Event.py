class Event:

    def __init__(self, engine):
        self.engine = engine
        self.log = self.engine.log
        self.modules = []

    def handle(self, client, packet, args):
        pass
