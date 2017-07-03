import time

class Logger:

	def __init__(self, output="./data/console.log"):
		self.output = open(output, 'w')

	def write(self, content):
		st = self.get_timestamp() + "\t" + content
		self.output.write(st + "\n")
		self.output.flush()
		print(st)

	def close(self):
		self.output.close()

	def get_timestamp(self):
		return "[" + (time.strftime("%H:%M:%S")) + " " + (time.strftime("%d/%m/%Y")) + "]"
