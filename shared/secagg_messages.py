# -*- coding: utf-8 -*-
# @Time : 2022/7/26 19:02
# @Author : LRX
# @Site : 
# @File : secagg_messages.py
# @Software: PyCharm

# 重写secagg_messages.proto

class ClientToServerWrapperMessage:
    def __init__(self):
        # 对象
        self._abort = None
        self._advertise_keys = None
        self._share_keys_response = None
        self._masked_input_response = None
        self._unmasking_response = None

    def get_abort(self):
        return self._abort

    def set_abort(self,abort):
        self._abort = abort

    def mutable_abort(self):
        return self.get_abort() if self._abort else AbortMessage()

    def get_advertise_keys(self):
        return self._advertise_keys

    def seta_advertise_keys(self,advertise_keys):
        self._advertise_keys = advertise_keys

    def mutable_advertise_keys(self):
        return self.get_advertise_keys() if self._advertise_keys else AdvertiseKeys()

    def get_share_keys_response(self):
        return self._share_keys_response

    def set_share_keys_response(self,share_keys_response):
        self._share_keys_response = share_keys_response

    def mutable_share_keys_response(self):
        return self.get_share_keys_response() if self._share_keys_response else ShareKeysResponse()

    def get_masked_input_response(self):
        return self._masked_input_response

    def set_masked_input_response(self,masked_input_response):
        self._masked_input_response = masked_input_response

    def mutable_masked_input_response(self):
        return self.get_masked_input_response() if self._masked_input_response else MaskedInputCollectionResponse()

    def get_unmasking_response(self):
        return self._unmasking_response

    def set_unmasking_response(self,unmasking_response):
        self._unmasking_response = unmasking_response

    def mutable_unmasking_response(self):
        return self.get_unmasking_response() if self._unmasking_response else UnmaskingResponse()



class ServerToClientWrapperMessage:
    def __init__(self):
        # 对象
        self._abort = None
        self._share_keys_request = None
        self._masked_input_request = None
        self._unmasking_request = None

    def get_abort(self):
        return self._abort

    def set_abort(self, abort):
        self._abort = abort

    def mutable_abort(self):
        return self.get_abort() if self._abort else AbortMessage()

    def get_share_keys_request(self):
        return self._share_keys_request

    def set_share_keys_request(self, share_keys_request):
        self._share_keys_request = share_keys_request

    def mutable_share_keys_request(self):
        return self.get_share_keys_request() if self._share_keys_request else ShareKeysRequest()

    def get_masked_input_request(self):
        return self._masked_input_request

    def set_masked_input_request(self, masked_input_request):
        self._masked_input_request = masked_input_request

    def mutable_masked_input_request(self):
        return self._masked_input_request if self._masked_input_request else MaskedInputCollectionRequest()

    def get_unmasking_request(self):
        return self._unmasking_request

    def set_unmasking_request(self, unmasking_request):
        self._unmasking_request = unmasking_request

    def mutable_unmasking_request(self):
        return self.get_unmasking_request() if self._unmasking_request else UnmaskingRequest()

class AbortMessage:
    def __init__(self):
        self._diagnostic_info = " "
        self._early_success = True

    def get_diagnostic_info(self):
        return self._diagnostic_info

    def set_diagnostic_info(self,diagnostic_info):
        self._diagnostic_info = diagnostic_info

    def get_early_success(self):
        return self._early_success

    def set_early_success(self,early_success):
        self._early_success = early_success


class AdvertiseKeys:
    def __init__(self):
        # 对象
        self._pair_of_public_keys = None

    def get_pair_of_public_keys(self):
        return self._pair_of_public_keys

    def set_pair_of_public_keys(self, pair_of_public_keys):
        self._pair_of_public_keys = pair_of_public_keys

    def mutable_pair_of_public_keys(self):
        return self.get_pair_of_public_keys() if self._pair_of_public_keys else PairOfPublicKeys()

class PairOfPublicKeys:
    def __init__(self):
        #bytes类型 无符号的一个字节
        self._noise_pk = 0
        self._enc_pk = 0

    def get_noise_pk(self):
        return self._noise_pk

    def set_noise_pk(self, noise_pk):
        self._noise_pk = noise_pk

    def get_enc_pk(self):
        return self._enc_pk

    def set_enc_pk(self, enc_pk):
        self._enc_pk = enc_pk

