# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-10 20:54:58
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-11 22:01:23

from .secagg_client_state import SecAggClientState
from .secagg_client_terminal_state import SecAggClientAbortedState 
from ..shared.cs_message import ClientToServerWrapperMessage

class SecAggClientAliveBaseState(SecAggClientState):
	def __init__(self, sender, transition_listener, state, async_abort):
		super().__init__(sender, transition_listener, state)
		self._async_abort = async_abort

	# 最终返回SecAggClientAbortedState
	def Abort(self, reason):
		return AbortAndNotifyServer("Abort upon external request for reason <{}>.".format(reason)) ;

	def AbortAndNotifyServer(self,reason):
		message_to_server = ClientToServerWrapperMessage()
		message_to_server.mutable_abort().set_diagnostic_info(reason)
		self.sender.Send(message_to_server)
		return SecAggClientAbortedState(reason, self.sender, self.transition_listener)