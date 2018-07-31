from lib import Engine
from mods import Hilight
from mods import MarkSpeak
from mods import Stats

# Engine creation
# Debug mode is set when any value but 0 is declared in args
engine = Engine.Engine(1)

# Rizon Network
# lib.Engine.Network(address, port, sslEnabled, servPassword)
rizon = Engine.Network('Rizon', 'irc.rizon.net', 6697, True)

# Client Profile
# lib.Engine.Profile(nick, network, nickservPass)
token = Engine.Profile('token', rizon)

# Client autojoin channels
token.ajoin = ["#apollo"]

# Client UMODES autoset
token.umodes = "+p"

# Insert our new Client into engine
engine.addClient(token)

# Load our modules
#engine.event.loadMod(Hilight.Hilight('paste.ee-api-key-here'))
engine.event.loadMod(MarkSpeak.MarkSpeak())
engine.event.loadMod(Stats.Stats())

# Start the Engine
engine.execute()