class ShareKeysRequest:
    def __init__(self):
        self._pairs_of_public_keys = None # 对象
        self._sec_agg_execution_logging_id = 0
        self._extra_data = 0 #类型任意
        self._session_id = 0

    def get_pairs_of_public_keys(self):
        return self._pairs_of_public_keys

    def set_pairs_of_public_keys(self, pairs_of_public_keys):
        self._pairs_of_public_keys = pairs_of_public_keys

    def mutable_pairs_of_public_keys(self):
        return self.get_pairs_of_public_keys() if self._pairs_of_public_keys else PairOfPublicKeys()

    def get_sec_agg_execution_logging_id(self):
        return self._sec_agg_execution_logging_id

    def set_sec_agg_execution_logging_id(self, sec_agg_execution_logging_id):
        self._sec_agg_execution_logging_id = sec_agg_execution_logging_id

    def get_extra_data(self):
        return self._extra_data

    def set_extra_data(self, extra_data):
        self._extra_data = extra_data

    def get_session_id(self):
        return self._session_id

    def set_session_id(self, session_id):
        self._session_id = session_id

class ShareKeysResponse:
    def __init__(self):
        self._encrypted_key_shares = 0

    def get_encrypted_key_shares(self):
        return self._encrypted_key_shares

    def set_encrypted_key_shares(self, encrypted_key_shares):
        self._encrypted_key_shares = encrypted_key_shares


class PairOfKeyShares:
    def __init__(self):
        self._noise_sk_share = 0
        self._prf_sk_share = 0

    def get_noise_sk_share(self):
        return self._noise_sk_share

    def set_noise_sk_share(self, noise_sk_share):
        self._noise_sk_share = noise_sk_share

    def get_prf_sk_share(self):
        return self._prf_sk_share

    def set_prf_sk_share(self, prf_sk_share):
        self._prf_sk_share = prf_sk_share


class MaskedInputCollectionRequest:
    def __init__(self):
        self._encrypted_key_shares = 0

    def get_encrypted_key_shares(self):
        return self._encrypted_key_shares

    def set_encrypted_key_shares(self, encrypted_key_shares):
        self._encrypted_key_shares = encrypted_key_shares


class MaskedInputCollectionResponse:
    def __init__(self):
        #map<string, MaskedInputVector> vectors
        self._vectors = {}

    def get_vectors(self):
        return self._vectors

    def set_vectors(self, vectors):
        self._vectors = vectors


class MaskedInputVector:
    def __init__(self):
        self._encoded_vector = 0
        self._extra_data = 0

    def get_encoded_vector(self):
        return self._encoded_vector

    def set_encoded_vector(self, encoded_vector):
        self._encoded_vector = encoded_vector

    def get_extra_data(self):
        return self._extra_data

    def set_extra_data(self, extra_data):
        self._extra_data = extra_data

class UnmaskingRequest:
    def __init__(self):
        self._dead_3_client_ids = 0

    def get_dead_3_client_ids(self):
        return self._dead_3_client_ids

    def set_dead_3_client_ids(self, dead_3_client_ids):
        self._dead_3_client_ids = dead_3_client_ids


class UnmaskingResponse:
    def __init__(self):
        self._noise_or_prf_key_shares = None

    def get_noise_or_prf_key_shares(self):
        return self._noise_or_prf_key_shares

    def set_noise_or_prf_key_shares(self, noise_or_prf_key_shares):
        self._noise_or_prf_key_shares = noise_or_prf_key_shares

    def mutable_noise_or_prf_key_shares(self):
        return self.get_noise_or_prf_key_shares() if self._noise_or_prf_key_shares else NoiseOrPrfKeyShare()


class NoiseOrPrfKeyShare:
    def __init__(self):
        self._noise_sk_share = 0
        self._prf_sk_share = 0

    def get_noise_sk_share(self):
        return self._noise_sk_share

    def set_noise_sk_share(self, noise_sk_share):
        self._noise_sk_share = noise_sk_share

    def get_prf_sk_share(self):
        return self._prf_sk_share

    def set_prf_sk_share(self, prf_sk_share):
        self._prf_sk_share = prf_sk_share








