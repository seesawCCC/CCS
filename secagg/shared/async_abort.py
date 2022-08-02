# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-27 22:32:41
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-08-02 15:22:16

class AsyncAbort():
	def __init__(self, i):
		self._i = i

	def Abort(self, reason):
		print('Abort ' + reason)
		self._reason = reason
	
	def Signalled(self):
		return False

	def Message(self):
		pass