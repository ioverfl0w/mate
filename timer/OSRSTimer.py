import lib.Timer
from mods import OSRS
import time

# The amount of time to wait to refresh a user's hiscore page. We don't want to get throttled by RuneScape.
updateTimer = 15  # minutes
maxLenMessage = 400  # Max characters per message


class OSRSTimer:

    # OSRSTimer
    #
    # Automatically announce level increases to desired channels. Compare new stats with previous to
    # provide a short summary of XP gains, HiScore changes, Boss kills, etc
    #
    # This timer module maintains the local storage of RS stats.

    def __init__(self, engine, osrs):
        # every timed-function needs to have a Schedule
        # lib.Timer.Schedule(name, delay (in seconds))
        self.schedule = lib.Timer.Schedule('OSRSTimer', 30)  # 30 seconds interval
        self.engine = engine  # Provides us access to the engine
        self.osrs = osrs  # Provides access to the linked OSRS user database
        self.osrs.osrsTimer = self  # Give the OSRS Module access to the local storage
        self.rsaccounts = []  # RSName, timelast updated, IRC Network, last stats
        if self.loadRsAccounts():
            self.engine.log.write('(OSRSTimer) LOAD COMPLETE. ' + str(len(self.rsaccounts)) + ' linked accounts.')
        else:
            self.engine.log.write('(OSRSTimer) Error loading. Please review console.log')

    # Timed-Functions are called from the Engine, so you have to determine
    # either to broadcast to all Clients or create a method to remember
    # which client you want.
    def execute(self, engine):
        x = 0  # our position in the rsaccounts array
        g = 0  # how many stats have changed
        for acc in self.rsaccounts:
            if acc[1] < time.time():
                rsn = str(acc[0])
                newStats = self.osrs.getStats(rsn)
                if newStats is None:
                    self.engine.log.write('(OSRSTimer) There was an issue getting stats..')
                    return
                if not str(newStats) == str(acc[2]):
                    if self.announceGains(x, rsn, newStats, acc):  # this will check if xp/kc have changed, not just hiscores
                        self.rsaccounts[x][3] = newStats  # update our stats
                        g += 1  # an account has been modified!

                self.rsaccounts[x][1] = time.time() + (updateTimer * 60)
            x += 1
        if g > 0:
            self.engine.log.write('(OSRSTimer) ' + str(g) + ' account' + ('' if g == 1 else 's') + ' experienced some gains')

    # Find the changed stats and create a message for IRC
    def announceGains(self, pos, rsn, newStats, acc):
        changes = []
        i = 0
        # let's find what changed
        while i < len(newStats) - 1:  # the last value is invalid
            if i == 0:  # checking total level milestones
                print('debug -- newStats & acc -- fetching stats for ' + rsn)
                print(newStats[i])
                print(acc[3][i])
                if newStats[i][1] > acc[3][i][1]:
                    # Add the following to limit how often we announce total levels
                    # if newStats[i][1] > 2000 or (str(newStats[i][1]).endswith('50') or str(newStats[i][1]).endswith('25') or str(newStats[i][1]).endswith('00')):
                    changes.append([i, 2])
            elif i < 24:  # stat achievements (hiscore, level, xp)
                if newStats[i][2] > acc[3][i][2]:  # gained xp, we will ignore when the stats are removed from hiscores bc of rank
                    changes.append([i, 1])

            else:  # everything else (hiscore, KC)
                if newStats[i][1] > acc[3][i][1]:  # change in boss KC
                    if not newStats[i][1] == -1:
                        changes.append([i, 0])  # 0 for boss/scrolls
            i += 1

        # if nothing is really changed, lets stop now.
        if len(changes) == 0:
            return False

        # build the message now
        i = 0
        header = '\0033[OSRS] \00304' + rsn + '\003 :: '  # Username header
        count = 0
        message = [header]
        for x in changes:
            msg = ''
            p = x[0]
            if p < 0 or p is OSRS.ALLCLUES:  # -1, 30 is All clues combined. We will separate them based on difficulty (ALLCLUES)
                i += 1
                continue

            # Better form continuing gains
            if i > 0:
                msg += ', '

            name = OSRS.STATS[p][1]  # our emoji for our message
            if self.engine.debug:
                self.engine.log.write('(Gains) ' + name + ' ' + str(newStats[p]))  # log our process
            rank = None if newStats[p][0] < 1 else str(f'{newStats[p][0]:,}')  # our rank for this skill/task
            lvl = newStats[p][1]  # this is either Level or Boss KC
            oLvl = acc[3][p][1]

            if x[1] is 0:  # Boss/task
                msg += 'Completed \00303' + str(lvl - oLvl) + ' \00307' + OSRS.STATS[p][0]
                msg += ' \0039(Total Complete: ' + str(newStats[p][1])
                msg += ('; Rank: ' + rank if rank is not None else '') + ')'

            elif x[1] is 1:  # Experience!
                ch = newStats[p][2] - acc[3][p][2]
                msg += name + '\00303+' + OSRS.cleanXPStr(ch) + '\003 xp \0039('
                msg += 'Lvl: ' + str(lvl) if lvl == oLvl else '\0033🎉 Lvl ' + str(lvl) + '(\0038+' + str(lvl - oLvl) + '\0033) 📈 '
                msg += '\00309' + ('' if rank is None else '; Rank: ' + rank) + ')'

            elif x[1] is 2:  # Total level achievement!
                msg += ('\0038🎉 Achieved Total Level ' + str(lvl) + ' (+' + str(lvl - oLvl) + ') ' ) + ('' if rank is None else '\0039(Rank: ' + rank + ') ') + '🎉'

            i += 1
            if len(message[count]) + len(msg) > maxLenMessage:
                count += 1
                message.append(header + msg[2:])
            else:
                message[count] += msg

        # Iterate the message to all linked channels
        # TODO - ""users"" per network should be able to specify whether they want their stats broadcast to all channels, or specific channels
        for clientt in self.engine.clients:
            for chan in self.osrs.getChannels(clientt, False):  # this will filter in all channels, so we can check if the user wants to broadcast
                if (chan[5] == OSRS.PUBLIC) or (self.osrs.existingLink(clientt, rsn) in chan[6]):  # channel is public, or RSN is whitelisted
                    print(msg)
                    for m in message:
                        clientt.msg(chan[3], m)
        return True

    # Retrieve the RS stats for this account that was last pulled from the HiScores
    def getLocalStats(self, account):
        account = account.lower()
        for stats in self.rsaccounts:
            if account == stats[0]:
                return stats[3]
        return None

    # This method, called upon init, will load the entire list of accounts
    def loadRsAccounts(self):
        accounts = []
        i = 0
        l = self.osrs.getAllAccounts()
        if len(l) == len(self.rsaccounts):
            return False
        for x in self.osrs.getAllAccounts():
            rsn = str(x[3])
            accounts.append([rsn, (time.time() + (updateTimer * 30) + (i * 60)), x[1], self.osrs.getStats(rsn)])
            if self.engine.debug:
                self.engine.log.write('(OSRSTimer) Loaded RSAccount #' + str(x[0]) + ' - ' + str(x))
            i += 1
        self.rsaccounts = accounts
        return True
