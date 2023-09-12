import requests
import time
import lib.Timer

updateLimit = 3  # Amount of topics to update with per change

def fetch_list():
    drudge = requests.get('https://feedpress.me/drudgereportfeed')
    drudge = str(drudge.content)[2:].replace('  ', '').split('\\n')
    reports = []
    i = 0
    counter = 0
    for x in drudge:
        if x.startswith('<title>'):  # We are looking for the Title, and the link will follow
            if counter is 0:  # The first instance of this is the main title, we skip this.
                counter += 1
                i += 1
                continue
            x = x.replace('\\', '')
            title = x.split('>')[1]
            title = title.split('<')[0]
            link = drudge[i + 1]
            link = link.split('>')[1]
            link = link.split('<')[0]
            reports.append([title, link])
            counter += 1
        i += 1
    return reports


class DrudgeTimer:

    # TODO store a list of the channels/networks that we are subbed to, similar to how OSRS operates...
    def __init__(self, eng, sub=[]):
        self.schedule = lib.Timer.Schedule('DrudgeTimer', 60)  #
        self.subs = sub
        self.engine = eng
        self.headlines = fetch_list()

    def add_subscription(self, bot, channel):
        self.subs.append([bot, channel.lower()])

    def rem_subscription(self, bot, channel):
        self.subs.remove([bot, channel.lower()])

    def is_subscribed_channel(self, bot, channel):
        return [bot, channel.lower()] in self.subs

    def broadcast(self, msg):
        for sub in self.subs:
            print(sub)
            sub[0].msg(sub[1], msg)

    def get_headlines(self):
        return self.headlines

    def clear(self):
        self.headlines = fetch_list()

    def containHeadline(self, newHeadline):
        newHeadline = newHeadline.lower()
        for h in self.headlines:
            if h[0].lower() == newHeadline:
                return True
        return False

    def execute(self, engine):
        report = fetch_list()
        count = 0
        for r in report:
            if count == updateLimit:
                break

            if self.containHeadline(r[0]):
                continue
            else:
                self.broadcast('' + r[0] + ' \00303(' + r[1] + ')')
                engine.log.write('(+) Headline: ' + r[0])
                count += 1
        self.headlines = report
