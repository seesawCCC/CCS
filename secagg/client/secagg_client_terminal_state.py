# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-08 20:16:33
# @Last Modified time: 2022-07-28 13:07:37
from .secagg_client_state import SecAggClientState
from .client_state import ClientState
from base.monitoring import StatusWarp

class SecAggClientAbortedState(SecAggClientState):
	def __init__(self, reason, sender, transition_listener):
		super().__init__(sender, transition_listener, ClientState.ABORTED)
		self.reason = reason
		# 记录日志(abort的原因)

	def IsAborted(self):
		return True

	@StatusWarp
	def ErrorMessage(self):
		return self.reason if self.reason else "None"

	def StateName(self):
		return "ABORTED"

class SecAggClientCompletedState(SecAggClientState):
	def __init__(self, sender, transition_listener):
		super().__init__(sender, transition_listener, ClientState.COMPLETED)

	def IsCompletedSuccessfully(self):
		return True

	def StateName(self):
		return 'COMPLETED'
