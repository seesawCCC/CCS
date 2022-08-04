# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-15 19:51:35
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-08-03 12:22:53

# 等待具体实现时再来重新修改keys.enc_pk()这方面的东西
from .client_state import ClientState, OtherClientState
from .secagg_client_alive_base_state import SecAggClientAliveBaseState
from ..shared import compute_session_id
from ..shared.secagg_messages import ClientToServerWrapperMessage, PairOfKeyShares
from ..shared.shamir_secret_sharing import ShamirSecretSharing
from ..shared.ecdh_key_agreement import EcdhPublicKey
from ..shared.aes_key import AesKey
from ..shared.aes_gcm_encryption import AesGcmEncryption

class R1ShareKeysStateDeliveredMessage():
	def __init__(self, prng, self_prng_key_shares, pairwise_prng_key_shares):
		self.client_id = 0
		self.error_message = ''
		self.number_of_alive_clients = 0
		self.number_of_clients = 0
		self.other_client_enc_keys = []
		self.other_client_prng_keys = []
		self.other_client_states = []
		self.session_id = compute_session_id.SessionId()
		self.prng = prng
		self.self_prng_key_shares = self_prng_key_shares
		self.pairwise_prng_key_shares = pairwise_prng_key_shares
		
class SecAggClientR1ShareKeysBaseState(SecAggClientAliveBaseState):
	def __init__(self, sender, transition_listener, async_abort):
		super().__init__(sender, transition_listener, ClientState.R1_SHARE_KEYS, async_abort)

	def SetUpShares(self, threshold, n, agreement_key, self_prng_key, self_prng_key_shares, pairwise_prng_key_shares):
		if not pairwise_prng_key_shares and not self_prng_key_shares:
			sharer = ShamirSecretSharing()
			pairwise_prng_key_shares.extend(sharer.Share(threshold, n, agreement_key))
			self_prng_key_shares.extend(sharer.Share(threshold, n, self_prng_key))

	# self_prng_key是bi
	def HandleShareKeysRequest(self, request, enc_key_agreement, max_clients_expected, minimum_surviving_clients_for_reconstruction, \
			prng_key_agreement, self_prng_key, r1_delivered_message):
		self._transition_listener.set_execution_session_id(request.sec_agg_execution_logging_id())
		request_public_keys_length = len(request.pairs_of_public_keys())
		if request_public_keys_length < minimum_surviving_clients_for_reconstruction:
			r1_delivered_message.error_message = "The ShareKeysRequest received does not contain enough participants."
			return False
		elif request_public_keys_length > max_clients_expected:
			r1_delivered_message.error_message = "The ShareKeysRequest received contains too many participants."
			return False
		r1_delivered_message.number_of_alive_clients = request_public_keys_length 
		r1_delivered_message.number_of_clients = request_public_keys_length
		client_id_set = False
		self.SetUpShares(minimum_surviving_clients_for_reconstruction, r1_delivered_message.number_of_clients, prng_key_agreement.PrivateKey(), self_prng_key, \
					r1_delivered_message.self_prng_key_shares, r1_delivered_message.pairwise_prng_key_shares)
		if len(request.session_id()) != compute_session_id.kSha256Length:
			r1_delivered_message.error_message = "Session ID is absent in ShareKeysRequest or has an unexpected length."
			return False
		r1_delivered_message.session_id.data = request.session_id()
		r1_delivered_message.other_client_states = [OtherClientState.kAlive] * r1_delivered_message.number_of_clients
		# 拿到两个公钥
		self_enc_public_key = enc_key_agreement.PublicKey()
		self_prng_public_key = prng_key_agreement.PublicKey()

		for i in range(r1_delivered_message.number_of_clients):
			if self._async_abort and self._async_abort.Signalled():
				r1_delivered_message.error_message = self._async_abort.Message()
				return False

			keys = request.pairs_of_public_keys(i)
			if not keys.enc_pk() or not keys.noise_pk():
				r1_delivered_message.other_client_states[i] = OtherClientState.kDeadAtRound1
				r1_delivered_message.number_of_alive_clients -= 1
				r1_delivered_message.other_client_enc_keys.append(AesKey())
				r1_delivered_message.other_client_prng_keys.append(AesKey())
			elif len(keys.enc_pk()) != EcdhPublicKey.kSize or len(keys.noise_pk()) != EcdhPublicKey.kSize:
				r1_delivered_message.error_message = "Invalid public key in request from server."
				return False
			else:
				enc_pk = EcdhPublicKey(keys.enc_pk()) 
				prng_pk = EcdhPublicKey(keys.noise_pk())
				if enc_pk == self_enc_public_key and prng_pk == self_prng_public_key:
					if client_id_set:
						r1_delivered_message.error_message = "Found this client's keys in the ShareKeysRequest twice somehow."
						return False
					r1_delivered_message.client_id = i
					client_id_set = True
					r1_delivered_message.other_client_enc_keys.append(AesKey())
					r1_delivered_message.other_client_prng_keys.append(AesKey())
				else:
					# Ki,j
					shared_enc_key = enc_key_agreement.ComputeSharedSecret(enc_pk)
					# Si,j
					shared_prng_key = prng_key_agreement.ComputeSharedSecret(prng_pk)
					if not shared_enc_key.ok() or not shared_prng_key.ok():
						r1_delivered_message.error_message =  "Invalid public key in request from server."
						return False
					r1_delivered_message.other_client_enc_keys.append(shared_enc_key.value())
					r1_delivered_message.other_client_prng_keys.append(shared_prng_key.value())
		if r1_delivered_message.number_of_alive_clients < minimum_surviving_clients_for_reconstruction:
			r1_delivered_message.error_message = "There are not enough clients to complete this protocol session!\n Aborting."
			return False
		if not client_id_set:
			r1_delivered_message.error_message = "The ShareKeysRequest sent by the server doesn't contain this client's public keys."
			return False
		return True

	def EncryptAndSendResponse(self, other_client_enc_keys, pairwise_prng_key_shares, self_prng_key_shares, sender):
		message = ClientToServerWrapperMessage()
		response = message.mutable_share_keys_response()
		encryptor = AesGcmEncryption()

		for i in range(len(other_client_enc_keys)):
			if self._async_abort and self._async_abort.Signalled():
				return False
			if not other_client_enc_keys[i].size():
				response.add_encrypted_key_shares("")
			else:
				key_shares_pair = PairOfKeyShares()
				key_shares_pair.set_noise_sk_share(pairwise_prng_key_shares[i].data)
				key_shares_pair.set_prf_sk_share(self_prng_key_shares[i].data)
				serialized_pair = key_shares_pair.SerializeAsString()
				response.add_encrypted_key_shares(encryptor.Encrypt(other_client_enc_keys[i], serialized_pair))
		sender.Send(message)
		return True
