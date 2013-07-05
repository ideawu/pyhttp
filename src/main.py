#encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""

from packet import *


text = '\r\n'
text += 'HTTP/1.1 200 OK\r\n'
#text += 'POST / HTTP/1.1\r\n'
text += 'Host: www.baidu.com\r\n'
text += 'User-Agent: Mozilla/5.0 (Linux; U; en-US; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7\r\n'
text += 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n'
text += 'Accept-Language: en-us,en;q=0.5\r\n'
text += 'Accept-Encoding: gzip,deflate\r\n'
text += 'Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7\r\n'
text += ' Keep-Alive: 300\r\n'
text += 'Connection: keep-alive\r\n'
text += 'Cache-Control: max-age=0\r\n'
text += 'Transfer-Encoding: chunked\r\n'
#text += 'Content-Length: 7\r\n'
text += '\r\n'
text += '1a; ignore-stuff-here\r\n'
text += 'abcdefghijklmnopqrstuvwxyz\r\n'
text += '10\r\n'
text += '1234567890abcdef\r\n'
text += '0\r\n'
text += 'some-footer: some-value\r\n'
text += 'another-footer: another-value\r\n'
text += '\r\n'
text += 'POST / HTTP/1.1\r\n'
text += 'Cookie: www.baidu.com\r\n'
text += 'Host: www.baidu.com\r\n'
text += 'Content-Length: 7\r\n'
text += '\r\n'
text += '1234567'

print text



def proc_recv(req, buf):
	while True:
		if req.parse(buf) == -1:
			return -1
		if req.event == req.EVENT_NONE:
			#print 'event none'
			return
		elif req.event == req.EVENT_READY:
			print 'body ready'
			return
		elif req.event == req.EVENT_CHUNK:
			print 'chunk', repr(req.chunk_body)
		elif req.event == req.EVENT_HEAD:
			print 'head ready'
		"""
		elif req.event == req.EVENT_FIRST_LINE:
			if req.is_request():
				print 'first-line: ' + repr('%s %s %s'%(req.method, req.uri, req.version))
			else:
				print 'first-line: ' + repr('%s %s %s'%(req.version, req.status_code, req.status_text))
		"""


for chunk_size in range(3, 6):
	buf = Buffer()
	req = HttpResponse()
	req.CHUNK_SIZE = chunk_size
	print '---chunk_size[%d]---'%chunk_size
	if 0:
		for ch in list(text):
			buf.append(ch)
			if proc_recv(req, buf) == -1:
				exit(0)
				print 'error'
				break
			if req.event == req.EVENT_READY:
				print '------'
				req = HttpRequest()
				req.CHUNK_SIZE = chunk_size
	else:
		buf.append(text)
		while buf.len() > 0:
			if proc_recv(req, buf) == -1:
				print 'error'
				exit(0)
				break
			if req.event == req.EVENT_READY:
				print '------'
				req = HttpRequest()
				req.CHUNK_SIZE = chunk_size


#print
#for k,v in req.header.iteritems():
#	print k, ':', v

