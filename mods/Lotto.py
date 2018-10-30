from lib import Engine
import datetime
import json
import requests
import sqlite3

import traceback

DIR = './data/'

LOTTO = {
    'powerball': {
        'win': 'https://www.powerball.com/api/v1/numbers/powerball/recent?_format=json',
        'next': 'https://www.powerball.com/api/v1/estimates/powerball?_format=json'
    },
    'megamillions': {
        'win': 'http://www.megamillions.com/Media/Static/winning-numbers/winning-numbers.json?rt=123456a',
        'next': 'http://www.megamillions.com/Media/Static/winning-numbers/winning-numbers.json?rt=987654b'
    }
}

class Lotto:

    # LottoMod
    #
    # Track multiple lotto picks per user against the MegaMillions and Powerball
    # Attach to a Timer that will check the winning numbers upon drawing

    def __init__(self):
        self.module = Engine.Module('Lotto', 'PRIVMSG')

        # Connect to our database
        self.db = sqlite3.connect(DIR + 'lotto.db')
        self.databaseCheck()
        self.checkNext()

    # Will make sure the database has the necessary tables, as well as Check
    # for the next drawing.
    def databaseCheck(self):
        # draws
        # this table will contain all the pending drawing dates, and the winning numbers
        # of previously tracked drawings
        self.db.execute('''
        create table if not exists 'draws' (
            id integer primary key,
            date text,
            winnums text default NULL,
            lotto text
        );''')
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
            network text,
            drawid integer
        );''')

    # Will check the next drawings with what is in the database. This will trigger an event that Will
    # Check all pending picks
    def checkNext(self):
        pass

    # client - the client that is processing the event
    # user - [0] nick , [1] user , [3] host
    # channel - either a channel or the client's nick
    # message - the content of the message
    def message(self, client, user, channel, message):
        args = message.lower().split(' ')
        if args[0] == '!help':
            return client.notice(user[0], '[Lotto Help] !lotto (pb|mm) - !pick (pb|mm) # # # # # #')

        if args[0] == '!lotto':
            if len(args) == 1: # Just display the winning numbers
                self.sendResults(client, channel, user[0], 'mm') # MegaMillions
                return self.sendResults(client, channel, user[0], 'pb') # Powerball
            if args[1] == 'pb' or args[1] == 'powerball':
                return sendResults(client, channel, user[0], 'pb')
            elif args[1] == 'mm' or args[1] == 'megamillions':
                    return sendResults(client, channel, user[0], 'mm')

        if args[0] == '!next':
            if len(args) == 1:
                client.msg()
                self.sendResults(client, channel, user[0], 'mm') # MegaMillions
                return self.sendResults(client, channel, user[0], 'pb') # Powerball
            if args[1] == 'pb' or args[1] == 'powerball':
                return sendResults(client, channel, user[0], 'pb')
            elif args[1] == 'mm' or args[1] == 'megamillions':
                    return sendResults(client, channel, user[0], 'mm')

        if args[0] == '!pick':
            # Show our picks
            if len(args) == 1:
                picks = self.getTickets(client, user[0])
                if len(picks) == 0:
                    return client.notice(user[0], 'No tickets. Use !pick help')
                client.notice(user[0], 'Total tickets: ' + str(len(picks)))
                i = 1
                for ticket in picks:
                    client.notice(user[0], 'Ticket #' + str(i) + ' - Date Placed: ' + ticket[1] + ' - Numbers: ' + ticket[2].strip('[]'))
                return

            # Submit a pick
            try:
                name = None
                if args[1] == 'pb' or args[1]== 'powerball':
                    name = 'pb'
                elif args[1] == 'mm' or args[1]== 'megamillions':
                    name = 'mm'
                else:
                    raise ValueError('[pick] unsupported lotto provided (' + args[1] + ')')

                nums = []
                for i in range(2,8): # picks should be 6 numbers
                    nums.append(int(args[i]))

                # TODO -- get the draw id
                drawid = 0

                self.submitPick(client, user[0], nums, drawid)

            except Exception:
                print(traceback.format_exc())
                client.notice(user[0], 'Syntax: !pick powerball(pb)|megamillions(mm) # # # # # #')
                client.notice(user[0], 'pb or mm is all that is necessary for the Lotto name.')
                return client.notice(user[0], 'Just use !pick to display your tickets.')

    def getTickets(self, client, nick):
        cur = self.db.cursor()
        cur.execute('SELECT * FROM picks WHERE network=? AND nick=?', [client.profile.network.name, nick])
        return cur.fetchall()

    def sendNext(self, client, dest, recip, lotto):
        pass

    def sendResults(self, client, dest, recip, lotto):
        if lotto == 'mm':
            r = self.get_megamillion_numbers()
        elif lotto == 'pb':
            r = self.get_powerball_numbers()
        else:
            return client.msg(dest, 'Invalid lotto type in sendResults()')

        client.msg(dest, recip + ': ' + r['lotto'] + ' Results (' + r['date'] + ') ' + '-'.join(map(str, r['nums'])) + ' ' + r['pb_code'] + ': ' + str(r['pb']) + ' x' + str(r['multiplier']))

    def submitPick(self, client, nick, nums, drawid):
        cur = self.db.cursor()
        cur.execute('INSERT OR IGNORE INTO picks (dateplaced, nums, nick, network, drawid) ' + \
            'VALUES (?,?,?,?,?)', [datetime.date.today(), json.dumps(nums), nick, client.profile.network.name, drawid])
        self.db.commit()
        cur.close()

    # MegaMillion Functions (website related)
    def get_megamillion_nextdrawing(self):
        request = requests.get(LOTTO['megamillions']['next'])
        res = request.json()['nextDraw']
        return {
                'drawdate': res['NextDrawDate'][:res['NextDrawDate'].index('T')],
                'prize': res['NextJackpotAnnuityAmount'],
                'cash': res['NextJackpotCashAmount']
            }

    # Fetch mega million numbers. Need to sort the numbers lowest -> highest
    def get_megamillion_numbers(self):
        # http://www.megamillions.com/Media/Static/winning-numbers/winning-numbers.json
        request = requests.get(LOTTO['megamillions']['win'])
        res = request.json()['numbersList'][0]
        nums = []
        for i in range(1, 6):
            nums.append(res['WhiteBall' + str(i)])
        nums.sort(key=int)
        return {'lotto': 'MegaMillions', 'pb_code': 'MB', 'nums': nums, 'pb': res['MegaBall'], 'multiplier': res['Megaplier'], 'date': res['DrawDate'][:res['DrawDate'].index('T')]}

    # Powerball Functions (website related)
    def get_powerball_nextdrawing(self):
        req = requests.get(LOTTO['powerball']['next'])
        res = req.json()[0]
        return {
                'drawdate': res['field_next_draw_date'][:res['field_next_draw_date'].index('T')],
                'prize': res['field_prize_amount'],
                'cash': res['field_prize_amount_cash']
            }

    # Fetch and return the winning numbers (5 nums). the powerball (1 num), and the multiplier
    def get_powerball_numbers(self):
        # Powerball https://www.powerball.com/api/v1/numbers/powerball/recent?_format=json
        req = requests.get(LOTTO['powerball']['win'])
        res = req.json()[0]
        nums = res['field_winning_numbers'].split(',')
        powerball = nums[5]
        del nums[5] # This is the powerball
        return {'lotto': 'Powerball', 'pb_code': 'PB', 'nums': map(int, nums), 'pb': int(powerball), 'multiplier': int(res['field_multiplier']), 'date': res['field_draw_date']}
