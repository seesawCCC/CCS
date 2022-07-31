# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-28 12:18:48
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-28 12:20:32

class StateTransitionListenerInterface():
	def __init__(self):
		pass

	def Transition(self, state):
		pass

	def Started(self, state):
		pass

	def Stopped(self, state):
		pass

	def set_execution_session_id(self, execution_session_id):
		pass