# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-08 20:18:58
# @Last Modified time: 2022-07-28 15:25:42

# 注意: FAILED_PRECONDITION以及FCP_STATUS()以后要根据模块的不同来重新构写
# 对于 FAILED_PRECONDITION以及FCP_STATUS的引用等确定了之后的细节再来补充

from base.monitoring import FCP_STATUS, StatusCode, StatusWarp
from secagg.shared.secagg_messages import ServerToClientWrapperMessage

class SecAggClientState():
	def __init__(self, sender, transition_listener, state):
		self._sender = sender
		self._transition_listener = transition_listener
		self._state = state
		self._transition_listener.Transition(self._state)
		self._fcp_terminal_state = StatusCode.FAILED_PRECONDITION

	@StatusWarp
	def Start(self):
		information = "An illegal start transition was attempted from state {}".format(self.StateName())
		return FCP_STATUS(self._fcp_terminal_state, information)

	@StatusWarp
	def HandleMessage(self, message):
		fcp_status = self._fcp_terminal_state
		message_content_case = message.message_content_case()
		if message_content_case == ServerToClientWrapperMessage.MESSAGE_CONTENT_NOT_SET:
			information = "Client received a message of unknown type but was in state {}".format(self.StateName())
		else:
			information = "Client received a message of type {} but was in state {}".format(message_content_case, self.StateName())
		return FCP_STATUS(fcp_status, information)

	@StatusWarp
	def SetInput(self, input_map):
		information = "An illegal input transition was attempted from state {}".format(self.StateName())
		return FCP_STATUS(self._fcp_terminal_state, information)

	@StatusWarp
	def Abort(self, reason):
		information = "The client1 was already in terminal state {} but received an abort with message: {}".format(StateName(), reason)
		return FCP_STATUS(self._fcp_terminal_state, information)

	def IsAborted(self):
		return False;

	def IsCompletedSuccessfully(self):
		return False

	@StatusWarp
	def ErrorMessage(self):
		information = "Error message requested, but client1 is in state: {}".format(self.StateName())
		return FCP_STATUS(self._fcp_terminal_state, information)

	def ValidateInput(self, input_map, input_vector_specs):
		if len(input_map) != len(input_vector_specs):
			return False
		for vector_spec in input_vector_specs:
			input_vec = input_map.get(vector_spec.name(), None)
			if not input_vec or input_vec.modulus() != vector_spec.modulus()\
				or input_vec.num_elements() != vector_spec.length():
				return False
		return True

	def StateName(self):
		return ''

	def State(self):
		return self._state