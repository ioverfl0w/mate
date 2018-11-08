from lib import Engine
import datetime
import json
import requests
import sqlite3
import time
import traceback

# Rate that the Lotto will check for next drawings (in minutes)
REFRESH_RATE = 30
# Lotto time is off, customize for your timezone
TIME_OFFSET = 1
# Expiration time in days for bets (+ 1 day)
EXPIRATION = 4

class Lotto:

    # LottoMod
    #
    # Track multiple lotto picks per user against the MegaMillions and Powerball
    # Attach to a Timer that will check the winning numbers upon drawing

    def __init__(self):
        self.module = Engine.Module('Lotto', 'PRIVMSG')

        # Connect to our database
        self.db = sqlite3.connect('./data/lotto.db')
        self.lastCheck = 0 #Last time the draw was checked
        self.databaseCheck()
        self.draws = self.getDraws()

    # Will make sure the database has the necessary tables, as well as Check
    # for the next drawing.
    def databaseCheck(self):
        # usersettings
        # table containing options the user sets, such as publicly announcing when someone has won
        # or have their picks be searchable by other users
        self.db.execute('''
        create table if not exists 'usersettings' (
            nick text UNIQUE,
            network text,
            announce integer default 0,
            public integer default 0
        );''')
        # picks
        # picks for all lottos
        self.db.execute('''
        create table if not exists 'picks' (
            id integer primary key,
            dateplaced text,
            nums text,
            nick text,
            network text
        );''')

    # Use this to fetch the next drawing dates. Will only pull from website based on REFRESH_RATE
    # to prevent abuse of the lotto websites.
    def getDraws(self):
        self.update()
        return self.draws

    # Update all of our stored information and database
    def update(self):
        if time.time() > (REFRESH_RATE * 60) + self.lastCheck:
            self.lastCheck = time.time()
            print('check performed')
            self.draws = {
                'pb': {
                    'next': self.get_powerball_nextdrawing(),
                    'nums': self.get_powerball_numbers()
                },
                'mm': {
                    'next': self.get_megamillion_nextdrawing(),
                    'nums': self.get_megamillion_numbers()
                }
            }

    # client - the client that is processing the event
    # user - [0] nick , [1] user , [3] host
    # channel - either a channel or the client's nick
    # message - the content of the message
    def message(self, client, user, channel, message):
        args = message.lower().split(' ')
        if args[0] == '!help':
            return client.notice(user[0], '[Lotto Help] !nums (pb|mm) - !next (pb|mm) - !pick # # # # # # - !check (id)')

        if args[0] == '!nums':
            if len(args) == 1: # Just display the winning numbers
                self.sendResults(client, channel, user[0], 'mm') # MegaMillions
                return self.sendResults(client, channel, user[0], 'pb') # Powerball
            return sendResults(client, channel, user[0], args[1])

        if args[0] == '!next':
            if len(args) == 1:
                self.sendNext(client, channel, user[0], 'mm') # MegaMillions
                return self.sendNext(client, channel, user[0], 'pb') # Powerball
            return self.sendNext(client, channel, user[0], args[1])

        if args[0] == '!check':
            if len(args) == 1:
                return client.notice(user[0], 'Syntax: !check (pb|mm) (id)')
            try:
                try:
                    id = int(id)
                except:
                    return client.notice(user[0], 'Unable to use the Id specified')

                picks = self.getTickets(client, user[0])
                if len(picks) == 0:
                    return client.notice(user[0], 'No tickets. Use !pick help')

                # TODO -- better limit the responses, better management system for

                # TODO -- user the user settings to either announce publicly or use a notice
                return client.msg(channel, user[0] + ': ' + self.checkTicket(self.getTicket(id), args[1]))

            except:
                print(traceback.format_exc())
                return client.notice(user[0], 'Error while checking')

        if args[0] == '!pick':
            # Show our picks
            if len(args) == 1:
                picks = self.getTickets(client, user[0])
                if len(picks) == 0:
                    return client.notice(user[0], 'No tickets. Use !pick help')
                client.notice(user[0], 'Total tickets: ' + str(len(picks)) + ' -- use !check (id)')
                return client.notice(user[0], 'All bets expire after ' + str(EXPIRATION) + ' days.')

            # Submit a pick
            try:
                nums = []
                for i in range(1,7): # picks should be 6 numbers
                    nums.append(int(args[i]))

                self.submitPick(client, user[0], nums)
                id = self.getLastTicket(client, user[0])[0]

                return client.notice(user[0], 'Your ticket has been submitted. You can check it with !check ' + str(id))

            except Exception:
                print(traceback.format_exc())
                return client.notice(user[0], 'Syntax: !pick # # # # # #')

    def checkTicket(self, ticket, lotto):
        pass

    def getTicket(self, client, nick, id):
        tickets = self.getTickets(client, nick)
        for t in ticket:
            if t[0] == id:
                return t
        return None

    def getTickets(self, client, nick):
        cur = self.db.cursor()
        cur.execute('SELECT * FROM picks WHERE network=? AND nick=? BY id DESC', [client.profile.network.name, nick])
        return cur.fetchall()

    def getLastTicket(self, client, nick):
        tickets = self.getTickets(client, nick)
        return tickets[len(tickets) - 1] if len(tickets) > 0 else None

    def sendNext(self, client, dest, recip, lotto):
        try:
            next = self.getDraws()[lotto]['next']
            #print(next)
            client.msg(dest, recip + ': Next ' + next['name'] + ' drawing is ' + next['drawdate'] + '. Jackpot: ' + ('$' if type(next['prize']) == int else '') + str(next['prize']))
        except:
            client.msg(dest, 'Invalid lotto name')
            print(traceback.format_exc())

    def sendResults(self, client, dest, recip, lotto):
        try:
            r = self.getDraws()[lotto]['nums']
            #print(next)
            client.msg(dest, recip + ': ' + r['lotto'] + ' Results (' + r['date'] + ') ' + '-'.join(map(str, r['nums'])) + ' ' + r['pb_code'] + ': ' + str(r['pb']) + ' x' + str(r['multiplier']))
        except:
            client.msg(dest, 'Invalid lotto name')
            print(traceback.format_exc())

    def submitPick(self, client, nick, nums):
        cur = self.db.cursor()
        cur.execute('INSERT OR IGNORE INTO picks (dateplaced, nums, nick, network) ' + \
            'VALUES (?,?,?,?)', [datetime.date.today(), json.dumps(nums), nick, client.profile.network.name])
        self.db.commit()
        cur.close()

    # Fetch and return the winning numbers (5 nums). the powerball (1 num), and the multiplier
    def get_powerball_numbers(self):
        req = requests.get(LOTTO['powerball']['win'])
        res = req.json()[0]
        nums = res['field_winning_numbers'].split(',')
        powerball = nums[5]
        del nums[5] # This is the powerball
        return {
                'lotto': 'PowerBall',
                'pb_code': 'PB',
                'nums': map(int, nums),
                'pb': int(powerball),
                'multiplier': int(res['field_multiplier']),
                'date': res['field_draw_date']
            }

    # Fetch mega million numbers. Need to sort the numbers lowest -> highest
    def get_megamillion_numbers(self):
        request = requests.get(LOTTO['megamillions']['win'])
        res = request.json()['numbersList'][0]
        nums = []
        for i in range(1, 6):
            nums.append(res['WhiteBall' + str(i)])
        nums.sort(key=int)
        return {
                'lotto': 'MegaMillions',
                'pb_code': 'MB',
                'nums': nums,
                'pb': res['MegaBall'],
                'multiplier': res['Megaplier'],
                'date': res['DrawDate'][:res['DrawDate'].index('T')]}

    # Powerball Functions (website related)
    def get_powerball_nextdrawing(self):
        req = requests.get(LOTTO['powerball']['next'])
        res = req.json()[0]
        date = datetime.datetime.strptime(res['field_next_draw_date'][:res['field_next_draw_date'].index('T')], '%Y-%m-%d').date()
        return {
                'name': 'PowerBall',
                'drawdate': str(date - datetime.timedelta(days=TIME_OFFSET)),
                'prize': res['field_prize_amount'],
                'cash': res['field_prize_amount_cash']
            }

    # MegaMillion Functions (website related)
    def get_megamillion_nextdrawing(self):
        request = requests.get(LOTTO['megamillions']['next'])
        res = request.json()['nextDraw']
        date = datetime.datetime.strptime(res['NextDrawDate'][:res['NextDrawDate'].index('T')], '%Y-%m-%d').date()
        return {
                'name': 'MegaMillions',
                'drawdate': str(date - datetime.timedelta(days=TIME_OFFSET)),
                'prize': res['NextJackpotAnnuityAmount'],
                'cash': res['NextJackpotCashAmount']
            }


