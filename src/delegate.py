#encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""
import thread
import Queue
import log
"""
异步调用API
"""

class DelegateException(Exception):
	pass

class DelegateResults:
	def __init__(self):
		self.items = {}
		self.a_lock = thread.allocate_lock()

	def slot(self, handle):
		with self.a_lock:
			self.items[handle] = Queue.Queue()

	def drop(self, handle):
		with self.a_lock:
			if self.items.has_key(handle):
				del self.items[handle]
			else:
				return False

	def put(self, handle, result):
		with self.a_lock:
			if self.items.has_key(handle):
				self.items[handle].put(result)
			else:
				return False

	""" 见 Delegate.begin 的描述 """
	def get(self, handle, timeout=-1, destroy_handle=True):
		with self.a_lock:
			if not self.items.has_key(handle):
				raise DelegateException('invalid handle[%s]'%repr(handle))
			item = self.items[handle]
		if timeout == -1:
			block = True
			timeout = None
		elif timeout == 0:
			block = False
		else:
			block = True
		result_t = None

		try:
			result_t = item.get(block, timeout)
			item.task_done();
		except:
			pass

		if result_t == None and destroy_handle:
			with self.a_lock:
				del self.items[handle]

		if result_t:
			status, result = result_t
			if not status:
				raise result
			return result
		return None


"""
异步调用API
"""
class Delegate:
	def __init__(self, maxsize=128):
		self.next_handle = 0
		self.num_workers = 0
		self.jobs = Queue.Queue(maxsize)
		self.results = DelegateResults()


	""" 启动工作线程
	@param worker_nums: 工作线程的数目
	"""
	def init(self, num_workers):
		self.num_workers = num_workers
		i = 0
		while i < self.num_workers:
			i += 1
			id = 'worker[%d]'%i
			thread.start_new_thread(self.worker_thread, (id,))

	""" 销毁所有工作线程
	"""
	def free(self):
		jobs = []
		# clear jobs
		while True:
			try:
				job = self.jobs.get_nowait()
				jobs.append(job)
				self.jobs.task_done()
			except:
				break
		i = 0
		# send quit signal
		while i < self.num_workers:
			i += 1
			self.jobs.put(None)
		self.jobs.join()
		#TODO: for job in jobs: error_callback?

	def worker_thread(self, id):
		log.debug('%s started'%id)
		while True:
			try:
				job = self.jobs.get(block=True, timeout=0.1)
				self.jobs.task_done()
			except Queue.Empty:
				continue
			if job == None:
				log.trace('got signal to quit')
				break
			handle, user_func, args, user_callback, user_cb_args = job
			try:
				result = user_func(args)
				status = True
			except BaseException,e:
				status = False
				result = e
			log.trace('%s one job done'%id)

			self.results.put(handle, (status, result))
			if user_callback:
				try:
					user_callback(handle, user_cb_args)
				except:
					pass
		log.debug('%s quit'%id)

	def __sys_callback(self, handle, result_t, user_callback, user_cb_args):
		self.results.put(handle, result_t)
		if user_callback:
			try:
				user_callback(handle, user_cb_args)
			except:
				pass

	""" 开始异步调用, 返回句柄, 通过该句柄获取结果
	@param func: 要执行的函数
	@param args: 要执行的函数的参数
	@param callback: 操作完成后要执行的回调, 回调中必须调用 Delegate.end() 方法获取结果,
		如果func()执行过程抛出异常, end()也会抛出同样的异常.
	@param callback_args: 执行callback时的参数.
	callback 和原型为 function(handle, callback_args)
	"""
	def begin(self, func, args=None, callback=None, callback_args=None):
		self.next_handle += 1
		handle = self.next_handle

		self.results.slot(handle)
		self.jobs.put((handle, func, args, callback, callback_args))
		return handle

	""" 获取异步调用的结果
	@param destroy_handle: 是否在返回之前销毁句柄, 而不论是否有结果.
	@return 返回操作的结果, 若操作还未执行完毕返回 None.
	"""
	def end(self, handle, timeout=-1, destroy_handle=False):
		return self.results.get(handle, timeout, destroy_handle)

