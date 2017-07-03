import lib.Engine

# Rizon Network
# lib.Engine.Network(address, port, sslEnabled, servPassword)
rizon = lib.Engine.Network('irc.rizon.net', 6697, True)

# Client Profile
# lib.Engine.Profile(nick, network, nickservPass)
token = lib.Engine.Profile('mate', rizon)

# Client autojoin channels
token.ajoin = ["#mate"]

# Client UMODES autoset
token.umodes = "+p"

# Engine creation
engine = lib.Engine.Engine()

# Insert our new Client into engine
engine.addClient(token)

# Start the Engine
engine.execute()
