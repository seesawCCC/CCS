# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-26 20:41:19
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-08-02 16:18:07

import sys, os
import traceback
from enum import Enum, unique

@unique
class StatusCode(Enum):
	OK = 0
	CANCELLED = 1
	UNKNOWN = 2
	INVALID_ARGUMENT = 3 
	DEADLINE_EXCEEDED = 4
	NOT_FOUND = 5
	ALREADY_EXISTS = 6
	PERMISSION_DENIED = 7
	UNAUTHENTICATED = 8
	RESOURCE_EXHAUSTED = 9
	FAILED_PRECONDITION = 10
	ABORTED = 11
	OUT_OF_RANGE = 12
	UNIMPLEMENTED = 13
	INTERNAL = 14
	UNAVAILABLE = 15
	DATA_LOSS = 16
	FAILED_UNKNOWN = 17

def FCP_CHECK(condition, information=''):
	if not condition:
		raise Exception("Check failed:" + information)

def FCP_STATUS(code, reason='', value=None):
	frame = sys._getframe(1)
	file_path = frame.f_code.co_filename 
	line = frame.f_lineno
	return MakeStatusBuilder(code, file_path, line, reason, value)

def MakeStatusBuilder(code, file_path, line, reason, value):
	return StatusBuilder(code, file_path, line, reason, value).Status()

class Status():
	def __init__(self, code, value, reason):
		self._code = code
		self._reason = reason
		self._value = value

	def ok(self):
		return self._code == StatusCode.OK

	def status(self):
		return self._code

	def code(self):
		return self._code

	def value(self):
		return self._value

	def reason(self):
		return self._reason

class StatusBuilder():
	def __init__(self, code, file, line, reason, value):
		self._code = code
		self._file = file
		self._line = line
		self._message = reason
		self._value = value

	def ok(self):
		return self._code == StatusCode.OK

	def code(self):
		return self._code

	def Status(self):
		if not self.ok():
			message = "(at {}:{}){}".format(os.path.basename(self._file), self._line, self._message)
			self._message = message
			# Logger处理，现在先换成print
			print(self._message)
		return Status(self._code, self._value, self._message)

	def value(self):
		return self._value


def StatusWarp(obj):
	def inner(self, *args, **kwargs):
		status = StatusCode.OK
		message = ''
		try:
			result = obj(self, *args, **kwargs)
		except Exception as e:
			# 这里可以记录e
			traceback.print_exc()
			status = StatusCode.FAILED_UNKNOWN
			message = str(e)
			result = None
		if isinstance(result, Status):
			pass
		elif isinstance(result, StatusBuilder):
			result = result.Status()
		else:
			result = Status(status, result, message )
		return result
	return inner

