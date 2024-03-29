# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-08-18 22:11:14
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-11 23:38:44

import threading
from contextlib import contextmanager

class TimeoutLock():
	def __init__(self, default_timeout):
		self._mutex = threading.Lock()
		self._default_timeout = default_timeout

	def acquire(self, block=True, timeout=-1): 
		return self._mutex.acquire(block, timeout)

	@contextmanager
	def acquire_timeout(self, timeout=0):
		timeout = self._default_timeout if not timeout else timeout
		result = self._mutex.acquire(timeout=timeout)
		yield result
		if result:
			self._mutex.release()

	def release(self):
		self._mutex.release()


class UserPool():

	_class_lock = threading.Lock()

	def __new__(cls, *args, **kwargs):
		with cls._class_lock:
			if not cls.__dict__.get('_instance', None):
				cls._instance = super(UserPool, cls).__new__(cls)
		return cls._instance

	def __init__(self):
		self._user_table = {}
		# self._user_table_mutex = threading.Lock()
		self._user_table_mutex = TimeoutLock(2)
		self._max_user_id = 0


	def AddUser(self, address, user_info):
		error = 0
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return -1
			existed = self._user_table.get(address, None)
			if existed:
				if existed['last_nonce'] >= user_info['last_nonce']:
					error = 1
				elif self._max_user_id > user_info['client_id']:
					error = 2
			if error == 0:
				self._user_table[address] = user_info
				self._max_user_id = user_info['client_id']+1
		return error

	def Remove(self, address):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return False
			if address in self._user_table:
				self._user_table.pop(address)
				return True
			return False

	def ChangeStatus(self, address, new_status):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return None
			if address not in self._user_table:
				return False
			self._user_table[address]['status']	= new_status
			return True	

	def GetUserByAddress(self, address):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return {}
			user = self._user_table.get(address, None)
			return user

	def GetAllUserAddress(self):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return []
			all_user = []
			for callback in self._user_table:
				if self._user_table[callback]['connection']:
					all_user.append(callback)
			# return list(self._user_table.keys())
			return all_user

	def GetAllUser(self):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return []
			return list(self._user_table.items())

	def GetAllUserValue(self):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return []
			return list(self._user_table.values())

	def GetAllClientId(self):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return []
			return sorted([user['client_id'] for user in self._user_table.values()])

	def existed(self, client_address):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return False
			return client_address in self._user_table

	def SetSocket(self, address, client_socket):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result or not client_socket:
				return None
			self._user_table[address]['socket'] = client_socket
			return client_socket

	def GetSocket(self, address):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return None
			user = self._user_table.get(address, None)
			if not user:
				return user
			return user['socket']

	def Clear(self):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return False
			self._user_table.clear()
			return True

	def SetConnection(self, callback, status):
		with self._user_table_mutex.acquire_timeout() as result:
			if not result:
				return None
			self._user_table[callback]['connection'] = status

