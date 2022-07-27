# -*- coding: utf-8 -*-
# @Time : 2022/7/13 10:44
# @Author : LRX
# @Site : 
# @File : secagg_client_r2_masked_input_coll_input_not_set_state.py
# @Software: PyCharm


from .secagg_client_r2_masked_input_coll_base_state import SecAggClientR2MaskedInputCollBaseState
from .secagg_client_state import SecAggClientState
from .secagg_client_terminal_state import SecAggClientCompletedState
from .secagg_client_terminal_state import SecAggClientAbortedState
from .secagg_client_alive_base_state import SecAggClientAliveBaseState
from .secagg_client_r2_masked_input_coll_waiting_for_input_state import SecAggClientR2MaskedInputCollWaitingForInputState
from .secagg_client_r2_masked_input_coll_input_set_state import SecAggClientR2MaskedInputCollInputSetState


class SecAggClientR2MaskedInputCollInputNotSetState(SecAggClientR2MaskedInputCollBaseState):
    def __init__(self, client_id, minimum_surviving_clients_for_reconstruction, number_of_alive_clients, number_of_clients,
                 input_vector_specs, other_client_states, other_client_enc_keys, other_client_prng_keys, own_self_key_share,
                 self_prng_key, sender, transition_listener, session_id, prng_factory, async_abort):
        super().__init__(sender, transition_listener, async_abort)
        self.client_id = client_id
        self.minimum_surviving_clients_for_reconstruction = minimum_surviving_clients_for_reconstruction
        self.number_of_alive_clients = number_of_alive_clients
        self.number_of_clients = number_of_clients
        self.input_vector_specs = input_vector_specs
        self.other_client_states = other_client_states
        self.other_client_enc_keys = other_client_enc_keys
        self.other_client_prng_keys = other_client_prng_keys
        self.own_self_key_share = own_self_key_share
        self.self_prng_key = self_prng_key
        self.session_id = session_id
        self.prng_factory = prng_factory
        if self.client_id >=0 :
            print("Client id must not be negative but was"+self.client_id)


    # 返回SecAggClientR2MaskedInputCollWaitingForInputState对象
    def HandleMessage(self,message):
        if message.has_abort() :
            if message.abort().early_success() :
                return SecAggClientCompletedState(self.sender,self.transition_listener)
            else:
                return SecAggClientAbortedState("Aborting because of abort message from the server.",self.sender,self.transition_listener)
        elif message.has_masked_input_request() is False:
            # Returns an error indicating that the message is of invalid type.
            return SecAggClientState.HandleMessage(message)

        request = message.masked_input_request()
        error_message = ''
        pairwise_key_shares = {}
        self_key_shares = {}
        map_of_masks = SecAggVectorMap.HandleMaskedInputCollectionRequest(request, self.client_id, self.input_vector_specs,
                                                                          self.minimum_surviving_clients_for_reconstruction, self.number_of_clients,
                                                                          self.other_client_enc_keys, self.other_client_prng_keys,
                                                                          self.own_self_key_share, self.self_prng_key, self.session_id, self.prng_factory,
                                                                          self.number_of_alive_clients, self.other_client_states.get(), pairwise_key_shares.get(), self_key_shares.get(), error_message)
        if map_of_masks is False:
            return SecAggClientAliveBaseState.AbortAndNotifyServer(error_message)

        return SecAggClientR2MaskedInputCollWaitingForInputState(self.client_id,self.minimum_surviving_clients_for_reconstruction,
                                                                 self.number_of_alive_clients, self.number_of_clients,
                                                                 self.input_vector_specs,map_of_masks,self.other_client_states,
                                                                 pairwise_key_shares,self_key_shares,self.sender,
                                                                 self.transition_listener,self.async_abort)

    def SetInput(self,input_map):
        if SecAggClientState.ValidateInput(input_map, self.input_vector_specs) is False:
            return FCP_STATUS(INVALID_ARGUMENT)
            # "The input to SetInput does not match the InputVectorSpecification."
        return SecAggClientR2MaskedInputCollInputSetState(self.client_id, self.minimum_surviving_clients_for_reconstruction, self.number_of_alive_clients,
                                                          self.number_of_clients, input_map, self.input_vector_specs, self.other_client_states,
                                                          self.other_client_enc_keys, self.other_client_prng_keys, self.own_self_key_share,
                                                          self.self_prng_key,self.sender, self.transition_listener, self.session_id, self.prng_factory, self.async_abort)

    def StateName(self):
        return "R2_MASKED_INPUT_COLL_INPUT_NOT_SET"



