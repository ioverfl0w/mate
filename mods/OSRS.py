from lib import Access
from lib import Engine
import sqlite3
import requests

RSL = 'RsLinks'
RSC = 'RsChannels'
ALLCLUES = 30  # All Clues are noted in the array at #30. This could change and is used in several places.


def cleanXPStr(amount):
    st = str(amount)
    ln = len(st)
    ch = list(st)
    base = 4 if ln > 3 else 7 if ln > 6 else 1  # This declares what position we want to use, with what increment
    if base == 1:
        return st  # not enough xp gained to condense
    # Returns a ' 4.1K ' form response.
    x = ln - base + 1  # Give us 4K instead of 4.0K
    return str(st[:x]) + ('.' + str(ch[x]) if x > 0 else '') + ('K' if base == 4 else 'M' if base == 7 else '')


class OSRS:

    # Old School RuneScape Mod
    #
    # This module is designed to ease the way we share our stats with
    # friends on IRC.
    # todo add commands to adjust public toggle for individual nicks. this will allow their accounts to only be sent to channels they desire
    # todo add commands for channel sponsors to adjust their settings for public toggle, and to add/del nicks from allowlist_nicks

    def __init__(self, engine):
        self.module = Engine.Module('OSRSMod', ['PRIVMSG', 'JOIN', 'IDENTIFY'])
        self.joinBuff = []  # to ensure we dont get auth requests mixed in
        self.osrsTimer = None  # This gets set when the Timer is initialized
        self.channels = []
        self.engine = engine

        self.db = sqlite3.connect('./data/osrs.db')
        # Create databases if not established

        # This database stores the RS stats. It is linked to a nickname@network combination.0aaa
        # TODO stats should be stored 1 week and used to print a summary periodically about stats earned over the week
        self.db.execute('''
        create table if not exists ''' + RSL + ''' (
            id integer primary key autoincrement,
            network text not null,
            nick text not null,
            rsaccount text not null,
            channels text not null,
            public integer
        );''')
        # This database stores channels that allow broadcasting of updates. This will have the irc network name,
        # the channel sponsor (an op granting permission), and whether we will treat this channel as a 'home' channel (ie giving voice, etc)
        # public 0-broadcast all public accounts, 1-only broadcast nicks in allowlist
        self.db.execute('''
        create table if not exists ''' + RSC + ''' (
            id integer primary key autoincrement,
            network text not null,
            sponsornick text not null,
            channel text not null,
            controlled integer,
            public integer,
            allowlist_nicks text not null
        );''')
        self.syncChannels(None)

    # client - the client that is processing the event
    # user - [0] nick , [1] user , [3] host
    # channel - either a channel or the client's nick
    # message - the content of the message
    def message(self, client, user, channel, message):
        args = message.lower().split(' ')
        access = client.activeRights(user[0])

        if args[0] == '!help':
            client.msg(channel, user[0] + ': [OSRS Help] !hiscores (!hs) - !stats - !link - !unlink - !allowlist')

        if args[0] == '!hs' or args[0] == '!hiscores':
            return client.msg(channel, user[0] + ': https://secure.runescape.com/m=hiscore_oldschool/overall')

        # Command to look up stats of an RS Account. If no username is specified, the stats stored
        # locally will be used to look up their linked account.
        #
        # Syntax: !stats
        if args[0] == '!stats':
            if len(args) == 1:
                links = self.getLinkedAccounts(client, user[0])
                if not links:
                    return client.msg(channel, user[0] + ': There is no account linked to your nick.')
                return client.msg(channel, user[0] + ': ' + self.buildStatMsg(links[0]))
            name = message[message.lower().index(args[1]):]
            if len(name) > 12:
                return client.msg(channel, user[0] + ': Invalid RuneScape username.')
            return client.msg(channel, user[0] + ': ' + self.buildStatMsg(name))

        # Command used to link a RS Account to a nick@network
        #
        # Syntax: !link <osrs_name>

        if args[0] == '!link':
            if len(args) > 1:
                name = message[message.lower().index(args[1]):]
                if len(self.getLinkedAccounts(client, user[0])) == 3 and access < Access.LEVELS['ADMIN']:
                    return client.msg(channel, user[0] + ': You can currently only link three accounts per nick.')
                if len(name) > 12:
                    return client.msg(channel, user[0] + ': Invalid RuneScape username.')
                if self.existingLink(client, name):
                    return client.msg(channel, user[0] + ': That OSRS account is already linked to another nick.')
                if self.linkRsAccount(client, user[0], name, True, channel):
                    c = self.getChannels(client, True, True, True)
                    client.msg(channel, user[0] + ': Account ' + name + ' added to your roster! Your stat updates will post in ' + ', '.join(c) + ' each time after you log out.')
                    return client.notice(user[0], 'Please note: if your stats are not visible from the RuneScape HiScores, your stats will not show up here. (https://secure.runescape.com/m=hiscore_oldschool/overall.ws)')
                return client.msg(channel, user[0] + ': Unable to add account ' + name)
            links = self.getLinkedAccounts(client, user[0])
            if not links:
                return client.msg(channel, user[0] + ': Link up to three of your OSRS Accounts by using !link <osrs_name>')
            return client.msg(channel, user[0] + ': Your nick is currently linked with ' + ', '.join(links))

        # Command used to remove RuneScape accounts linked to their nick.
        #
        # Syntax: !unlink <osrs_name> confirm
        #
        if args[0] == '!unlink':
            if args[len(args) - 1] == 'confirm':
                if args[1] == '*':
                    acc = self.getLinkedAccounts(client, user[0])
                    if not acc:
                        return client.msg(channel, user[0] + ': You are not linked with any RuneScape accounts using !link')
                    for ac in acc:
                        if not self.unlinkRsAccount(client, user[0], ac):
                            client.msg(channel, user[0] + ': error removing account ' + ac)
                    return client.msg(channel, user[0] + ': You have been unlinked from the Old School RuneScape accounts: ' + ', '.join(acc))

                rsn = message[message.lower().index(args[1]):message.lower().index(args[len(args) - 1]) - 1].lower()
                for linked in self.getLinkedAccounts(client, user[0]):
                    if linked == rsn:
                        if self.unlinkRsAccount(client, user[0], rsn):
                            return client.msg(channel, user[0] + ': Your RuneScape account \'' + rsn + '\' has been unlinked.')
                        return client.msg(channel, user[0] + ': There was a problem removing that account.')
                return client.msg(channel, user[0] + ' That account is not linked with your nick. Check your linked accounts using !link')

            return client.msg(channel, user[0] + ': To confirm unlinking your RS Account, please type ' + args[0] + ' <rsaccount/*> confirm')

        # Channel allowlist - this will allow sponsors to decide which irc nicks are permitted to have their OSRS accounts streamed here
        if args[0] == '!allowlist':
            spons = self.isSponsor(client, access, user, channel, True, access >= Access.LEVELS['ADMIN'])
            if spons == 1:
                return client.notice(user[0], 'Error - channel not in use') if access >= Access.LEVELS['ADMIN'] else None  # this channel is not being used.
            if spons[0] == 2:
                return client.notice(user[0], 'You need to be authenticated first. Use \'/notice ' + client.profile.nick + ' auth\'' +
                                     ' or simply send \'.\' into the chat. I will message you that you have been authenticated. Then try again.')
            if spons[0] == 0:
                chan = spons[1]
                if chan == 1:
                    return client.notice(user[0], ':o')

                if len(args) == 1:  # Lets return the allowlist itself
                    return client.notice(user[0], '[' + chan[1] + '/' + chan[3] + ' Allowlist] ' + chan[6])
                if len(args) == 3:
                    if args[2] == spons[1][2]:
                        return client.notice(user[0], 'You cannot add or remove the channel sponsor from the allowlist. If you would like this channel to no longer be used for OSRS stat streaming, contact dj.')
                    if args[1] == 'add':  # Lets add someone to the allowlist
                        return client.notice(user[0], self.addUserAllowlist(client, chan, args[2]))
                    if args[1] == 'del':
                        return client.notice(user[0], self.delUserAllowlist(client, chan, args[2]))
                return client.notice(user[0], 'Syntax: !allowlist [add/del] [nick]  (use no parameters to view the allowlist)')

        # Admin Commands beyond this line
        if access < Access.LEVELS['ADMIN']:
            return

        if args[0] == '!help':
            return client.notice(user[0], '[OSRS Admin] !check - !rsadd - !rsdel - !rslist')

        # Used to check if there is a stored connection for specified usernames and nicks
        if args[0] == '!check':
            if len(args) == 1:
                client.notice(user[0], '!check - Use this command to check if an IRC nick or RuneScape account is linked with the other.')
                return client.notice(user[0], 'Syntax: !check <rs> <rsaccount>   or  !check irc <nick>')
            accountname = message[message.lower().index(args[2]):]
            if args[1] == 'rs':
                links = self.existingLink(client, accountname)
                if not links:
                    return client.notice(user[0], 'The RuneScape username \'' + accountname + '\' is not linked to any IRC nicks.')
                return client.notice(user[0], 'The RuneScape username \'' + accountname + '\' is linked to \'' + links[0] + '\' on IRC.')
            elif args[1] == 'irc':
                links = self.getLinkedAccounts(client, accountname)
                if not links:
                    return client.notice(user[0], 'The IRC user \'' + accountname + '\' is not linked to any RuneScape accounts.')
                return client.notice(user[0], 'The IRC user \'' + accountname + '\' is linked to \'' + ','.join(links) + '\' on RuneScape.')
            else:
                return client.notice(user[0], 'Syntax: !check <rs> <rsaccount>   or   !check irc <nick>')

        # Command used by Bot Admins to add channels to broadcast to
        #
        # Syntax: !rsadd <channel> <sponsor> <level>
        #
        # Channel: the irc channel being added
        # Sponsor: this is a nick (preferably an op in the channel) granting us permission
        # level: 0 is normal. 1 is home channel mode. this will auto voice users upon joining.
        # public: 0 is public, 1 is private (need to add users to the allowlist, sponsor added automatically)
        if args[0] == '!rsadd':
            if len(args) == 5:  # 1: channel  2: sponsor  3: homechan 4: public
                c = args[1]  # channel
                s = args[2]  # sponsor
                l = PRIVATE if args[3] == 'y' else PUBLIC
                p = args[4] == 'y'  # public=0, private=1
                wl = s
                # We dont allow duplicates
                if not self.getChannel(client, c):
                    if self.addChannel(client, c, s, l, wl, p):
                        self.syncChannels(client)
                        client.join(c)
                        return client.msg(channel, user[0] + ': The channel ' + c + ' on ' + client.profile.network.name + ' has been added (Sponsor: ' + s + ').' +
                                          (' This channel is a home channel. It will auto voice registered users upon joining. It is recommended to set channel mode +m' if l > 0 else ''))

                    return client.notice(user[0], 'Syntax: ' + args[0] + ' <#channel> <sponsor(nick)> <homechannel(y/n)> <public(y/n)>')
                return client.notice(user[0], 'That channel is already added. Remove it first (!rsdel), and try again.')
            return client.notice(user[0], 'Syntax: ' + args[0] + ' <#channel> <sponsor(nick)> <homechannel(y/n)> <public(y/n)>')
            #return client.notice(user[0], args[0] + ' help: channel -> channel to broadcast in. sponsor -> channel operator. level -> 0(normal channel), 1(home channel). public -> 0(public mode), 1(private mode, uses allowlist)')

        # Command used by Bot Admins to remove channels we are broadcasting to
        #
        # Syntax: !rsdel <channel> <confirm>
        if args[0] == '!rsdel':
            if len(args) == 3:
                chan = self.getChannel(client, args[1])
                if not chan:
                    return client.notice(user[0], 'That channel is not found.')
                if args[2] == 'confirm':
                    if self.remChannel(client, args[1]):
                        self.syncChannels(client)
                        return client.msg(channel, user[0] + ': The channel ' + args[1] + ' has been removed successfully.')
                    return client.notice(user[0], 'There was an error with your command.1')
            return client.notice(user[0], 'Syntax: ' + args[0] + ' <channel> confirm')

        # Command used to list off all channels we are connected with.
        if args[0] == '!rslist':
            chans = self.getChannelsDB(client)
            if not chans:
                return client.notice(user[0], 'There are no channels found.')
            msg = '\00303Channels (sponsor/level/public): '
            i = 0
            for c in chans:
                if i > 0:
                    msg += '\003, '
                msg += '\00304' + c[3] + ' \00306(' + c[2] + '/' + ('home' if c[4] == PRIVATE else 'guest') + '/' + ('public' if c[5] == PUBLIC else 'private') + ')'
                i += 1
            return client.notice(user[0], msg)

    # We will auto voice registered users to help avoid abuse
    def join(self, client, user, location):
        if self.isHomeChannel(client, location, True):
            self.joinBuff.append([user[0], location])
            client.whois(user[0])

    # AutoVoice users in our channels ..
    def identify(self, client, nick):
        if len(self.joinBuff) == 0:
            return
        i = 0
        for x in self.joinBuff:
            if nick == self.joinBuff[i][0]:
                if self.isHomeChannel(client, self.joinBuff[i][1], True):
                    client.mode(self.joinBuff[i][1], '+v ' + self.joinBuff[i][0])
                del self.joinBuff[i]
                return
            i += 1

    def buildStatMsg(self, rsaccount):
        stats = self.osrsTimer.getLocalStats(rsaccount)  # use a local stored database
        if stats is None:  # this will fix the accounts not being tracked by us
            stats = self.getStats(rsaccount)
        if stats is None:  # this account simply does not exist
            return 'That user was not found on the OSRS Hiscores.'
        msg = '\0034[' + rsaccount + ']\003'
        skills = 0
        for s in stats:
            if 24 <= skills < ALLCLUES:
                skills += 1
                continue
            if not s[1] == -1:
                msg += ' ' + STATS[skills][1] + ' ' + str(s[1])
            if skills == ALLCLUES:
                break
            skills += 1
        return msg

    # Fetch the OSRS HiScore page
    # Format: 0-HiScoreRank, 1-Level, 2-Experience
    def getStats(self, rsaccount):
        rsaccount = rsaccount.lower()
        try:
            response = requests.get('https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player=' + rsaccount.replace(' ', '%A0'))
            raw = str(response.content)[2:].split('\\n')
            self.engine.log.write('getStats - ' + rsaccount + ' - ' + str(raw), False)  # silent debug this
            res = []
            i = 0
            for x in raw:
                y = x.split(',')
                z = []
                for a in y:
                    if a == "'":
                        return res
                    z.append(int(a))
                res.append(z)
                i += 1
            return res
        except:
            return None

    # Authenticate users that are channel sponsors to give them rights
    # 0-Yes & Authed, 1-False, 2-Yes But Needs Authed
    def isSponsor(self, client, access, user, channel, returnChannel=False, override=False):
        chan = self.getChannel(client, channel)
        print(chan)
        if chan:  # we have channels
            print(chan)
            if chan[1] == client.profile.network.name and chan[3] == channel:
                if override or user[0] == chan[2]:  # ensure this user is the sponsor
                    res = 0 if access > 0 else 2
                    return [res, chan if returnChannel else None]
        return 1

    def isHomeChannel(self, client, channel, homeChan=False):
        channel = channel.lower()
        for c in self.getChannels(client, True, homeChan):
            if c[1] == client.profile.network.name and c[3] == channel:
                return c[4] == PRIVATE
        return False

    def getChannelsDB(self, client):
        if not client:
            cur = self.sql('SELECT * FROM ' + RSC)
        else:
            cur = self.sql('SELECT * FROM ' + RSC + ' WHERE network=?', [client.profile.network.name])
        try:
            db = cur.fetchall()
        except:
            db = None
        cur.close()
        return db

    def getChannels(self, client, public=True, homeChan=False, onlyName=False):
        chans = self.getChannelsDB(client)
        chns = []
        for c in chans:
            if public and c[5] == PRIVATE:
                continue  # public channel request, and result is private
            if homeChan and c[4] == PUBLIC:
                continue  # home channel request, and result is guest
            if onlyName:
                chns.append(c[3])  # channel only
            else:
                chns.append(c)  # id, network, sponsornick, channel, controlled, public, allowlist
        return chns

    def getChannel(self, client, channel):
        channel = channel.lower()
        chans = self.getChannelsDB(client)
        if not chans:
            return None
        for c in chans:
            if c[3] == channel:
                return c
        return None

    # We will be adding a channel into the database that is allowing us to broadcast
    def addChannel(self, client, channel, sponsor, level, allowlist=None, public=True):
        cur = self.sql('INSERT INTO  ' + RSC + ' (network, sponsornick, channel, controlled, public, allowlist_nicks) VALUES (?, ?, ?, ?, ?, ?);',
                       [client.profile.network.name, sponsor.lower(), channel.lower(), level, PUBLIC if public else PRIVATE, allowlist])
        self.db.commit()
        return True

    def syncChannels(self, client):
        self.channels = self.getChannelsDB(client)

    def remChannel(self, client, channel):
        cur = self.sql('DELETE FROM ' + RSC + ' WHERE network=? AND channel=?', [client.profile.network.name, channel.lower()])
        self.db.commit()
        cur.close()
        return True

    def addUserAllowlist(self, client, channel, addition):
        if addition in channel[6]:
            return 'That nick is already on the allowlist for ' + client.profile.network.name + '/' + channel[3]
        wl = str(channel[6]).split(',')
        wl.append(addition)
        wl = ','.join(wl)
        return self.updateChannelAllowlist(client, channel, wl, addition)

    def delUserAllowlist(self, client, channel, removal):
        if removal not in channel[6]:
            return 'That nick is not on the allowlist for ' + client.profile.network.name + '/' + channel[3]
        wl = str(channel[6]).split(',')
        i = 0
        d = []
        for x in wl:
            if x == removal:
                d.append(i)
            i += 1

        i = 0
        for x in d:
            del wl[x - i]
            i += 1

        wl = ','.join(wl)
        return self.updateChannelAllowlist(client, channel, wl, removal, False)

    def updateChannelAllowlist(self, client, channel, allowlist, nick, add=True):
        cur = self.db.cursor()
        cur.execute('UPDATE ' + RSC + ' SET allowlist_nicks = ? WHERE id = ?', [allowlist, channel[0]])
        self.db.commit()
        cur.close()
        return 'Successfully ' + ('added ' + nick + ' to ' if add else 'removed ' + nick + ' from ') + client.profile.network.name + '/' + channel[3] + ' allowlist.'

    # Check if a Rs Account is already linked to a nick
    def existingLink(self, client, rsaccount):
        cur = self.sql('SELECT nick FROM ' + RSL + ' WHERE network=? AND rsaccount=?',
                       [client.profile.network.name, rsaccount.lower()])
        try:
            account = cur.fetchone()[0]
        except:
            account = None
        cur.close()
        return account

    # Link a RS Account to a nick@network
    def linkRsAccount(self, client, nick, rsaccount, public=True, chans=None):
        nick = nick.lower()
        cur = self.sql('INSERT INTO  ' + RSL + ' (rsaccount, network, nick, channels, public) VALUES (?, ?, ?, ?, ?);',
                       [rsaccount.lower(), client.profile.network.name, nick, chans, PUBLIC if public else PRIVATE])
        self.db.commit()
        cur.close()
        return True

    def unlinkRsAccount(self, client, nick, rsn):
        nick = nick.lower()
        cur = self.sql('DELETE FROM ' + RSL + ' WHERE nick=? AND network=? AND rsaccount=?', [nick, client.profile.network.name, rsn])
        self.db.commit()
        cur.close()
        return True

    # grab the linked Rs Accounts linked to a nick@network
    def getLinkedAccounts(self, client, nick):
        nick = nick.lower()
        links = []
        cur = self.sql('SELECT rsaccount FROM ' + RSL + ' WHERE network=? AND nick=?',
                       [client.profile.network.name, nick])

        try:
            for e in cur.fetchall():
                # print(list(e)[0])
                links.append(list(e)[0])
        except:
            links = None
        cur.close()
        return links

    def getAllAccounts(self):
        accounts = []
        cur = self.sql('SELECT * FROM ' + RSL)
        try:
            for e in cur.fetchall():
                accounts.append(e)
        except:
            print('error')
            return
        cur.close()
        return accounts

    def sql(self, statement, options=None):
        cur = self.db.cursor()
        if options is None:
            cur.execute(statement)
        else:
            cur.execute(statement, options)
        return cur


