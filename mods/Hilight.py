class Hilight:

    # Hilight
    #
    # Maintains short message buffer for each channel, and pushes
    # Hilight events to them when they are next active.

    def __init__(self):
        self.module = lib.Engine.Module('Hilight', 'PRIVMSG')

    def message(self, client, user, channel, message):
        pass
