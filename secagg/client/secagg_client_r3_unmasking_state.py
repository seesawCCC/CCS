
from .secagg_client_alive_base_state import SecAggClientAliveBaseState
from .secagg_client_terminal_state import SecAggClientCompletedState, SecAggClientAbortedState
from .secagg_client_state import SecAggClientState
from .client_state import OtherClientState
from ..shared.secagg_messages import ClientToServerWrapperMessage
from base.monitoring import FCP_CHECK, StatusWarp

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
        FCP_CHECK(self.client_id >= 0, "Client id must not be negative but was {}".format(self.client_id))

    @StatusWarp
    def HandleMessage(self, message):
        if message.has_abort():
            if message.abort().early_success():
                return SecAggClientCompletedState(self._sender, self._transition_listener)
            else:
                return SecAggClientAbortedState("Aborting because of abort message from the server.", self._sender, self._transition_listener)
        elif not message.has_unmasking_request():
            return super().HandleMessage(message)
        if self._async_abort and self._async_abort.Signalled():
            return self.AbortAndNotifyServer(self._async_abort.Message())

        request = message.unmasking_request()
        dead_at_round_3_client_ids = []

        for i in request.dead_3_client_ids():
            id=i-1
            if id == self.client_id:
                return self.AbortAndNotifyServer("The received UnmaskingRequest states this client has aborted, but this client had not yet aborted.")
            elif id >= self.number_of_clients:
                return self.AbortAndNotifyServer("The received UnmaskingRequest contains a client id that does correspond to any client.")
            if self.other_client_states[id] ==  OtherClientState.kAlive:
                self.other_client_states[id] = OtherClientState.kDeadAtRound3
                number_of_alive_clients = number_of_alive_clients-1
            elif self.other_client_states[id] ==  OtherClientState.kDeadAtRound3:
                return self.AbortAndNotifyServer("The received UnmaskingRequest repeated a client more than once as a dead client.")
            elif self.other_client_states[id] == OtherClientState.kDeadAtRound1:
                pass
            elif self.other_client_states[id] == OtherClientState.kDeadAtRound2:
                pass
            else:
                return self.AbortAndNotifyServer("The received UnmaskingRequest considers a client dead in round 3 that was already considered dead.")

        if number_of_alive_clients <self.minimum_surviving_clients_for_reconstruction:
            return self.AbortAndNotifyServer("Not enough clients survived. The server should not have sent this UnmaskingRequest.")

        message_to_server = ClientToServerWrapperMessage()
        unmasking_response = message_to_server.mutable_unmasking_response()

        for i in range(self.number_of_clients):
            if self._async_abort and self._async_abort.Signalled():
                return self.AbortAndNotifyServer(self._async_abort.Message())
            if self.other_client_states[i] == OtherClientState.kAlive:
                noise_or_prf_key_shares = NoiseOrPrfKeyShare()
                noise_or_prf_key_shares.set_prf_sk_share(self.self_key_shares[i].data)
                unmasking_response.add_noise_or_prf_key_shares(noise_or_prf_key_shares)
            elif self.other_client_states[i] == OtherClientState.kDeadAtRound3:
                noise_or_prf_key_shares = NoiseOrPrfKeyShare()
                noise_or_prf_key_shares.set_noise_sk_share(self.pairwise_key_shares[i].data)
                unmasking_response.add_noise_or_prf_key_shares(noise_or_prf_key_shares)
            elif self.other_client_states[i] == OtherClientState.kDeadAtRound1:
                unmasking_response.add_noise_or_prf_key_shares(None)
            elif self.other_client_states[i] == OtherClientState.kDeadAtRound2:
                unmasking_response.add_noise_or_prf_key_shares(None)
            else:
                noise_or_prf_key_shares = NoiseOrPrfKeyShare()
                unmasking_response.add_noise_or_prf_key_shares(noise_or_prf_key_shares)

        self._sender.Send(message_to_server)
        return SecAggClientCompletedState(self._sender, self._transition_listener)


    def StateName(self):
        return "R3_UNMASKING"