# Static variables for each lotto, may change over time
LOTTO = {
    'powerball': {
        'win': 'https://www.powerball.com/api/v1/numbers/powerball/recent?_format=json',
        'next': 'https://www.powerball.com/api/v1/estimates/powerball?_format=json',
        'winners': [
            {
                'name': 'Powerball match',
                'base_prize': 4,
                'pb_match': True,
                'num_match': 0
            },
            {
                'name': 'Powerball+1 match',
                'base_prize': 4,
                'pb_match': True,
                'num_match': 1
            },
            {
                'name': 'Powerball+2 match',
                'base_prize': 7,
                'pb_match': True,
                'num_match': 2
            },
            {
                'name': '3 number match',
                'base_prize': 7,
                'pb_match': False,
                'num_match': 3
            },
            {
                'name': 'Powerball+3 match',
                'base_prize': 100,
                'pb_match': True,
                'num_match': 3
            },
            {
                'name': '4 number match',
                'base_prize': 100,
                'pb_match': False,
                'num_match': 4
            },
            {
                'name': 'Powerball+4 match',
                'base_prize': 50000,
                'pb_match': True,
                'num_match': 4
            },
            {
                'name': '5 number match',
                'base_prize': 1000000,
                'pb_match': False,
                'num_match': 5
            },
            {
                'name': 'Jackpot',
                'base_prize': -1, #No value, variable
                'pb_match': True,
                'num_match': 5
            }
        ] # end winners
    },
    'megamillions': {
        'win': 'http://www.megamillions.com/Media/Static/winning-numbers/winning-numbers.json?rt=123456a',
        'next': 'http://www.megamillions.com/Media/Static/winning-numbers/winning-numbers.json?rt=987654b',
        'winners': [
            {
                'name': 'Megaball match',
                'base_prize': 2,
                'pb_match': True,
                'num_match': 0
            },
            {
                'name': 'Megaball+1 match',
                'base_prize': 4,
                'pb_match': True,
                'num_match': 1
            },
            {
                'name': 'Megaball+2 match',
                'base_prize': 10,
                'pb_match': True,
                'num_match': 2
            },
            {
                'name': '3 number match',
                'base_prize': 10,
                'pb_match': False,
                'num_match': 3
            },
            {
                'name': 'Megaball+3 match',
                'base_prize': 200,
                'pb_match': True,
                'num_match': 3
            },
            {
                'name': '4 number match',
                'base_prize': 500,
                'pb_match': False,
                'num_match': 4
            },
            {
                'name': 'Megaball+4 match',
                'base_prize': 10000,
                'pb_match': True,
                'num_match': 4
            },
            {
                'name': 'Match 5',
                'base_prize': 1000000,
                'pb_match': False,
                'num_match': 5
            },
            {
                'name': 'Jackpot',
                'base_prize': -1, #No value, variable
                'pb_match': True,
                'num_match': 5
            }
        ] # end winners
    }
}
