import time
import lib.Timer

class AlarmClock:
	
	def __init__(self, engine):
		self.schedule = lib.Timer.Schedule('AlarmClock', 1, active=False)  # disable this module until needed
		self.alarms = []
		self.engine = engine  # for logging/debugging purposes
		
	def strike(self):
		return self.start <= time.time()
			
	def clear(self):
		self.start = time.time() + self.delay
		
	def read_alarm(self, registrar):
		for a in self.alarms:
			if a[0] == registrar[0]:
				x = str((int(a[1]) - time.time()) / 60)
				return [a[0], x, a[2], a[3]]
		return None
		
	def rem_alarm(self, registrar):
		for a in self.alarms:
			if a[0] == registrar[0]:
				self.alarms.remove(a)  # remove the alarm

				# if this is the last alarm, lets disable this timer
				if len(self.alarms) == 0:
					self.schedule.active = False
					self.engine.log.write('(AlarmClock) Timer disabled.')
				return 1
		return 0
		
	def add_alarm(self, registrar, tme, channel, message, client):
		if len(self.alarms) == 0:
			self.schedule.active = True
			self.engine.log.write('(AlarmClock) Timer enabled.')
		else:
			for a in self.alarms:
				if a[0] == registrar[0]:
					return False  # already has an alarm set

		self.alarms.append([registrar[0], (tme * 60) + time.time(), channel, message, client])
		return True
	
	def exec_alarm(self, alarm):
		alarm[4].msg(alarm[2], "\0033[Alarm] \00301- " + alarm[3] + " [set by " + alarm[0] + "]")
		alarm[4].notice(alarm[0], "Your alarm has gone off!")
		self.alarms.remove(alarm)
	
	def execute(self, engine):
		# do our checks
		for a in self.alarms:
			if a[1] <= time.time():
				self.exec_alarm(a)

		if len(self.alarms) == 0:
			self.engine.log.write('(AlarmClock) Disabling timer ...')
			self.schedule.active = False
