# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-08 20:18:58
# @Last Modified time: 2022-07-11 21:46:16

class SecAggClientState():
	def __init__(self, sender, transition_listener, state):
		pass

	def Start(self):
		pass

	def HandleMessage(self, message):
		pass

	def SetInput(self, input_map):
		pass

	def Abort(self, reason):
		pass

	def IsAborted(self):
		pass

	def IsCompletedSuccessfully(self):
		pass

	def ValidateInput(self, input_map, input_vector_specs):
		pass

	def StateName(self):
		pass

	def State(self):
		pass