from lib import Engine


class Alarm:

    def __init__(self, alarm):
        self.module = Engine.Module('Alarm', ['PRIVMSG'])
        self.alarm = alarm  # Our AlarmClock timer

    def message(self, client, user, channel, message):
        args = message.lower().split(' ')

        if not channel.startswith('#'):
            return

        if args[0] == '!help':
            return client.msg(channel, user[0] + ': [Alarm Help:] !newalarm - !view - !cancel')

        if args[0] == '!newalarm':
            if len(args) > 2:
                try:
                    time = int(args[1])
                except Exception:
                    return client.notice(user[0], 'Invalid time. How many minutes from now?')
                chk = self.alarm.add_alarm(user, time, channel, message[message.index(args[2]):], client)
                if not chk:
                    return client.notice(user[0], 'You already have an alarm set.')
                return client.notice(user[0], 'Your alarm has been set for ' + args[1] + ' minutes from now.')
            else:
                return client.notice(user[0], 'Syntax: !newalarm [time] [message]')

        if args[0] == '!view':
            alarm = self.alarm.read_alarm(user)
            if alarm is None:
                return client.notice(user[0], 'You have no alarm set.')
            return client.notice(user[0], 'Channel: ' + alarm[2] + ' - Time left: ' + Engine.timedString(
                float(alarm[1]) * 60) + ' - Message - ' + alarm[3])

        if args[0] == '!cancel':
            alarm = self.alarm.read_alarm(user)
            if alarm is None:
                return client.notice(user[0], 'You have no alarm set.')
            if len(args) > 1 and args[1] == 'confirm':
                if self.alarm.rem_alarm(user) == 1:
                    return client.notice(user[0], 'Your alarm was removed successfully.')
                return client.notice(user[0], 'There was a conflict removing your alarm!')
            return client.notice(user[0], 'Type !cancel confirm to confirm the removal of your current alarm.')
