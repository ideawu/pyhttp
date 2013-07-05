#encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""
import new, socket
from buffer import *

LINK_ROLE_SERVER	= 1
LINK_ROLE_CLIENT	= 2
LINK_ROLE_ACCEPT	= 3

class LinkBase:
	def __init__(self, sock=None):
		self.id = -1
		self.fd = None
		self.sock = None
		self.local_addr = '' # ip:port
		self.remote_addr = '' # ip:port
		self.parent = None
		self.role = None
		self.ptr = None
		self.alive = False

		self.recv_pkt = None
		self.recv_buf = Buffer();
		self.send_buf = Buffer();

	def is_client(self):
		return self.role == LINK_ROLE_CLIENT

	def is_server(self):
		return self.role == LINK_ROLE_SERVER

	def is_accept(self):
		return self.role == LINK_ROLE_ACCEPT

	def listen(self, host, port, backlog=128):
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sock.bind((host, port))
			sock.listen(backlog)
		except BaseException, e:
			return False
		self.role = LINK_ROLE_SERVER
		self.set_sock(sock)

	# TODO: accept_all(self):

	def accept(self):
		sock, addr = self.sock.accept()
		link = new.instance(self.__class__)
		link.__init__(sock)
		link.role = LINK_ROLE_ACCEPT
		link.parent = self
		link.remote_addr = "%s:%d" % sock.getpeername()
		return link

	def connect(self, host, port):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((host, port))
		sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		self.role = LINK_ROLE_CLIENT
		self.set_sock(sock)
		self.remote_addr = "%s:%d" % sock.getpeername()

	def set_sock(self, sock):
		self.fd = sock.fileno()
		self.sock = sock
		self.alive = True
		self.local_addr = "%s:%d" % sock.getsockname()

	def is_alive(self):
		return self.alive

	def close(self):
		self.alive = False
		try:
			self.sock.close()
			self.sock = None
		except:
			pass

	def fileno(self):
		return self.fd

	""" 判断是否已经读就绪 """
	def recv_ready(self):
		return self.recv_pkt.ready()

	""" 进行一次网络读操作 """
	def net_recv(self, bufsize=8192):
		try:
			data = self.sock.recv(bufsize)
			#data = self.sock.recv(3)
			#print 'link <-', repr(data)
		except BaseException,e:
			return -1
		if not data:
			return 0

		self.recv_buf.append(data)
		return len(data)

	""" 进行一次网络写操作
	@return
		-1: 错误
		0 : 建议调用者关闭连接
	"""
	def net_send(self):
		try:
			len = self.sock.send(self.send_buf.base)
			#len = self.sock.send(self.send_buf.base[0:3])
			#print 'link ->', repr(self.send_buf.base[0:len])
		except BaseException,e:
			return -1

		self.send_buf.consume(len)
		return len

	""" 非阻塞发送(数据拷贝到发送缓冲) """
	def async_send(self, data):
		return self.send(data, urgent=False)

	""" 非阻塞读取 """
	def async_recv(self):
		return self.recv(block=False)

	""" 见 send_packet, 只传入要发送的报体 """
	def send(self, data, urgent=True):
		packet = self.PacketClass()
		packet.set_body(data)
		ret = self.send_packet(packet, urgent)
		return ret

	""" 见 recv_packet, 只返回报体部分 """
	def recv(self, block=True):
		ret = self.recv_packet(block)
		if ret == -1:
			return -1
		elif ret == None:
			return None
		else:
			return ret.body

	""" 非阻塞的 send_packet """
	def async_send_packet(self, packet):
		return self.send_packet(packet, urgent=False)

	""" 非阻塞的 recv_packet """
	def async_recv_packet(self):
		return self.recv_packet(block=False)

	""" 将报文写到发送缓冲里
	@param urgent: 若为True, 则等待网络发送完毕才返回. 默认等待.
	@return
	-1: 错误
	"""
	def send_packet(self, packet, urgent=True):
		data = packet.encode()
		self.send_buf.append(data)
		if urgent:
			while self.send_buf.len() > 0:
				if self.net_send() == -1:
					return -1
		return len(data)
