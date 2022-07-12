# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-11 17:35:22
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-12 00:11:28

import threading

from .secagg_client_r0_advertise_keys_state import SecAggClientR0AdvertiseKeysInputNotSetState

class SecAggClient():

	def __new__(cls, *args, **kwargs):
		if not cls.__dict__.get('_instance', None):
			cls._instance = super(SecAggClient, cls).__new__(cls)
		return cls._instance

	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, input_vector_specs, prng,\
				sender, transition_listener, prng_factory, abort_signal_for_test):
		self._mu = threading.Lock()
		self._abort_signal = None
		self._async_abort = abort_signal_for_test if abort_signal_for_test else abort_signal_
		self._state = SecAggClientR0AdvertiseKeysInputNotSetState(max_clients_expected, minimum_surviving_clients_for_reconstruction,\
          				input_vector_specs, prng, sender, transition_listener, prng_factory, self._async_abort)

	def Start(self):
		with self._mu:
			state_or_error = self._state.Start()
			if state_or_error:
				self._state = state_or_error
			return self._get_process_state(state_or_error)  

	def Abort(self, reason=''):
		if not reason:
			return self.Abort("unknown reason")
		self._async_abort.Abort(reason)
		with self._mu:
			if self._state.IsAborted() or self._state.IsCompletedSuccessfully():
				# FCP_STATUS(OK),暂且用1来指代这个absl::StatusCode::kOk.
				return 1
			state_or_error = self._state.Abort(reason)
			if state_or_error:
				self._state = state_or_error
			return self._get_process_state(state_or_error)

	def SetInput(self, input_map):
		with self._mu:
			state_or_error = self._state.SetInput(input_map)
			if state_or_error:
				self._state = state_or_error
			return self._get_process_state(state_or_error)

	def ReceiveMessage(self, incoming):
		with self._mu:
			state_or_error = self._state.ReceiveMessage(incoming)
			if state_or_error:
				self._state = state_or_error
				return not (self._state.IsAborted() or self._state.IsCompletedSuccessfully())
			else:
				return state_or_error.State()

	def ErrorMessage(self):
		with self._mu:
			return self._state.ErrorMessage()

	def IsAborted(self):
		with self._mu:
			return self._state.IsAborted()

	def IsCompletedSuccessfully(self):
		with self._mu:
			return self._state.IsCompletedSuccessfully()		

	def State(self):
		with self._mu:
			return self._state.StateName()

	def Close(self):
		del self.__class__._instance 
		self.__class__._instance = None

	def _get_process_state(self, state_or_error):
		return state_or_error.State() if state_or_error else state_or_error



