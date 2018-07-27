import sqlite3

print('''\n\nAdd an initial admin to Mate. After adding this, authenticate with
mate by using /notice (botname) auth
You can then add new users to your access system by using !set (nick) (level)
from within IRC while authed.\n
Access user levels:
3 - OWNER
2 - ADMIN
1 - TRUSTED/MOD
0 - NORMAL USER
-1 - IGNORED\n''')

def build():
    network = input('Network name (this is case sensitive and should match what you have configured in run file):  ')
    nick = input('Nick:  ')
    level = input('Access level (number only):  ')
    table = input('Table name (leave blank unless you have changed this):  ')
    insert(network, nick, level, table)

def insert(network, nick, level, table):
    try:
        if network == '':
            print('Network name required. Check run.py for network name')
            quit()
        if nick == '':
            print('Nick required. Who are you giving access to?')
            quit()
        level = int(level)
        if table == '':
            table = 'MateAccess'
    except:
        print('Level must be a number!!!')
        quit()

    db = sqlite3.connect('./access.db')
    db.execute('''
        create table if not exists ''' + table + ''' (
            network text,
            nick text,
            level integer
        );''')

    db.execute('INSERT INTO ' + table + ' values (?, ?, ?) ', [network, nick.lower(), level])
    db.commit()
    print('Database created. Copy the new access.db file and place it into the data directory.')


    more = input('Adding more accounts? y/n\t\t')
    if more.lower() == 'y':
        build()


build()
