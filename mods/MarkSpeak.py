from lib import Engine
from random import choice
from random import randint
import sqlite3

# the table in our sqlite3 database
table = 'MarkSpeak'
# max words to have in a single sentence
max_words = 21
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
                about = message[message.index(args[2]):].split(' ')
                if len(about) > 1:
                    r = []
                    for i in range(0, len(about) - 1):
                        r.append(self.buildString(about[i]))
                    return client.msg(channel, choice(r))

                # Single word for context, build a sentence with it
                return client.msg(channel, self.buildString(about[0]))
            # No context to work with, build random sentence
            return client.msg(channel, self.buildString(self.getRandomWord()))

    def buildString(self, about):
        results = []

        for i in range(min_words, max_words):
            possible = self.getWords(about if len(results) < 1 else results[len(results) - 1])
            #print(possible)
            if len(possible) == 0:
                break
            for word in choice(possible)[0].split(' '):
                results.append(word)

        results.insert(0, about)
        return ' '.join(results)

    # Fetch a random root word for us to build around
    def getRandomWord(self):
        cur = self.database.cursor()
        cur.execute('SELECT word FROM ' + table)
        return choice(cur.fetchall())[0]

    def getWords(self, root):
        cur = self.database.cursor()

        # Get our list of words for post word selection (root: the, ex: the thing)
        cur.execute('SELECT nextword, count FROM ' + table + ' WHERE word=? ORDER BY count DESC', [root])
        return cur.fetchall()
