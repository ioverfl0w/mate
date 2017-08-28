from lib import Engine
from random import choice
from random import randint
import sqlite3

# the table in our sqlite3 database
table = 'MarkSpeak'
# max words to have in a single sentence
max_words = 15
# minimum word count for a single sentence
min_words = 6

class MarkSpeak:

    # MarkSpeak
    #
    # Markov Chain string builder. Uses a database of lines from a plaintext source file.
    # TODO - record new words from active chat

    def __init__(self):
        self.module = Engine.Module('MarkSpeak', 'PRIVMSG')
        # our database
        self.database = sqlite3.connect('./data/mark.db')

    def message(self, client, user, channel, message):
        if not channel.startswith('#'):
            return

        args = message.split(' ')

        if args[0].lower() == '.talk':
            if len(args) > 2 and args[1].lower() == 'about':
                about = message[message.index(args[2]):]
                client.msg(channel, self.buildString(about))

    def buildString(self, about):
        results = []

        for i in range(min_words, max_words):
            possible = self.getWords(about if len(results) < 1 else results[len(results) - 1])
            if len(possible) == 0:
                continue
            results.append(choice(possible)[1])
        return ' '.join(results)

    def getWords(self, root):
        cur = self.database.cursor()

        # Get our list of words for post word selection (root: the, ex: the thing)
        cur.execute('SELECT * FROM ' + table + ' WHERE word=? ORDER BY count', [root])
        return cur.fetchall()
