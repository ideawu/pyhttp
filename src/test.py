#encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""
from http_link import *



http = HttpLink()

for i in range(0, 1):
	"""
	data = {
		'a' : i,
	}

	resp = http.request('http://localhost:8080/index.php', data)
	"""

	resp = http.request('http://www.baidu.com')

	print '----------'
	print '> ' + http.last_req.encode().replace('\n', '\n> ')
	print '----------'
	print '< ' + resp.encode().replace('\n', '\n< ')
	print '----------'


