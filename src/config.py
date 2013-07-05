# encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""
import re

class Config:
	def __init__(self, key='root', val='', parent=None):
		self.key = key
		self.val = val
		self.parent = parent
		self.children = []

	def __strspn(self, string, pred):
		from itertools import takewhile
		return len(list(takewhile(pred.__contains__, string)))

	def load(self, filename):
		self.filename = filename
		f = open(filename, 'r')
		lines = f.readlines()
		f.close()

		lineno = 0
		last_cfg = self
		for line in lines:
			lineno += 1
			if not line.strip():
				continue

			indent = self.__strspn(line, '\t')
			last_indent = last_cfg.get_depth() - 1
			if indent == last_indent:
				parent = last_cfg.parent
			elif indent == last_indent + 1:
				parent = last_cfg
			elif indent < last_indent:
				parent = last_cfg.get_parent(last_indent - indent + 1)
			else:
				print 'line(%d): invalid indent %d' %(lineno, indent)
				return False

			line = line.lstrip()
			if line[0:1] == '#':
				key = '#'
				val = line[1:]
				key = key.strip()
				val = val.strip()
			else:
				ps = re.split('[\:=]', line, 1)
				if len(ps) != 2:
					print 'line(%d)bad line: %s' %(lineno, repr(line))
					return False
				key, val = ps
				key = key.strip()
				val = val.strip()

			last_cfg = parent.add_child(key, val)
		return True

	def get_depth(self):
		c = self
		d = 0
		while c.parent:
			d += 1
			c = c.parent
		return d

	def get_parent(self, depth):
		cfg = self
		while depth > 0 and cfg:
			cfg = cfg.parent;
			depth -= 1
		return cfg;

	#def add(self, path, val):
	#	self.children[key] = val

	def get(self, path=None):
		cfg = self
		if path:
			ps = re.split('[\.\/]', path)
			for p in ps:
				cfg = cfg.get_child(p)
				if cfg == False:
					return False
		return cfg

	def add_child(self, key, val):
		#print '%s < %s'%(self.key, key)
		cfg = Config(key, val, self)
		self.children.append(cfg)
		return cfg

	def get_child(self, key):
		for child in self.children:
			if child.key == key:
				return child
		return False

	def get_str(self, path=None, defval=''):
		cfg = self.get(path)
		if cfg == False:
			return defval
		else:
			return cfg.val

	def get_int(self, path=None, defval=-1):
		cfg = self.get(path)
		if cfg == False:
			return defval
		else:
			try:
				ret = int(cfg.val)
				return ret
			except:
				return defval

	def to_str(self, indent=0):
		buf = ''
		if indent >= 0:
			buf += '\t' * indent
		if self.key == '#':
			buf += self.key + ' ' + self.val + '\n'
		else:
			buf += self.key + ' : ' + self.val + '\n'

		for child in self.children:
			buf += child.to_str(indent + 1)

		if indent == 0 and len(self.children) > 0:
			buf += '\n'
		return buf


	def save(self, filename=None):
		print self.to_str()


def load(filename):
	conf = Config()
	ret = conf.load(filename)
	if ret == False:
		return False
	else:
		return conf


