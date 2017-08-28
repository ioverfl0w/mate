#This script is used to convert a file with plaintext to a database that can
#be used by the MarkSpeak module.
import sqlite3
import traceback

source_text = './dump.dat'

conn = sqlite3.connect('mark.db')
counter = 0

# Create the database
conn.execute('''
create table if not exists MarkSpeak (
    word text,
    nextword text,
    count integer,
    primary key(word, nextword)
);
''')

def insertwords(word, nextword):
    pair = [word, nextword]
    conn.execute('''
insert or ignore into MarkSpeak (
    word, nextword, count
)
values (
    ?, ?, 0
);''', pair)
    conn.execute('''
update MarkSpeak
set count = count + 1
where word=? and nextword=?;
''', pair)


with open(source_text) as f:
    for line in f:
        line = line.strip()
        args = line.split(' ')

        # Ignore single word messages for now
        if len(args) <= 1:
            continue

        # Ignore what appears to be a quote
        if args[0].startswith('<'):
            continue

        # Go through each word in a line, adding their attributes to our database
        for i in range(0, len(args) - 1):
            if not i + 1 >= len(args):
                insertwords(args[i], args[i + 1])
                #print(args[i] + '\t' + args[i + 1])
                counter += 1

        counter += 1
        if str(counter).endswith('000'):
            print('Combos in database: ' + str(counter))

print('Added ' + str(counter) + ' rows to database.')
conn.commit()
conn.close()
