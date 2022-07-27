# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-11 17:35:22
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-26 12:20:43

import threading

from .secagg_client_r0_advertise_keys_state import SecAggClientR0AdvertiseKeysInputNotSetState
from ..shared.async_abort import AsyncAbort

class SecAggClient():

	_class_lock = threading.Lock()

	def __new__(cls, *args, **kwargs):
		with cls._class_lock:
			if cls.__dict__.get('_instance', None):
				cls.Close()
			cls._instance = super(SecAggClient, cls).__new__(cls)
		return cls._instance

	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, input_vector_specs, prng,\
				sender, transition_listener, prng_factory, abort_signal_for_test=None):
		self._mu = threading.Lock()
		self._abort_signal = None
		self._async_abort = AsyncAbort(abort_signal_for_test if abort_signal_for_test else self._abort_signal)
		self._state = SecAggClientR0AdvertiseKeysInputNotSetState(max_clients_expected, minimum_surviving_clients_for_reconstruction,\
          				input_vector_specs, prng, sender, transition_listener, prng_factory, self._async_abort)

	def Start(self):
		with self._mu:
			try:
				state_or_error = self._state.Start()
			except Exception as e:
				state_or_error = None
			finally:
				self._state = state_or_error
			return self._get_process_state(state_or_error)  

	def Abort(self, reason=''):
		if not reason:
			return self.Abort("unknown reason")
		self._async_abort.Abort(reason)
		with self._mu:
			if self._state.IsAborted() or self._state.IsCompletedSuccessfully():
				return FCP_STATUS(OK)
			try:
				state_or_error = self._state.Abort(reason)
			except Exception as e:
				state_or_error = None
			finally:
				self._state = state_or_error
			return self._get_process_state(state_or_error)

	def SetInput(self, input_map):
		with self._mu:
			try:
				state_or_error = self._state.SetInput(input_map)
			except Exception as e:
				state_or_error = None
			finally:
				self._state = state_or_error
			return self._get_process_state(state_or_error)

	def ReceiveMessage(self, incoming):
		with self._mu:
			try:
				state_or_error = self._state.ReceiveMessage(incoming)
				self._state = state_or_error
				return not (self._state.IsAborted() or self._state.IsCompletedSuccessfully())
			except Exception as e:
				state_or_error = None
				return state_or_error

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

	@classmethod
	def Close(cls):
		with cls._class_lock:
			del cls._instance 
			cls._instance = None

	def _get_process_state(self, state_or_error):
		return state_or_error



