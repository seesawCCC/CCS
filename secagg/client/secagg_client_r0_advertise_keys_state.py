# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-11 21:21:18
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-28 16:26:33

from .secagg_client_alive_base_state import SecAggClientAliveBaseState
from .secagg_client_terminal_state import SecAggClientCompletedState, SecAggClientAbortedState
from .secagg_client_r1_share_keys_state import SecAggClientR1ShareKeysInputNotSetState, SecAggClientR1ShareKeysInputSetState
from .client_state import ClientState
from ..shared.ecdh_key_agreement import EcdhKeyAgreement
from ..shared.secagg_messages import ClientToServerWrapperMessage
from base.monitoring import StatusWarp, FCP_STATUS, StatusCode

# 有关返回的StatusOr<T>可能会自建一个类来处理

class SecAggClientR0AdvertiseKeysBaseState(SecAggClientAliveBaseState):
	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, input_vector_specs,\
				prng, sender, transition_listener, prng_factory, async_abort = None):
		super().__init__(sender, transition_listener, ClientState.R0_ADVERTISE_KEYS, async_abort)
		self._max_clients_expected = max_clients_expected
		self._minimum_surviving_clients_for_reconstruction = minimum_surviving_clients_for_reconstruction
		self._input_vector_specs = input_vector_specs
		self._prng = prng
		self._prng_factory = prng_factory

	@StatusWarp
	def Start(self):
		enc_key_agreement = EcdhKeyAgreement.CreateFromRandomKeys().value()
		prng_key_agreement = EcdhKeyAgreement.CreateFromRandomKeys().value()
		message = ClientToServerWrapperMessage()
		public_keys = message.mutable_advertise_keys().mutable_pair_of_public_keys()
		public_keys.set_enc_pk(enc_key_agreement.PublicKey().AsString())
		public_keys.set_noise_pk(prng_key_agreement.PublicKey().AsString())
		self._sender.Send(message)
		return self._next_Rstate()

	@StatusWarp
	def HandleMessage(self, message):
		if message.has_abort():
			if message.abort().early_success():
				return SecAggClientCompletedState(self._sender, self._transition_listener)
			else:
				return SecAggClientAbortedState("Aborting because of abort message from the server.", self._sender, self._transition_listener)
		else:
			return super().HandleMessage(message)

	def _next_Rstate(self, enc_key_agreement, prng_key_agreement):
		return None

class SecAggClientR0AdvertiseKeysInputSetState(SecAggClientR0AdvertiseKeysBaseState):
	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, input_map, input_vector_specs,\
				prng, sender, transition_listener, prng_factory, async_abort = None):
		super().__init__(max_clients_expected, minimum_surviving_clients_for_reconstruction, input_vector_specs,\
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
		super().__init__(max_clients_expected, minimum_surviving_clients_for_reconstruction, input_vector_specs,\
				prng, sender, transition_listener, prng_factory, async_abort)

	def _next_Rstate(self, enc_key_agreement, prng_key_agreement):
		return SecAggClientR1ShareKeysInputNotSetState(self._max_clients_expected, self._minimum_surviving_clients_for_reconstruction,\
					enc_key_agreement, self._input_map, self._input_vector_specs, self._prng, prng_key_agreement, self._sender, self._transition_listener, self._prng_factory, self._async_abort)

	@StatusWarp
	def SetInput(self, input_map):
		if not self.ValidateInput(input_map, self._input_vector_specs):
			# FCP_STATUS的具体细节到时再实现
			information = "The input to SetInput does not match the InputVectorSpecification."
			return FCP_STATUS(StatusCode.INVALID_ARGUMENT, information)
		return SecAggClientR0AdvertiseKeysInputSetState(self._max_clients_expected, self._minimum_surviving_clients_for_reconstruction, input_map,\
			self._input_vector_specs, self._prng, self._sender, self._transition_listener, self._prng_factory, self._async_abort)

	def StateName(self):
		return "R0_ADVERTISE_KEYS_INPUT_NOT_SET"