# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-27 22:32:41
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-28 15:19:31

class AsyncAbort():
	def __init__(self, i):
		self._i = i

	def Abort(self, reason):
		print('Abort ' + reason)
		self._reason = reason
	
	def Signalled(self):
		pass

	def Message(self):
		pass