PUBLIC = 0
PRIVATE = 1

STATS = [
    ['Total Level', 'Total'],  # 0
    ['Attack', '⚔️︎'],  # 1
    ['Defence', '🛡️'],  # 2
    ['Strength', '💪'],  # 3
    ['Hitpoints', '♥️'],  # 4
    ['Ranged', '🏹'],  # 5
    ['Prayer', '✝️'],  # 6
    ['Magic', '🧙'],  # 7
    ['Cooking', '🥧'],  # 8
    ['Woodcutting', '🪓'],  # 9
    ['Fletching', '🔁'],  # 10
    ['Fishing', '🎣'],  # 11
    ['Firemaking', '🔥'],  # 12
    ['Crafting', '🛠️'],  # 13
    ['Smithing', '️🔨'],  # 14
    ['Mining', '⛏️'],  # 15
    ['Herblore', '🌿'],  # 16
    ['Agility', '🏃'],  # 17
    ['Thieving', '💰'],  # 18
    ['Slayer', '💀️'],  # 19
    ['Farming', '🌾'],  # 20
    ['Runecrafting', '🧿'],  # 21
    ['Hunter', '🐾'],  # 22
    ['Construction', '🏠'],  # 23
    ['24', ''],  # 24 SAILING ??
    ['25', ''],  # 25
    ['26', ''],  # 26
    ['27', ''],  # 27
    ['28', ''],  # 28
    ['28', ''],  # 29
    ['All Clue Scrolls', '📜'],  # 30  (ALLCLUES)
    ['Beginner Clue Scrolls', 'beginner'],  # 30+1 ..
    ['Easy Clue Scrolls', 'easy'],  # 31
    ['Medium Clue Scrolls', 'med'],  # 32
    ['Hard Clue Scrolls', 'hard'],  # 33
    ['Elite Clue Scrolls', 'elite'],  # 34
    ['Master Clue Scrolls', 'master'],  # 35
    ['LMS - Rank', 'lms'],  # 36
    ['38', ''],  # 37
    ['Soul Wars Zeal', 'swz'],  # 38
    ['Rifts closed', 'rc'],  # 39
    ['Abyssal Sire', 'as'],  # 40
    ['Alchemical Hydra', 'ah'],  # 41
    ['42', ''],  # 42
    ['Barrows Chests', 'barrows'],  # 43
    ['Bryophyta', ''],  # 44
    ['Callisto', ''],  # 45
    ['46', 'Wc'],  # 46
    ['Cerberus', ''],  # 47
    ['Chambers of Xeric', ''],  # 48
    ['Chambers of Xeric: Challenge Mode', ''],  # 49
    ['50', ''],  # 50
    ['51', ''],  # 51
    ['52', ''],  # 52
    ['Corporeal Beast', ''],  # 53
    ['54', ''],  # 54
    ['Dagannoth Prime', ''],  # 55
    ['Dagannoth Rex', ''],  # 56
    ['Dagannoth Supreme', ''],  # 57
    ['Deranged Archaeologist', ''],  # 58
    ['59', ''],  # 59
    ['General Graador', ''],  # 60
    ['Giant Mole', ''],  # 61
    ['Grotesque Guardians', ''],  # 62
    ['Hespori', ''],  # 63
    ['Kalphite Queen', ''],  # 64
    ['65', ''],  # 65
    ['Kraken', ''],  # 66
    ['67', ''],  # 67
    ['K\'ril Tsutaroth', ''],  # 68
    ['Mimic', ''],  # 69
    ['Nex', ''],  # 70
    ['Nightmare', ''],  # 71
    ['Phosani\'s Nightmare', ''],  # 72
    ['73', ''],  # 73
    ['74', ''],  # 74
    ['Sarachnis', ''],  # 75
    ['Scorpia', ''],  # 76
    ['Skotizo', ''],  # 77
    ['78', ''],  # 78
    ['79', ''],  # 79
    ['The Guantlet', ''],  # 80
    ['The Corrupted Guantlet', ''],  # 81
    ['82', ''],  # 82
    ['83', ''],  # 83
    ['Theatre of Blood', ''],  # 84
    ['Theatre of Blood: Hard Mode', ''],  # 85
    ['Thermonuclear Smoke Devil', ''],  # 86
    ['Tombs of Amascut', ''],  # 87
    ['Tombs of Amascut: Expert Mode', ''],  # 88
    ['TzKal-Zuk', ''],  # 89
    ['TzTok-Jad', ''],  # 90
    ['Vardorvis', ''],  # 91
    ['92', ''],  # 92
    ['93', ''],  # 93
    ['Vorkath', ''],  # 94
    ['Wintertodt', ''],  # 95
    ['Zalcano', ''],  # 96
    ['Zulrah', ''],  # 97
    ['98', ''],  # 98
]

