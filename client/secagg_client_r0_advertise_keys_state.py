# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-11 21:21:18
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-12 16:04:17

from .secagg_client_alive_base_state import SecAggClientAliveBaseState
from .secagg_client_terminal_state import SecAggClientCompletedState, SecAggClientAbortedState
from .secagg_client_r1_share_keys_input_not_set_state import SecAggClientR1ShareKeysInputNotSetState
from .secagg_client_r1_share_keys_input_set_state import SecAggClientR1ShareKeysInputSetState
from .client_state import ClientState
from ..shared.ecdh_key_agreement import EcdhKeyAgreement
from ..shared.cs_message import ClientToServerWrapperMessage

class SecAggClientR0AdvertiseKeysBaseState(SecAggClientAliveBaseState):
	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, input_vector_specs,\
				prng, sender, transition_listener, prng_factory, async_abort = None):
		super().__init__(sender, transition_listener, ClientState.R0_ADVERTISE_KEYS, async_abort)
		self._max_clients_expected = max_clients_expected
		self._minimum_surviving_clients_for_reconstruction = minimum_surviving_clients_for_reconstruction
		self._input_vector_specs = input_vector_specs
		self._prng = prng
		self._prng_factory = prng_factory

	def Start(self):
		enc_key_agreement = EcdhKeyAgreement.CreateFromRandomKeys().value()
		prng_key_agreement = EcdhKeyAgreement.CreateFromRandomKeys().value()
		message = ClientToServerWrapperMessage()
		public_keys = message.mutable_advertise_keys().mutable_pair_of_public_keys()
		public_keys.set_enc_pk(enc_key_agreement.PublicKey().AsString())
		public_keys.set_noise_pk(prng_key_agreement.PublicKey().AsString())
		self._sender.Send(message)
		return self._next_Rstate()

	def HandleMessage(self, message):
		if message.has_abort():
			if message.abort().early_success():
				return SecAggClientCompletedState(self._sender, self._transition_listener)
			else:
				return SecAggClientAbortedState("Aborting because of abort message from the server.", self._sender, self._transition_listener)
		else:
			return self.HandleMessage(message)

	def _next_Rstate(self, enc_key_agreement, prng_key_agreement):
		return None

class SecAggClientR0AdvertiseKeysInputSetState(SecAggClientR0AdvertiseKeysBaseState):
	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, input_map, input_vector_specs,\
				prng, sender, transition_listener, prng_factory, async_abort = None):
		super().__init__(max_clients_expected, minimum_surviving_clients_for_reconstruction, input_map, input_vector_specs,\
				prng, sender, transition_listener, prng_factory, async_abort)
		self._input_map = input_map

	def _next_Rstate(self, enc_key_agreement, prng_key_agreement):
		return SecAggClientR1ShareKeysInputSetState(self._max_clients_expected, self._minimum_surviving_clients_for_reconstruction,\
					enc_key_agreement, self._input_map, self._input_vector_specs, self._prng, prng_key_agreement, self._sender, self._transition_listener, self._prng_factory, self._async_abort)

	def StateName(self):
		return "R0_ADVERTISE_KEYS_INPUT_SET"


class SecAggClientR0AdvertiseKeysInputNotSetState(SecAggClientR0AdvertiseKeysBaseState):
	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, input_vector_specs,\
				prng, sender, transition_listener, prng_factory, async_abort):
		super().__init__(max_clients_expected, minimum_surviving_clients_for_reconstruction, input_map, input_vector_specs,\
				prng, sender, transition_listener, prng_factory, async_abort)

	def _next_Rstate(self, enc_key_agreement, prng_key_agreement):
		return SecAggClientR1ShareKeysInputNotSetState(self._max_clients_expected, self._minimum_surviving_clients_for_reconstruction,\
					enc_key_agreement, self._input_map, self._input_vector_specs, self._prng, prng_key_agreement, self._sender, self._transition_listener, self._prng_factory, self._async_abort)

	def SetInput(self, input_map):
		if not self.ValidateInput(input_map, self._input_vector_specs):
			# FCP_STATUS这一块暂且留空, 先返回一个None
			return None
		return SecAggClientR0AdvertiseKeysInputSetState(self._max_clients_expected, self._minimum_surviving_clients_for_reconstruction, input_map\
					self._input_vector_specs, self._prng, self._sender, self._transition_listener, self._prng_factory, self._async_abort)

	def StateName(self):
		return "R0_ADVERTISE_KEYS_INPUT_NOT_SET"