from lib import Engine
from mods import Hilight
from mods import Relay
from mods import Stats

# Example configuration for multiple clients running the Relay module

# Engine creation
# Debug mode is set when any value but 0 is declared in args
engine = Engine.Engine(1)

# Rizon Network
# lib.Engine.Network(address, port, sslEnabled, servPassword)
rizon = Engine.Profile('token', Engine.Network('Rizon', 'sli.rizon.net', 6697, True))
rizon.ajoin = ['#apollo']

mopar = Engine.Profile('token', Engine.Network('Mopar', 'irc.moparisthebest.com', 6697, True))
mopar.ajoin = ['#bots']

# Insert our new Clients into engine
engine.addClient(rizon)
engine.addClient(mopar)

#Configuration for Relay module between networks
#It is important to use getClient, not just use the profiles above
relay = Relay.Relay()
relay.link(engine.getClient(rizon), rizon.ajoin[0])
relay.link(engine.getClient(mopar), mopar.ajoin[0])

# Load our modules
engine.event.loadMod(Stats.Stats())
engine.event.loadMod(relay)

# Start the Engine
engine.execute()
