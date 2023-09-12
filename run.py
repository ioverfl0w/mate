from lib import Engine
from mods import Alarm
from mods import DrudgeMod
from mods import Lotto
from mods import Stats
from mods import OSRS
from timer import AlarmClock
from timer import DrudgeTimer
from timer import OSRSTimer

# Engine creation
# Debug mode is set when any value but 0 is declared in args
engine = Engine.Engine(1)

# Rizon Network
# lib.Engine.Network(address, port, sslEnabled, servPassword)
rizon = Engine.Network('Rizon', 'irc.rizon.net', 6697, True)

# Client Profile
# lib.Engine.Profile(nick, network, nickservPass)
token = Engine.Profile('Hans', rizon, 'howlonghaveibeenhereosrs03') #

# Client autojoin channels
# TODO allow all config to be saved within a database file created from a setup program
token.ajoin = ['#osrs', '#nova', '#drudge', '#2003scape', '#runescape', '#trollhour', '#ghetty.space', '#asia', '#ethereal', '#steam', '#code', '#chat', '#games', '#linux']  #

# Client UMODES autoset
# token.umodes = ''

# Insert our new Client into engine
engine.addClient(token)
client = engine.getClient(token)

osrs = OSRS.OSRS(engine)
alarmClock = AlarmClock.AlarmClock(engine)
drudge = DrudgeTimer.DrudgeTimer(engine)

drudge.add_subscription(client, '#drudge')

# Load our modules
engine.event.loadMod(Stats.Stats())
engine.event.loadMod(osrs)
engine.event.loadMod(Alarm.Alarm(alarmClock))
engine.event.loadMod(DrudgeMod.DrudgeMod(drudge))
# engine.event.loadMod(Lotto.Lotto())

# Load our Timers
engine.timer.loadTimeFunc(OSRSTimer.OSRSTimer(engine, osrs))
engine.timer.loadTimeFunc(alarmClock)
engine.timer.loadTimeFunc(drudge)

# Start the Engine
engine.execute()
