import time


def get_timestamp():
	return "[" + (time.strftime("%H:%M:%S")) + " " + (time.strftime("%d/%m/%Y")) + "]"


class Logger:

	def __init__(self, output="./data/console.log"):
		self.output = open(output, 'w')

	def write(self, content, toBuffer=True):
		st = get_timestamp() + "\t" + content
		self.output.write(st + "\n")
		self.output.flush()
		if toBuffer:
			print(st)

	def close(self):
		self.output.close()
