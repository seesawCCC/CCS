# -*- coding: utf-8 -*-
# @Time : 2022/7/12 15:51
# @Author : LRX
# @Site : 
# @File : secagg_client_r2_masked_input_coll_base_state.py
# @Software: PyCharm

from .secagg_client_alive_base_state import SecAggClientAliveBaseState
from .client_state import OtherClientState, ClientState
from ..shared.secagg_vector import SecAggVector
from ..shared.map_of_masks import MapOfMasks
from ..shared.aes_gcm_encryption import AesGcmEncryption
from ..shared.secagg_messages import PairOfKeyShares, ClientToServerWrapperMessage
from ..shared.shamir_secret_sharing import ShamirShare
from base.monitoring import FCP_STATUS, FCP_CHECK
import time

class SecAggClientR2MaskedInputCollBaseState(SecAggClientAliveBaseState):
    def __init__(self, sender, transition_listener, async_abort):
        super().__init__(sender, transition_listener, ClientState.R2_MASKED_INPUT, async_abort)

    # 返回SecAggVectorMap对象
    def HandleMaskedInputCollectionRequest(self, request, client_id,input_vector_specs, minimum_surviving_clients_for_reconstruction, number_of_clients,
                                           other_client_enc_keys, other_client_prng_keys, own_self_key_share, self_prng_key,session_id,prng_factory,
                                           number_of_alive_clients,other_client_states,pairwise_key_shares,self_key_shares,error_message):
        if request.encrypted_key_shares_size() != number_of_clients:
            error_message[0] ="The number of encrypted shares sent by the server does not match the number of clients."
            return None

        # Parse the request, decrypt and store the key shares from other clients.
        # AesGcmEncryption类需要在shared文件中书写
        decryptor = AesGcmEncryption()
        plaintext = ""
        for i in range(number_of_clients):
            if self._async_abort and self._async_abort.Signalled():
                error_message[0] = self._async_abort.Message()
                return None

            if i == client_id :
                # this client1
                pairwise_key_shares.append(ShamirShare(b''))
                self_key_shares.append(own_self_key_share)
            elif other_client_states[i] != OtherClientState.kAlive:
                if len(request.encrypted_key_shares(i)) > 0:
                    # A client1 who was considered aborted sent key shares.
                    error_message[0] = "Received encrypted key shares from an aborted client1."
                    return None
                else:
                    pairwise_key_shares.append(ShamirShare(b''))
                    self_key_shares.append(ShamirShare(b''))
            elif len(request.encrypted_key_shares(i)) == 0:
                # A client1 who was considered alive dropped out. Mark it as dead.
                other_client_states[i] = OtherClientState.kDeadAtRound2
                pairwise_key_shares.append(ShamirShare(b''))
                self_key_shares.append(ShamirShare(b''))
                number_of_alive_clients = number_of_alive_clients-1
            else:
                # A living client1 sent encrypted key shares, so we decrypt and store them.
                decrypted = decryptor.Decrypt(other_client_enc_keys[i], request.encrypted_key_shares(i))
                # if decrypted.ok() is False:
                #     error_message = "Authentication of encrypted data failed."
                #     return None;
                # else:
                #     plaintext = decrypted.value()
                plaintext = decrypted
                # PairOfKeyShares pairwise_and_self_key_shares;
                pairwise_and_self_key_shares = PairOfKeyShares()
                if pairwise_and_self_key_shares.ParseFromString(plaintext) is False:
                    error_message[0] = "Unable to parse decrypted pair of key shares."
                    return None
                pairwise_key_shares.append(ShamirShare(pairwise_and_self_key_shares.noise_sk_share()))
                self_key_shares.append(ShamirShare(pairwise_and_self_key_shares.prf_sk_share()))

        if number_of_alive_clients < minimum_surviving_clients_for_reconstruction :
            error_message[0] = "There are not enough clients to complete this protocol session. Aborting."
            return None

        # std::vector<AesKey> prng_keys_to_add;
        # std::vector<AesKey> prng_keys_to_subtract;
        prng_keys_to_add = []
        prng_keys_to_subtract = []

        prng_keys_to_add.append(self_prng_key)

        for i in range(number_of_clients):
            if self._async_abort and self._async_abort.Signalled():
                error_message[0] = self._async_abort.Message()
                return None
            if i == client_id or other_client_states[i] != OtherClientState.kAlive:
                continue
            elif i < client_id:
                prng_keys_to_add.append(other_client_prng_keys[i])
            else:
                prng_keys_to_subtract.append(other_client_prng_keys[i])

        map_ = MapOfMasks(prng_keys_to_add, prng_keys_to_subtract, input_vector_specs,
               session_id, prng_factory, self._async_abort)

        if not map_:
            error_message[0] = self._async_abort.Message()
            return None
        return map_

    # 返回SecAggVector对象
    def AddSecAggVectors(self, v1, v2):
        # FCP_CHECK(v1.modulus() == v2.modulus());
        if v1.modulus() == v2.modulus():
            modulus = v1.modulus()

        vec1 = SecAggVector(v1).GetAsUint64Vector()
        vec2 = SecAggVector(v2).GetAsUint64Vector()
        # FCP_CHECK(vec1.size() == vec2.size());
        for i in range(len(vec1)):
            vec1[i] = ((vec1[i] + vec2[i]) % modulus)

        return SecAggVector(vec1, modulus)

    def SendMaskedInput(self, input_map, map_of_masks):
        # ClientToServerWrapperMessage to_send;
        to_send = ClientToServerWrapperMessage()
        # to_send = ' '
        # for (auto& pair : *input_map)
        for pair in input_map:
            # SetInput should already have guaranteed these
            # FCP_CHECK(map_of_masks->find(pair.first) != map_of_masks->end())
            # if map_of_masks.find(pair.first) != map_of_masks.end():
            mask = map_of_masks.get(pair, None)
            FCP_CHECK(mask)
            sum = self.AddSecAggVectors(input_map[pair], mask)
            # sum_vec_proto = MaskedInputVector()
            # sum_vec_proto.set_encoded_vector(sum.TakePackedBytes())
            sum_vec_proto = sum
            (to_send.mutable_masked_input_response().mutable_vectors())[pair] = sum_vec_proto;
        self._sender.Send(to_send)

        return None







