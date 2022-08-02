# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-10 20:54:58
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-28 15:22:52

from .secagg_client_state import SecAggClientState
from .secagg_client_terminal_state import SecAggClientAbortedState 
from ..shared.secagg_messages import ClientToServerWrapperMessage
from base.monitoring import StatusWarp

class SecAggClientAliveBaseState(SecAggClientState):
	def __init__(self, sender, transition_listener, state, async_abort):
		super().__init__(sender, transition_listener, state)
		self._async_abort = async_abort

	@StatusWarp
	def Abort(self, reason):
		return self.AbortAndNotifyServer("Abort upon external request for reason <{}>.".format(reason)) ;

	def AbortAndNotifyServer(self, reason):
		message_to_server = ClientToServerWrapperMessage()
		message_to_server.mutable_abort().set_diagnostic_info(reason)
		self._sender.Send(message_to_server)
		return SecAggClientAbortedState(reason, self._sender, self._transition_listener)