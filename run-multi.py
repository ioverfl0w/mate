from lib import Engine
from mods import Hilight
from mods import Stats

# Example configuration for multiple clients on multiple networks under a single program

# Engine creation
# Debug mode is set when any value but 0 is declared in args
engine = Engine.Engine(0)

# Rizon Network
# lib.Engine.Network(address, port, sslEnabled, servPassword)
rizon = Engine.Network('Rizon', 'sli.rizon.net', 6667)

# Client Profiles
# Testing different options for multiple client loading easily
clients = {'clients': [Engine.Profile('token', rizon),
                Engine.Profile('tiken', rizon),
                Engine.Profile('teken', rizon) ] }

# Demonstrate a 4th connection to a separate network, using the single
# client format rather than the multi client Json
freenode = Engine.Profile('mate-pyirc', Engine.Network('Freenode', 'irc.freenode.net', 6697, True))
freenode.ajoin = ['##mate-testing']


# Client autojoin channels
clients['ajoin'] = ['#apollo']

# Client UMODES autoset
clients['umodes'] = "+p"

# Insert our new Clients into engine
engine.addClients(clients) #insert out list of Rizon clients
engine.addClient(freenode) # insert our single Freenode client

# Load our modules
engine.event.loadMod(Hilight.Hilight('paste.ee-api-key-here'))
engine.event.loadMod(Stats.Stats())

# Start the Engine
engine.execute()
