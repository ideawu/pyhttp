#encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""

def instance_class(path):
	ps = path.split('.')
	if len(ps) >= 2:
		pkt = '.'.join(ps[0:-1])
		mod = __import__(pkt)
		for p in ps[1:]:
			mod = getattr(mod, p)
	else:
		import sys
		modname = globals()['__name__']
		mod = sys.modules[modname]
		mod = getattr(mod, path)
	instance = mod()
	return instance
