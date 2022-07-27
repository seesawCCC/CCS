# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-08 20:18:58
# @Last Modified time: 2022-07-26 11:50:19

# 注意: FAILED_PRECONDITION以及FCP_STATUS()以后要根据模块的不同来重新构写
# 对于 FAILED_PRECONDITION以及FCP_STATUS的引用等确定了之后的细节再来补充
FAILED_PRECONDITION = 1

class SecAggClientState():
	def __init__(self, sender, transition_listener, state):
		self._sender = sender
		self._transition_listener = transition_listener
		self._state = state
		self._transition_listener.Transition(self._state)
		self._fcp_terminal_state = FAILED_PRECONDITION

	def Start(self):
		information = "An illegal start transition was attempted from state {}".format(self.StateName())
		return FCP_STATUS(self._fcp_terminal_state, information)

	def HandleMessage(self, message):
		fcp_status = self._fcp_terminal_state
		if message.message_content_case() == ServerToClientWrapperMessage.MESSAGE_CONTENT_NOT_SET:
			information = "Client received a message of unknown type but was in state {}".format(self.StateName())
		else:
			information = "Client received a message of type {} but was in state {}".format(message.message_content_case(), self.StateName())
		return FCP_STATUS(fcp_status, information)

	def SetInput(self, input_map):
		information = "An illegal input transition was attempted from state {}".format(self.StateName())
		return FCP_STATUS(self._fcp_terminal_state, information)

	def Abort(self, reason):
		information = "The client was already in terminal state {} but received an abort with message: {}".format(StateName(), reason)
		return FCP_STATUS(self._fcp_terminal_state, information)

	def IsAborted(self):
		return False;

	def IsCompletedSuccessfully(self):
		return False

	def ErrorMessage(self):
		information = "Error message requested, but client is in state {}".format(self.StateName())
		return FCP_STATUS(self._fcp_terminal_state, information)

	def ValidateInput(self, input_map, input_vector_specs):
		if input_map.size() != input_vector_specs.size():
			return False
		for vector_spec in input_vector_specs:
			input_vec = input_map.find(vector_spec.name())
			if input_vec == input_map.end() or input_vec.second.modulus() != vector_spec.modulus()\
				or  input_vec.second.num_elements() != vector_spec.length():
				return False
		return True

	def StateName(self):
		return ''

	def State(self):
		return self._state