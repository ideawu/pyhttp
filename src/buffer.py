#encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""

class Buffer:
	def __init__(self, data=''):
		self.base = data

	def append(self, data):
		self.base += data

	def consume(self, len):
		self.base = self.base[len :]

	def len(self):
		return len(self.base)

	def read(self, size):
		ret = self.base[0 : size]
		self.base = self.base[size : ]
		return ret


	def readline(self):
		pos = self.base.find('\n')
		if pos == -1:
			return None
		line_len = pos + 1
		line = self.base[0 : line_len]
		self.base = self.base[line_len : ]
		return line
