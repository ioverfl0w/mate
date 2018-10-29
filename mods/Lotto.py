from lib import Engine
import requests
import sqlite3

DIR = './data/'
TABLE = 'Lotto'

LOTTO = {
    'powerball': {
        'win': 'https://www.powerball.com/api/v1/numbers/powerball/recent?_format=json',
        'next': 'https://www.powerball.com/api/v1/estimates/powerball?_format=json'
    },
    'megamillions': {
        'win': 'http://www.megamillions.com/Media/Static/winning-numbers/winning-numbers.json?rt=123456a',
        'next': 'https://www.powerball.com/api/v1/estimates/powerball?_format=json'
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
        # Create database if does not exist
        self.db.execute('''
        create table if not exists ''' + TABLE + ''' (
            lotto text,
            nick text UNIQUE,
            picks text,
            winnums text,
            draw_date text
        );''')

    # client - the client that is processing the event
    # user - [0] nick , [1] user , [3] host
    # channel - either a channel or the client's nick
    # message - the content of the message
    def message(self, client, user, channel, message):
        args = message.lower().split(' ')
        if args[0] == '!help':
            return client.notice(user[0], '[Lotto Help] !lotto (pb|mm) - !bet (pb|mm) # # # # # #')

        if args[0] == '!lotto':
            if len(args) == 1: # Just display the winning numbers
                self.sendResults(client, channel, user[0], 'mm') # MegaMillions
                return self.sendResults(client, channel, user[0], 'pb') # Powerball
            if args[1] == 'pb' or args[1] == 'powerball':
                return sendResults(client, channel, user[0], 'pb')
            elif args[1] == 'mm' or args[1] == 'megamillions':
                    return sendResults(client, channel, user[0], 'mm')

        if args[0] == '!bet':
            if len(args) < 8:
                client.notice(user[0], 'Syntax: !bet powerball(pb)|megamillions(mm) # # # # # #')
                return client.notice(user[0], 'pb or mm is all that is necessary.')

    def sendResults(self, client, dest, recip, lotto):
        r = None
        if lotto == 'mm':
            r = self.get_megamillion_numbers()
        elif lotto == 'pb':
            r = self.get_powerball_numbers()
        else:
            return client.msg(dest, 'Invalid lotto type in sendResults()')

        client.msg(dest, recip + ': ' + r['lotto'] + ' Results (' + r['date'] + ') ' + '-'.join(map(str, r['nums'])) + ' ' + r['pb_code'] + ': ' + str(r['pb']) + ' x' + str(r['multiplier']))

    # Fetch mega million numbers. Need to sort the numbers lowest -> highest
    def get_megamillion_numbers(self):
        # http://www.megamillions.com/Media/Static/winning-numbers/winning-numbers.json
        request = requests.get(LOTTO['megamillions']['win'])
        res = request.json()['numbersList'][0]
        nums = []
        print(res)
        for i in range(1, 6):
            nums.append(res['WhiteBall' + str(i)])
        nums.sort(key=int)
        return {'lotto': 'MegaMillions', 'pb_code': 'MB', 'nums': nums, 'pb': res['MegaBall'], 'multiplier': res['Megaplier'], 'date': res['DrawDate'][:res['DrawDate'].index('T')]}

    # Fetch and return the winning numbers (5 nums). the powerball (1 num), and the multiplier
    def get_powerball_numbers(self):
        # Powerball https://www.powerball.com/api/v1/numbers/powerball/recent?_format=json
        request = requests.get(LOTTO['powerball']['win'])
        res = request.json()[0]
        numbers = res['field_winning_numbers'].split(',')
        powerball = numbers[5]
        del numbers[5] # This is the powerball
        return {'lotto': 'Powerball', 'pb_code': 'PB', 'nums': map(int, numbers), 'pb': int(powerball), 'multiplier': int(res['field_multiplier']), 'date': res['field_draw_date']}
