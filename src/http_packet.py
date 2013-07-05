#encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""

HTTP_REQUEST	= 1
HTTP_RESPONSE	= 2

HTTP_METHOD_GET		= 'GET'
HTTP_METHOD_POST	= 'POST'
HTTP_METHOD_HEAD	= 'HEAD'

HTTP_VERSION_1_0	= 'HTTP/1.0'
HTTP_VERSION_1_1	= 'HTTP/1.1'

import re
from buffer import Buffer

class HttpPacket:
	def __init__(self, type=None):
		self.type = type

		self.header = {}
		self.body = ''
		self.bodylen = -1
		self.bodylen_left = -1
		self.cookies = []

		self.method = None
		self.uri = None
		self.version = None
		self.path = None	# uri的路径部分
		self.query = None
		self.status_code	= '200'
		self.status_text	= 'OK'

		self.STATE_NONE			= 0
		self.STATE_HEAD			= 10
		self.STATE_BODY			= 20
		self.STATE_CHUNK		= 21
		self.STATE_READY		= 30
		self.state = self.STATE_NONE

		self.EVENT_NONE			= 0
		self.EVENT_FIRST_LINE	= 10
		self.EVENT_HEAD			= 20
		self.EVENT_CHUNK		= 30
		self.EVENT_READY		= 40
		self.event = self.EVENT_NONE

		self.MAX_CHUNK_SIZE = 76 # 测试用, 正常情况应该设为较大值
		self.chunked = False
		self.chunk_size = -1
		self.chunk_left = -1
		self.chunk_body = ''
		self.merge_chunk = False

	def set_body(self, body):
		self.body = body

	def ready(self):
		return self.state == self.STATE_READY

	def is_request(self):
		return self.type == HTTP_REQUEST

	def is_response(self):
		return self.type == HTTP_RESPONSE

	def set_header(self, k, v):
		key = str(k)
		key_lower = key.lower()
		val = str(v)
		if key_lower in ['set-cookie', 'cookie']:
			self.cookies.append(val)
			return
		#self.header[key] = val
		self.header[key_lower] = (key, val)
		if key_lower == 'content-length':
			try:
				self.bodylen = int(val)
				self.bodylen_left = self.bodylen
			except:
				pass
		elif key_lower == 'transfer-encoding':
			self.chunked = (v == 'chunked')

	def get_header(self, k):
		k = k.lower()
		if self.header.has_key(k):
			return self.header[k][1]
		else:
			return ''

	def del_header(self, k):
		k = k.lower()
		if self.header.has_key(k):
			del self.header[k]

	def has_header(self, k):
		k = k.lower()
		return self.header.has_key(k)

	def decode(self, data):
		buf = Buffer(data)
		while True:
			if self.parse(buf) == -1:
				print 'decode error'
				return -1
			if self.event == self.EVENT_NONE:
				print 'data is not a valid packet'
				return -1
			elif self.event == self.EVENT_READY:
				print 'body ready'
				return
			elif self.event == self.EVENT_CHUNK:
				print 'chunk', repr(self.chunk_body)
				self.body += self.chunk_body
			elif self.event == self.EVENT_HEAD:
				print 'head ready'

	def parse(self, buf):
		# 恢复状态, 因为 CHUNK 是一个临时状态
		if self.event == self.EVENT_CHUNK:
			self.state = self.STATE_BODY
			self.chunk_body = ''

		self.event = self.EVENT_NONE

		if self.state == self.STATE_NONE:
			if self.parse_first_line(buf) == -1:
				return -1
			if self.state == self.STATE_HEAD:
				self.event = self.EVENT_FIRST_LINE
		elif self.state == self.STATE_HEAD:
			if self.parse_header(buf) == -1:
				return -1
			# test
			if self.state == self.STATE_BODY:
				self.event = self.EVENT_HEAD
		else:
			if self.parse_body(buf) == -1:
				return -1
			# test
			# 即使是 normal-body, 也会先返回 chunk, 再 ready
			if self.state == self.STATE_CHUNK:
				self.event = self.EVENT_CHUNK
			if self.state == self.STATE_READY:
				self.event = self.EVENT_READY

	def parse_first_line(self, buf):
		while True:
			line = buf.readline()
			if line == None:
				return
			elif line == '\r\n' or line == '\n': # 忽略前置的空白行
				continue
			break

		ps = re.split('\s+', line.strip(), 2)
		if len(ps) != 3:
			print 'bad first line: ' + repr(line)
			return -1

		if self.is_request():
			method, uri, version = ps
			if method not in [HTTP_METHOD_GET, HTTP_METHOD_POST, HTTP_METHOD_HEAD]:
				print 'bad method ' + method
				return -1
			if uri.find('?') != -1:
				path, query = uri.split('?', 1)
			else:
				path, query = uri, ''
			self.method, self.uri, self.version = method, uri, version
		else:
			version, code, text = ps
			if len(code) != 3 or code.isdigit() == False:
				print 'bad code ' + code
				return -1
			self.version = version
			self.status_code = code
			self.status_text = text

		if version not in [HTTP_VERSION_1_0, HTTP_VERSION_1_1]:
			print 'bad version ' + version
			return -1

		self.state = self.STATE_HEAD

	def parse_header(self, buf):
		while buf.len() > 0:
			if buf.base.startswith('\r\n'):
				buf.base = buf.base[2 : ]
				if self.method in [HTTP_METHOD_GET, HTTP_METHOD_HEAD]:
					if self.chunked:
						print 'chunked with ' + self.method
						return -1
					self.bodylen = 0
					self.bodylen_left = 0
				if self.bodylen < 0 and not self.chunked:
					print 'bad Content-Length: %d' % self.bodylen
					return -1
				self.state = self.STATE_BODY
				return

			line_len = 0
			while True:
				pos = buf.base.find('\n', line_len)
				if pos == -1:
					return
				line_len = pos + 1
				if line_len == buf.len():
					# 可能折行未接收完整, 所以停止解析
					return

				# 为了兼容折行header, 必须在\n之后跟着数据才能确定是否为一个完整的header
				ch = buf.base[line_len]
				if ch == ' ' or ch == '\t': # 折行的header
					#print 'multiline header'
					continue

				line = buf.read(line_len)
				#print 'recv: ' + repr(line)
				if line.find(':') == -1:
					self.set_header(line, None)
				else:
					key, val = line.split(':', 1)
					key = key.strip()
					val = val.strip()
					self.set_header(key, val)
				break

	def parse_body(self, buf):
		# TODO: max packet body
		if self.chunked:
			ret = self.parse_chunked_body(buf)
		else:
			ret = self.parse_normal_body(buf)
		return ret

	def parse_normal_body(self, buf):
		want = min(self.bodylen_left, self.MAX_CHUNK_SIZE - len(self.chunk_body))
		data = buf.read(want)
		self.chunk_body += data
		self.bodylen_left -= len(data)

		if self.bodylen_left == 0:
			if self.chunk_body:
				self.state = self.STATE_CHUNK
			else:
				self.state = self.STATE_READY
		elif len(self.chunk_body) == self.MAX_CHUNK_SIZE:
			self.state = self.STATE_CHUNK

	def parse_chunked_body(self, buf):
		if self.chunk_size == -1:
			line = buf.readline()
			if line == None:
				return
			size = line.split(';', 1)[0]
			try:
				self.chunk_size = int(size, 16)
				self.chunk_left = self.chunk_size
			except:
				print 'parse chunk size[%s] error'%repr(size)
				return -1
			#print 'chunk size[%d]'% self.chunk_size
		if self.chunk_size == 0:
			# 这是一个等待合并的chunk
			if self.merge_chunk: # merge chunk?
				if self.chunk_body:
					self.state = self.STATE_CHUNK
					return
			while True:
				line = buf.readline()
				if line == None:
					return
				if line == '\r\n' or line == '\n':
					#print 'chunk end'
					self.state = self.STATE_READY
					return
				#print 'chunk footer: ' + repr(line)
				if line.find(':') == -1:
					self.set_header(line, None)
				else:
					key, val = line.split(':', 1)
					key = key.strip()
					val = val.strip()
					self.set_header(key, val)
		else:
			if self.chunk_left > 0:
				want = min(self.chunk_left, self.MAX_CHUNK_SIZE - len(self.chunk_body))
				#print 'chunk_left=%d, want=%s' %(self.chunk_left, want)
				data = buf.read(want)
				self.chunk_body += data
				self.chunk_left -= len(data)
			if len(self.chunk_body) == self.MAX_CHUNK_SIZE:
				self.state = self.STATE_CHUNK # 收到的一个chunk, 可能分解成多个chunk
				return
			if self.chunk_left == 0:
				if buf.len() >= 2: # CRLF
					ret = buf.read(2)
					if ret != '\r\n':
						print 'bad chunk data ends with: %s'%repr(ret)
						return -1
					self.chunk_size = -1
					if not self.merge_chunk and self.chunk_body: # merge chunk?
						self.state = self.STATE_CHUNK
						return
				elif buf.len() == 1 and buf.base[0] == '\n': # LF
					buf.read(1)
					self.chunk_size = -1
					if not self.merge_chunk and self.chunk_body: # merge chunk?
						self.state = self.STATE_CHUNK
						return
				else: # not sure if chunk is ready
					pass

	def encode(self):
		return self.encode_header() + self.body

	def encode_header(self):
		if not self.has_header('Content-Length') and not self.chunked:
			self.set_header('Content-Length', len(self.body))

		first_line = ''
		if self.is_request():
			first_line += '%s %s %s\r\n'%(self.method, self.uri, self.version)
		else:
			first_line += '%s %s %s\r\n'%(self.version, self.status_code, self.status_text)

		if self.is_request():
			cookies = 'Cookie: ' + '; '.join(self.cookies) + '\r\n';
		else:
			cookies = ''
			for c in self.cookies:
				cookies += 'Set-Cookie: ' + c + '\r\n'

		header = ''
		for k_lower, (k, v) in self.header.iteritems():
			if v == None:
				header += str(k) + '\r\n'
			else:
				header += str(k) + ': ' + str(v) + '\r\n'
		header += '\r\n' # "首部"还包括一个空行
		return first_line + cookies + header


class HttpResponse(HttpPacket):
	def __init__(self):
		HttpPacket.__init__(self, HTTP_RESPONSE)
		self.merge_chunk = False


# TODO: multipart
class HttpRequest(HttpPacket):
	def __init__(self):
		HttpPacket.__init__(self, HTTP_REQUEST)
		self.merge_chunk = True
		self.host = None
		self.port = 80

	def set_url(self, url):
		if url.find('://') == -1:
			url = 'http://' + url
		schema, right = url.split('://', 1)
		if schema.lower() != 'http':
			raise 'informal url: %s'%url
		if right.find('/') == -1:
			host = right
			self.uri = '/'
		else:
			host, right = right.split('/', 1)
			self.uri = '/' + right
		if host.find(':') != -1:
			self.host, port = host.split(':', 1)
			self.port = int(port)
		else:
			self.host = host
		if self.uri.find('?') != -1:
			self.path = self.uri.split('?', 1)[0]
		else:
			self.path = self.uri
		self.set_header('Host', self.host)

