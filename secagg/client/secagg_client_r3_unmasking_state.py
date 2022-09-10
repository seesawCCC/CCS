from .secagg_client_alive_base_state import SecAggClientAliveBaseState
from .secagg_client_terminal_state import SecAggClientCompletedState
from .secagg_client_terminal_state import SecAggClientAbortedState
from .secagg_client_state import SecAggClientState
from .client_state import OtherClientState
from ..shared.secagg_messages import ClientToServerWrapperMessage,UnmaskingResponse

class SecAggClientR3UnmaskingState(SecAggClientAliveBaseState):
    def __init__(self, client_id, number_of_alive_clients, sender, minimum_surviving_clients_for_reconstruction, number_of_clients, other_client_states, pairwise_key_shares, self_key_shares, transition_listener, async_abort):
        super().__init__(sender, transition_listener, async_abort)
        self.client_id = client_id
        self.number_of_alive_clients = number_of_alive_clients
        self.minimum_surviving_clients_for_reconstruction = minimum_surviving_clients_for_reconstruction
        self.number_of_clients = number_of_clients
        self.other_client_states = other_client_states
        self.pairwise_key_shares = pairwise_key_shares
        self.self_key_shares = self_key_shares
        if self.client_id >=0:
            print("Client id must not be negative but was "+client_id)


    def HandleMessage(self, message):
        if message.has_abort():
            if message.abort().early_success():
                return SecAggClientCompletedState(self.sender, self.transition_listener)
            else:
                return SecAggClientAbortedState("Aborting because of abort message from the server.", self.sender, self.transition_listener)
        elif message.has_unmasking_request() !=True:
            return SecAggClientState.HandleMessage(message)
        if self.async_abort and self.async_abort.Signalled():
            return SecAggClientAliveBaseState.AbortAndNotifyServer(self.async_abort.Message())

        request = message.unmasking_request()
        dead_at_round_3_client_ids = ''

        for i in request.dead_3_client_ids():
            id=i-1
            if id == self.client_id:
                return SecAggClientAliveBaseState.AbortAndNotifyServer(
                    "The received UnmaskingRequest states this client1 has aborted, but this client1 had not yet aborted.")
            elif id >= self.number_of_clients:
                return SecAggClientAliveBaseState.AbortAndNotifyServer(
                    "The received UnmaskingRequest contains a client1 id that does correspond to any client1.")
            if self.other_client_states[id] ==  OtherClientState.kAlive:
                self.other_client_states[id] = OtherClientState.kDeadAtRound3
                number_of_alive_clients = number_of_alive_clients-1
            elif self.other_client_states[id] ==  OtherClientState.kDeadAtRound3:
                return SecAggClientAliveBaseState.AbortAndNotifyServer(
                    "The received UnmaskingRequest repeated a client1 more than once as a dead client1.")
            elif self.other_client_states[id] == OtherClientState.kDeadAtRound1:
                pass
            elif self.other_client_states[id] == OtherClientState.kDeadAtRound2:
                pass
            else:
                return SecAggClientAliveBaseState.AbortAndNotifyServer(
                    "The received UnmaskingRequest considers a client1 dead in round 3 that was already considered dead.");

        if number_of_alive_clients <self.minimum_surviving_clients_for_reconstruction:
            return SecAggClientAliveBaseState.AbortAndNotifyServer(
                "Not enough clients survived. The server should not have sent this UnmaskingRequest.")

        message_to_server = ClientToServerWrapperMessage()
        unmasking_response = UnmaskingResponse()

        for i in range(self.number_of_clients):
            if self.async_abort and self.async_abort.Signalled():
                return SecAggClientAliveBaseState.AbortAndNotifyServer(self.async_abort.Message())
            if self.other_client_states[i] == OtherClientState.kAlive:
                unmasking_response.add_noise_or_prf_key_shares().set_prf_sk_share(self.self_key_shares[i].data)
            elif self.other_client_states[i] == OtherClientState.kDeadAtRound3:
                unmasking_response.add_noise_or_prf_key_shares().set_noise_sk_share(self.pairwise_key_shares[i].data)
            elif self.other_client_states[i] == OtherClientState.kDeadAtRound1:
                return 0
            elif self.other_client_states[i] == OtherClientState.kDeadAtRound2:
                return 0
            else:
                unmasking_response.add_noise_or_prf_key_shares()

        self.sender.Send(message_to_server)
        return SecAggClientCompletedState(self.sender, self.transition_listener)


    def StateName(self):
        return "R3_UNMASKING"











