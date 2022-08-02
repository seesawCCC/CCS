# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-11 17:35:22
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-28 16:30:21

import threading

from .secagg_client_r0_advertise_keys_state import SecAggClientR0AdvertiseKeysInputNotSetState
from ..shared.async_abort import AsyncAbort
from base.monitoring import FCP_STATUS, StatusCode, StatusWarp

class SecAggClient():

	_class_lock = threading.Lock()

	def __new__(cls, *args, **kwargs):
		with cls._class_lock:
			if cls.__dict__.get('_instance', None):
				del cls._instance 
				cls._instance = None
			cls._instance = super(SecAggClient, cls).__new__(cls)
		return cls._instance

	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, input_vector_specs, prng,\
				sender, transition_listener, prng_factory, abort_signal_for_test):
		self._mu = threading.Lock()
		self._abort_signal = None
		self._async_abort = AsyncAbort(abort_signal_for_test if abort_signal_for_test else self._abort_signal)
		self._state = SecAggClientR0AdvertiseKeysInputNotSetState(max_clients_expected, minimum_surviving_clients_for_reconstruction,\
          				input_vector_specs, prng, sender, transition_listener, prng_factory, self._async_abort)

	def Start(self):
		with self._mu:
			state_or_error = self._state.Start()
			if state_or_error.ok():
				self._state = state_or_error.value()
			return self._get_process_state(state_or_error)  

	def Abort(self, reason=''):
		if not reason:
			return self.Abort("unknown reason")
		self._async_abort.Abort(reason)
		with self._mu:
			if self._state.IsAborted() or self._state.IsCompletedSuccessfully():
				return FCP_STATUS(StatusCode.OK)
			state_or_error = self._state.Abort(reason)
			if state_or_error.ok():
				self._state = state_or_error.value()
			return self._get_process_state(state_or_error)

	def SetInput(self, input_map):
		with self._mu:
			state_or_error = self._state.SetInput(input_map)
			if state_or_error.ok():
				self._state = state_or_error.value()
			return self._get_process_state(state_or_error)

	@StatusWarp
	def ReceiveMessage(self, incoming):
		with self._mu:
			state_or_error = self._state.HandleMessage(incoming)
			if state_or_error.ok():
				self._state = state_or_error.value()
				return not (self._state.IsAborted() or self._state.IsCompletedSuccessfully())
			else:
				return self._get_process_state(state_or_error)

	@StatusWarp
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

	def _get_process_state(self, state_or_error):
		return state_or_error.status()



