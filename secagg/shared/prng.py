# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-19 17:50:50
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-19 18:13:00

class SecurePrng():
	def __init__(self):
		pass

	def Rand8(self):
		pass

	def Rand64(self):
		pass

class SecureBatchPrng(SecurePrng):
	def __init__(self):
		super().__init__()

	def GetMaxBufferSize(self):
		pass

	def RandBuffer(self, buffer, buffer_size):
		pass