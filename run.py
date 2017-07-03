import lib.Engine

# Engine creation
engine = lib.Engine.Engine()

# Rizon Network
# lib.Engine.Network(address, port, sslEnabled, servPassword)
rizon = lib.Engine.Network('irc.rizon.net', 6697, True)

# Client Profile
# lib.Engine.Profile(nick, network, nickservPass)
token = lib.Engine.Profile('token', rizon)

# Client autojoin channels
token.ajoin = ["#apollo"]

# Client UMODES autoset
token.umodes = "+p"

# Insert our new Client into engine
engine.addClient(token)

# Load our modules

# Start the Engine
engine.execute()
