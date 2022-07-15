# -*- coding: utf-8 -*-
# @Time : 2022/7/15 16:29
# @Author : LRX
# @Site : 
# @File : secagg_client_r2_masked_input_coll_waiting_for_input_state.py
# @Software: PyCharm

from .secagg_client_r2_masked_input_coll_base_state import SecAggClientR2MaskedInputCollBaseState
from .secagg_client_state import SecAggClientState
from .secagg_client_terminal_state import SecAggClientCompletedState
from .secagg_client_terminal_state import SecAggClientAbortedState
from .secagg_client_r3_unmasking_state import SecAggClientR3UnmaskingState

class SecAggClientR2MaskedInputCollWaitingForInputState(SecAggClientR2MaskedInputCollBaseState):
    def __init__(self, client_id, minimum_surviving_clients_for_reconstruction, number_of_alive_clients, number_of_clients,
                 input_vector_specs, map_of_masks, other_client_states, pairwise_key_shares, self_key_shares,
                 sender, transition_listener, async_abort):
        super().__init__(sender, transition_listener, async_abort)
        self.client_id = client_id
        self.minimum_surviving_clients_for_reconstruction = minimum_surviving_clients_for_reconstruction
        self.number_of_alive_clients = number_of_alive_clients
        self.number_of_clients = number_of_clients
        self.input_vector_specs = input_vector_specs
        self.map_of_masks = map_of_masks
        self.other_client_states = other_client_states
        self.pairwise_key_shares = pairwise_key_shares
        self.self_key_shares = self_key_shares
        if self.client_id >= 0:
            print("Client id must not be negative but was "+self.client_id)

    def HandleMessage(self,message):
        # Handle abort messages only
        if message.has_abort():
            if message.abort().early_success():
                return SecAggClientCompletedState(self.sender, self.transition_listener)
            else:
                return SecAggClientAbortedState("Aborting because of abort message from the server.",self.sender, self.transition_listener)
        else:
            # Returns an error indicating that the message is of invalid type
            return SecAggClientState.HandleMessage(message)

    def SetInput(self,input_map):
        # Only need to do 3 things: Validate input, send message to server, and
        # return the new state.
        if SecAggClientState.ValidateInput(input_map, self.input_vector_specs) is False:
            return FCP_STATUS(INVALID_ARGUMENT)
            # "The input to SetInput does not match the InputVectorSpecification."

        self.SendMaskedInput(input_map,self.map_of_masks)

        return SecAggClientR3UnmaskingState(self.client_id,self.number_of_alive_clients, self.minimum_surviving_clients_for_reconstruction,
                                            self.number_of_clients, self.other_client_states, self.pairwise_key_shares,
                                            self.self_key_shares, self.sender, self.transition_listener, self.async_abort)

    def StateName(self):
        return "R2_MASKED_INPUT_COLL_WAITING_FOR_INPUT"



