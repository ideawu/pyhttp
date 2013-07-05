#encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""
import new, socket, urllib
from link_base import *
from http_packet import *
import log

class HttpLink(LinkBase):
	def __init__(self, sock=None):
		LinkBase.__init__(self, sock)

		self.keep_alive = False
		self.last_req = HttpRequest()

	def listen(self, host, port, backlog=128):
		self.recv_pkt = HttpRequest()
		return LinkBase.listen(self, host, port, backlog)

	def accept(self):
		self.recv_pkt = HttpRequest()
		return LinkBase.accept(self)

	def connect(self, host, port):
		self.recv_pkt = HttpResponse()
		return LinkBase.connect(self, host, port)

	def net_send(self):
		ret = LinkBase.net_send(self)
		if self.is_accept() and not self.keep_alive and self.send_buf.len() == 0:
			return 0
		return ret

	def send(self, data, urgent=True, header={}):
		if self.is_client():
			packet = HttpRequest()
			packet.method = HTTP_METHOD_POST
			packet.uri = '/'
			self.last_req = packet
		else:
			packet = HttpResponse()

		for k,v in header.iteritems():
			packet.set_header(k, v)
		packet.set_body(str(data))

		return self.send_packet(packet, urgent)

	def send_packet(self, packet, urgent=True):
		if self.keep_alive:
			if not packet.version:
				packet.version = HTTP_VERSION_1_1
			if not packet.has_header('Connection'):
				packet.set_header('Connection', 'Keep-Alive')
			if not packet.has_header('Keep-Alive') and self.is_client():
				packet.set_header('Keep-Alive', '300')
		else:
			if not packet.version:
				packet.version = HTTP_VERSION_1_0
		if packet.get_header('Connection').lower() != 'keep-alive':
			self.keep_alive = False
		return LinkBase.send_packet(self, packet, urgent)

	"""
	进行一次报文解析, 返回解析的事件
	"""
	def proc_recv(self):
		buf = self.recv_buf
		packet = self.recv_pkt
		if packet.parse(buf) == -1:
			return -1
		return packet.event

	""" 从接收缓冲区中读取一个报文,
	@param block: 是否阻塞直到接收完毕. 默认阻塞.
	@return
	0: 连接关闭
	-1: 错误
	None: 报文未就绪(block 不为 True 时)
	Packet: 收到的报文
	"""
	def recv_packet(self, block=True):
		buf = self.recv_buf
		packet = self.recv_pkt
		while True:
			if self.recv_ready():
				break
			if packet.parse(buf) == -1:
				return -1

			# TODO: callbacks
			if packet.event == packet.EVENT_NONE:
				if block:
					self.net_recv()
				else:
					return None
			elif packet.event == packet.EVENT_READY:
				#print 'body ready'
				pass
			elif packet.event == packet.EVENT_CHUNK:
				#print 'chunk', repr(packet.chunk_body)
				packet.body += packet.chunk_body
			elif packet.event == packet.EVENT_HEAD:
				#print 'head ready'
				pass

		if packet.get_header('Connection').lower() == 'keep-alive':
			#print 'keep-alive'
			self.keep_alive = True
		else:
			#print 'not keep-alive'
			self.keep_alive = False

		self.recv_pkt = new.instance(self.recv_pkt.__class__)
		self.recv_pkt.__init__()
		return packet

	# TODO: 完善
	def request(self, url, data=None):
		self.keep_alive = True
		req = HttpRequest()

		if not data:
			req.method = HTTP_METHOD_GET
		else:
			req.method = HTTP_METHOD_POST
			if isinstance(data, dict):
				req.set_header('Content-Type', 'application/x-www-form-urlencoded')
				req.set_body(urllib.urlencode(data))
			else:
				req.set_body(str(data))
		req.set_url(url)

		if req.host != self.last_req.host or req.port != self.last_req.port:
			self.close()

		if not self.is_alive():
			# TODO: 判断 host:port 是否和上次相同
			log.debug('open new connection')
			self.connect(req.host, req.port)
		else:
			log.debug('reuse connection')

		self.last_req = req
		self.send_packet(req)

		resp = self.recv_packet()
		if resp == -1:
			log.error('server return -1')
			return ''

		if not self.keep_alive:
			self.close()

		return resp
