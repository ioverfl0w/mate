import lib.Engine
import shelve
import time

# Scrollback limit for hilight events
scrollback_limit = 5
# Database paths
scrollback_db = './data/hl-sb.db'
hilight_db = './data/hl-core.db'

class Hilight:

    # Hilight
    #
    # Maintains short message buffer for each channel, and pushes
    # Hilight events to them when they are next active.
    #
    # TODO - convert database from shelves to sql
    #
    # TODO - better track users between being checked out and being waited on
    # Right now they are all in one list in local memory, maybe splitting later
    # if ever scaled larger
    #
    # TODO - change from Paste.ee to something else that does not require an API key
    # Maybe just throttle paste it to a PM

    def __init__(self, apikey):
        self.module = lib.Engine.Module('Hilight', 'PRIVMSG')

        # List of users opted in for hilight services
        self.watch = []
        # Pending events, not yet complete
        self.events = []
        # API Key used with Paste.ee
        self.key = apikey
        # Sync with database files
        self.hlsync()

    def message(self, client, user, channel, message):
        # we need to see if this user is returning from AFK
        self.checkin(client, user)

        # append contents of messages to scrollback
        if channel.startswith('#'):
            self.storemsg(client, user, channel, message)

        # check for hilight events
        self.checkmsg(client, channel, message)

        args = message.split(' ')

        # Optin to Hilighting services
        # Syntax: !optin [duration in mins] confirm
        # Example: !optin 15 confirm
        if args[0].lower() == '!optin':
            if not len(args) == 3:
                client.notice(user[0], 'To opt in for Hilight notifications, please use the following syntax:')
                return client.notice(user[0], 'Syntax: !optin [check out time in seconds] confirm')
            if args[2].lower() == 'confirm':
                try:
                    dur = int(args[1])
                    if dur <= 0:
                        return client.notice(user[0], 'Duration must be greater than 0.')
                    if self.optin(client, user[0], dur):
                        self.hlsync(upload=True) #upload our database with shelve
                        return client.notice(user[0], 'Duration period set to ' + args[1] + ' minute' + ('s' if dur == 1 else '') + '.')
                    return client.notice(user[0], 'Duration period not changed.')
                except:
                    client.notice(user[0], 'The duration should be the number of minutes you should be AFK before declared away.')
                    return client.notice(user[0], 'Syntax: !optin [check out time in seconds] confirm')

        # Optout of Hilighting services
        # Syntax: !optout confirm
        if args[0].lower() == '!optout':
            if len(args) == 2 and args[1].lower() == 'confirm':
                if self.optout(client, user[0]):
                    self.hlsync(upload=True)
                    return client.notice(user[0], 'You have successfully opted out of Hilighting services.')
                return client.notice(user[0], 'You are not currently subscribed to Hilighting services.')
            return client.notice(user[0], 'To confirm your opt out of Hilighting services from ' + client.profile.nick + ', please use \002!optout confirm')

    # check if a user is checked out, and send them their shit
    def checkin(self, client, user):
        if self.ischeckedout(client, user):
            #process any pending events
            c = 0
            e = []
            for event in self.events:
                if event['nick'] == user[0] and event['net'] == client.profile.network.name:
                    self.pushevent(event)
                c += 1
            c = 0
            for i in e:
                del self.events[i - c]
                c += 1

            #if no events, stop now
            if len(self.events) == 0:
                return

            #convert all events into pastebin format_exc
            events = self.getallevents(client, user[0])
            content = str(len(events)) + ' event ' + ('' if len(events) == 1 else 's') +' for ' \
                        + user[0] + ' on ' + client.profile.network.name + '\n\n'
            for event in events:
                content += 'Hilight Event in ' + event['chan'] + '\n'
                for scrollback in event['sb']:
                    content += scrollback['time'] + '  <' + scrollback['user'] + '> ' + scrollback['msg'] + '\n'
                content += '[end of event] \n\n'

            #upload to pastebin and send our results
            paste = pastee(self.key, 'Hilights for ' + user[0], content)
            return client.notice(user[0], 'Welcome back, you\'ve had ' + str(len(events)) + \
                            ' hilight' + ('' if len(events) == 1 else 's') +' since you\'ve ' + \
                            'been gone. ' + (paste.decode('utf-8') if len(events) > 0 else ''))

    def ischeckedout(self, client, user):
        for u in self.watch:
            if u['nick'] == user[0] and u['net'] == client.profile.network.name:
                return u['seen'] + (u['dur'] * 60) < time.time()

    # Check if a message's contents has a checked out user's nick
    def checkmsg(self, client, channel, msg):
        msg = msg.lower()
        for usr in self.watch:
            if usr['seen'] + (usr['dur'] * 60) < time.time() and usr['nick'].lower() in msg:
                # Hilight event, create a new even
                #u=nick, n=network name, c=channel, sb=list of messages missed
                print('event triggered for ' + usr['nick'])
                self.events.append({'nick': usr['nick'], 'net': client.profile.network.name, 'chan': channel, 'sb': self.getscrollback(client, channel)})

    # Store message in scrollback
    def storemsg(self, client, user, chan, message):
        # First, we add to our scrollback
        # pointer combines the network name and channel
        pointer = client.profile.network.name + '@' + chan
        # message storage format
        msg = {'user': user[0], 'msg': message, 'time': client.engine.log.get_timestamp()}
        sb = shelve.open(scrollback_db, writeback=True)
        try:
            # add new message contents to scrollback
            sb[pointer].append(msg)
        except:
            # New channel, create and restart storage
            sb[pointer] = []
            sb.close()
            return self.storemsg(client, user, chan, message)

        # check if our scrollback is the max size
        if len(sb[pointer]) > scrollback_limit:
            del sb[pointer][0] #delete the oldest line

        sb.close()

        #Now we will add to any events, and push if necessary
        c = 0 #counter for id
        r = [] #list of events to remove
        for ev in self.events:
            if ev['chan'] == chan and ev['net'] == client.profile.network.name:
                ev['sb'].append(msg)
                if len(ev['sb']) == scrollback_limit * 2:
                    self.pushevent(ev)
                    r.append(c)
            c += 1
        for i in r:
            del self.events[i]

        #Last we will update the sender's last seen time for Hilight
        for usr in self.watch:
            if usr['nick'] == user[0]:
                usr['seen'] = time.time()
                self.hlsync(upload=True) #update database with new time

    # optin to hilight service
    # return value declares whether a database sync is required
    def optin(self, client, nick, duration):
        #check for duplicates
        for u in self.watch:
            if u['nick'] == nick and u['net'] == client.profile.network.name:
                if u['dur'] == duration:
                    return False #no sync required
                u['dur'] = duration
                return True #sync required
        #no match, new user
        self.watch.append({'net': client.profile.network.name, 'nick': nick, 'dur': duration, 'seen': time.time()})
        return True # sync required

    # optout of hilight services
    # return value declares whether a database sync is required
    def optout(self, client, nick):
        c = 0
        for u in self.watch:
            if u['nick'] == nick and u['net'] == client.profile.network.name:
                del self.watch[c]
                return True
        return False

    # get the scrollback for a channel. Channel scrollback is listed  as 'network'@'channel'
    def getscrollback(self, client, channel):
        try:
            sb = shelve.open(scrollback_db)
            scroll = sb[client.profile.network.name + '@' + channel]
            sb.close()
            return scroll
        except:
            # no scrollback found (?)
            return []

    # write completed events to shelve
    def pushevent(self, event):
        hl = shelve.open(hilight_db, writeback=True)
        hl['out'].append(event)
        hl.close()

    # fetch all hilight events for a user. Note: calling this will clear the user's events
    def getallevents(self, client, nick):
        hl = shelve.open(hilight_db, writeback=True)
        try:
            c = 0 #counter
            r = [] #list to be cleared
            events = [] #result events
            for u in hl['out']:
                if u['nick'] == nick and u['net'] == client.profile.network.name:
                    events.append(u)
                    r.append(c)
                c += 1

            c = 0
            for i in r:
                del hl['out'][i - c]
                c += 1
        except:
            events = []
            hl.close()
        return events

    # Sync Hilight database auto checkout users with a local memory copy
    # upload will upload local copy to shelve file or otherwise download
    def hlsync(self, upload=False):
        try:
            hl = shelve.open(hilight_db, writeback=upload)
            if upload:
                hl['users'] = self.watch
            else:
                self.watch = hl['users']
            hl.close()
        except:
            # Database corrupt, recreate
            hl['users'] = []
            hl['out'] = []
            hl.close()
            return self.hlsync(upload)

def pastee(key, desc, txt):
	import requests # Import Requests

	post_param = {'key':key,'description':desc,'language':'plain','paste':txt,'format':'simple'} #Parameters to pass to the Pastee API
	r = None

	try:
		r = requests.post('http://paste.ee/api',json=post_param, verify=False) # Post the params to Pastee API and get the url
	except requests.ConnectionError as e:
		print('Connection Error')

	# Dictonary of errors
	error = {
			'error_no_key':'No Key present',
			'error_no_paste':'Nothing to paste',
			'error_invalid_key':'Please pass Valid Key',
			'error_invalid_language':'Invalid Langauge'
			}

	if r:
		if r.content in error:
			print(error[r.content]) #if any error return error
			return None
		else:
			#print (r.content) #print pastee url to the cmd or python command line
			return r.content

	return 0
