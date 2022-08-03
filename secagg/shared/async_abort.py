# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-27 22:32:41
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-28 15:19:31

import threading
import rwlock
from base.monitoring import FCP_CHECK

l = rwlock.RWLock()

class AsyncAbort(threading.Thread):

	def __init__(self, signal):
		self._signal = signal
		# 使用了读写锁
		threading.Thread.__init__(self)
		FCP_CHECK(self._signal==[])

	def Abort(self, message):
		l.writer_lock.acquire()
		self._signal.append(message)
		l.writer_lock.release()

	
	def Signalled(self):
		if self._signal:
			return True
		else:
			return False

	def Message(self):
		l.reader_lock.acquire()
		return ';'.join(self._signal)

