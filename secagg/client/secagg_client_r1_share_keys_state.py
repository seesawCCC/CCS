# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-16 19:37:18
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-28 16:38:42

from .secagg_client_r1_share_keys_base_state import SecAggClientR1ShareKeysBaseState, R1ShareKeysStateDeliveredMessage
from .secagg_client_terminal_state import SecAggClientCompletedState, SecAggClientAbortedState
from .secagg_client_r2_masked_input_coll_input_set_state import SecAggClientR2MaskedInputCollInputSetState
from .secagg_client_r2_masked_input_coll_input_not_set_state import SecAggClientR2MaskedInputCollInputNotSetState
from ..shared.aes_key import AesKey
from base.monitoring import FCP_STATUS, StatusCode, StatusWarp



class SecAggClientR1ShareKeysCommonState(SecAggClientR1ShareKeysBaseState):
	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, enc_key_agreement, \
			input_vector_specs, prng, prng_key_agreement, sender, transition_listener, prng_factory, async_abort=None):
		super().__init__(sender, transition_listener, async_abort)
		self._max_clients_expected = max_clients_expected
		self._minimum_surviving_clients_for_reconstruction = minimum_surviving_clients_for_reconstruction
		self._enc_key_agreement = enc_key_agreement
		self._input_vector_specs = input_vector_specs
		self._prng = prng
		self._prng_key_agreement = prng_key_agreement
		self._prng_factory = prng_factory
		self._self_prng_key_shares = []
		self._pairwise_prng_key_shares = []

	@StatusWarp
	def HandleMessage(self, message):
		if message.has_abort():
			if message.abort().early_success():
				return SecAggClientCompletedState(self._sender, self._transition_listener)
			else:
				reason = "Aborting because of abort message from the server."
				return SecAggClientAbortedState(reason, self._sender, self._transition_listener)
		elif not message.has_share_keys_request():
			return super().HandleMessage(message)
		#bi
		self_prng_key_buffer = [0]*AesKey.kSize
		for i in range(AesKey.kSize):
			self_prng_key_buffer[i] = self._prng.Rand8()
		self_prng_key = AesKey(self_prng_key_buffer)

		r1_delivered_message = R1ShareKeysStateDeliveredMessage(self._prng, self._self_prng_key_shares, self._pairwise_prng_key_shares)
		success = self.HandleShareKeysRequest(message.share_keys_request(), self._enc_key_agreement, self._max_clients_expected, self._minimum_surviving_clients_for_reconstruction, self._prng_key_agreement, self_prng_key, r1_delivered_message) 
		if not success:
			return self.AbortAndNotifyServer(r1_delivered_message.error_message)
		if not self.EncryptAndSendResponse(r1_delivered_message.other_client_enc_keys, self._pairwise_prng_key_shares, self._self_prng_key_shares, self._sender.get()):
			return  self.AbortAndNotifyServer(self._async_abort.Message())
		
		own_self_key_share = self._self_prng_key_shares[r1_delivered_message.client_id]
		return self._next_Rstate(r1_delivered_message, own_self_key_share, self_prng_key)

	def _next_Rstate(self, r1_delivered_message, own_self_key_share, self_prng_key):
		pass

class SecAggClientR1ShareKeysInputSetState(SecAggClientR1ShareKeysCommonState):
	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, enc_key_agreement, input_map,\
		input_vector_specs, prng, prng_key_agreement, sender, transition_listener, prng_factory, async_abort=None):
		super().__init__(max_clients_expected, minimum_surviving_clients_for_reconstruction, enc_key_agreement, \
			input_vector_specs, prng, prng_key_agreement, sender, transition_listener, prng_factory, async_abort)
		self._input_map = input_map

	def StateName(self):
		return "R1_SHARE_KEYS_INPUT_SET"

	def _next_Rstate(self, r1_delivered_message, own_self_key_share, self_prng_key):
		return SecAggClientR2MaskedInputCollInputSetState(r1_delivered_message.client_id, self._minimum_surviving_clients_for_reconstruction, r1_delivered_message.number_of_alive_clients, r1_delivered_message.number_of_clients, \
			self._input_map, self._input_vector_specs, r1_delivered_message.other_client_states, r1_delivered_message.other_client_enc_keys, r1_delivered_message.other_client_prng_keys, own_self_key_share, self_prng_key, self._sender, \
			self._transition_listener, r1_delivered_message.session_id, self._prng_factory, self._async_abort)

class SecAggClientR1ShareKeysInputNotSetState(SecAggClientR1ShareKeysCommonState):
	def __init__(self, max_clients_expected, minimum_surviving_clients_for_reconstruction, enc_key_agreement, \
			input_vector_specs, prng, prng_key_agreement, sender, transition_listener, prng_factory, async_abort=None):
		super().__init__(max_clients_expected, minimum_surviving_clients_for_reconstruction, enc_key_agreement, \
			input_vector_specs, prng, prng_key_agreement, sender, transition_listener, prng_factory, async_abort)

	@StatusWarp
	def SetInput(self, input_map):
		if not self.ValidateInput(input_map, self._input_vector_specs):
			information = "The input to SetInput does not match the InputVectorSpecification."
			return FCP_STATUS(INVALID_ARGUMENT, information)
		return SecAggClientR1ShareKeysInputSetState(self._max_clients_expected, self._minimum_surviving_clients_for_reconstruction, self._enc_key_agreement, \
			input_map, self._input_vector_specs, self._prng, self._prng_key_agreement, self._sender, self._transition_listener, self._prng_factory, self._async_abort)

	def StateName(self):
		return "R1_SHARE_KEYS_INPUT_NOT_SET"

	def _next_Rstate(self, r1_delivered_message, own_self_key_share, self_prng_key):
		return SecAggClientR2MaskedInputCollInputNotSetState(r1_delivered_message.client_id, self._minimum_surviving_clients_for_reconstruction, r1_delivered_message.number_of_alive_clients, r1_delivered_message.number_of_clients, \
			self._input_vector_specs, r1_delivered_message.other_client_states, r1_delivered_message.other_client_enc_keys, r1_delivered_message.other_client_prng_keys, own_self_key_share, self_prng_key, self._sender, \
			self._transition_listener, r1_delivered_message.session_id, self._prng_factory, self._async_abort)
