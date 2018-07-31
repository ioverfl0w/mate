from lib import Engine
from random import choice
from random import randint
import sqlite3
import time

# the table in our sqlite3 database
table = 'MarkSpeak'
# max words to have in a single sentence
max_words = 15
# minimum word count for a single sentence
min_words = 6
# Words that cannot end a sentence
CONT_WORDS = ['the', 'of', 'and', 'or', 'but', 'for']
# Hilight response delay (in seconds)
RESPONSE_DELAY = 3

class MarkSpeak:

    # MarkSpeak
    #
    # Markov Chain string builder. Uses a database of lines from a plaintext source file.
    # TODO - record new words from active chat
    # TODO - make this less shit, its awful. and I hate looking at it

    def __init__(self, clients=None):
        self.module = Engine.Module('MarkSpeak', 'PRIVMSG', clients=clients)
        # our database
        self.database = sqlite3.connect('./data/mark-3.db')
        #last hilight response
        self.last_hilight = 0

    def message(self, client, user, channel, message):
        if not channel.startswith('#'):
            return

        args = message.split(' ')

        #if args [0].lower() == client.profile.nick.lower() and time.time() > self.last_hilight + RESPONSE_DELAY * 1000:


        if args[0].lower() == '.talk':
            if len(args) > 2 and args[1].lower() == 'about':
                about = message[message.index(args[2]):].split(' ')
                if len(about) > 1:
                    r = []
                    for i in range(0, len(about) - 1):
                        r.append(self.buildString(about[i]))
                    return client.msg(channel, user[0] + ': ' + choice(r))

                # Single word for context, build a sentence with it
                return client.msg(channel, user[0] + ': ' + self.buildString(about[0]))
            # No context to work with, build random sentence
            return client.msg(channel, user[0] + ': ' + self.buildString(self.getRandomWord()))

    def buildString(self, about):
        results = []
        size = 0

        for i in range(min_words, max_words):
            results = self.continuePhrase(about, results)
            if size == len(results): # no new additions
                break
            size = len(results)

        # Prevent phrases from ending in continuation words
        while True:
            if results[len(results) - 1].lower() in CONT_WORDS:
                results = self.continuePhrase(about, results)
            break

        #results.insert(0, about)
        return ' '.join(results)

    def continuePhrase(self, about, phrase):
        possible = self.getWords(about if len(phrase) < 1 else phrase[len(phrase) - 1])
        print(possible)
        if not len(possible) == 0:
            for word in choice(possible)[0].split(' '):
                phrase.append(word)
        print(phrase)
        return phrase

    # Fetch a random root word for us to build around
    def getRandomWord(self):
        cur = self.database.cursor()
        cur.execute('SELECT word FROM ' + table)
        return choice(cur.fetchall())[0]

    def getWords(self, root):
        cur = self.database.cursor()

        # Get our list of words for post word selection (root: the, ex: the thing)
        cur.execute('SELECT nextword FROM ' + table + ' WHERE word=? GROUP BY count ORDER BY count DESC', [root])
        return cur.fetchall()
