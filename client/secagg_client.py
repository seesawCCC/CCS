# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-11 17:35:22
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-15 19:25:22

import threading

from .secagg_client_r0_advertise_keys_state import SecAggClientR0AdvertiseKeysInputNotSetState

class SecAggClient():

	_class_lock = threading.Lock()

	def __new__(cls, *args, **kwargs):
		with cls._class_lock:
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
			if state_or_error.ok():
				self._state = state_or_error.value()
			return self._get_process_state(state_or_error)  

	def Abort(self, reason=''):
		if not reason:
			return self.Abort("unknown reason")
		self._async_abort.Abort(reason)
		with self._mu:
			if self._state.IsAborted() or self._state.IsCompletedSuccessfully():
				return FCP_STATUS(OK)
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

	def ReceiveMessage(self, incoming):
		with self._mu:
			state_or_error = self._state.ReceiveMessage(incoming)
			if state_or_error.ok():
				self._state = state_or_error.value()
				return not (self._state.IsAborted() or self._state.IsCompletedSuccessfully())
			else:
				return state_or_error.status()

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
		with self.__class__._class_lock:
			del self.__class__._instance 
			self.__class__._instance = None

	def _get_process_state(self, state_or_error):
		return state_or_error.status() if state_or_error else state_or_error



