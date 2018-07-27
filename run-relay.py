from lib import Engine
from mods import Hilight
from mods import Relay
from mods import Stats

# Example configuration for multiple clients on multiple networks under a single program

# Engine creation
# Debug mode is set when any value but 0 is declared in args
engine = Engine.Engine(1)

# Rizon Network
# lib.Engine.Network(address, port, sslEnabled, servPassword)
rizon = Engine.Network('Rizon', 'sli.rizon.net', 6697, True)

# Client Profiles
# Testing different options for multiple client loading easily
clients = {'clients': [Engine.Profile('token', rizon),
                Engine.Profile('tiken', rizon)] }

# Demonstrate a 4th connection to a separate network, using the single
# client format rather than the multi client Json
mopar = Engine.Profile('token', Engine.Network('MoparNet', 'irc.moparisthebest.com', 6697, True))
mopar.ajoin = ['#bots']


# Client autojoin channels
clients['ajoin'] = ['#apollo']

# Client UMODES autoset
clients['umodes'] = "+p"

# Insert our new Clients into engine
engine.addClients(clients) #insert out list of Rizon clients
engine.addClient(mopar) # insert our single Freenode client

# Establish Clients
# TODO - make this look better
main = engine.getClient(clients['clients'][0])
link1 = engine.getClient(clients['clients'][1])
link2 = engine.getClient(mopar)

#Configuration for Relay module between networks
relay = Relay.Relay([link1, link2])
relay.link(link1, '#apollo')
relay.link(link2, '#bots')

# Load our modules
#engine.event.loadMod(Hilight.Hilight('paste.ee-api-key-here'))
engine.event.loadMod(Stats.Stats(main))
engine.event.loadMod(relay)

# Start the Engine
engine.execute()
