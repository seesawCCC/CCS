# -*- coding: utf-8 -*-
# @Time : 2022/7/26 19:02
# @Author : LRX
# @Site : 
# @File : secagg_messages.py
# @Software: PyCharm

# 重写secagg_messages.proto
import pickle

class ClientToServerWrapperMessage:
    def __init__(self):
        # 对象
        self._abort = None
        self._advertise_keys = None
        self._share_keys_response = None
        self._masked_input_response = None
        self._unmasking_response = None

    def abort(self):
        return self._abort

    def has_abort(self):
        return bool(self._abort)

    def set_abort(self,abort):
        self._abort = abort

    def mutable_abort(self):
        if not self._abort:
            self._abort = AbortMessage()
        return self.abort()

    def advertise_keys(self):
        return self._advertise_keys

    def has_advertise_keys(self):
        return bool(self._advertise_keys)

    def set_advertise_keys(self, advertise_keys):
        self._advertise_keys = advertise_keys

    def mutable_advertise_keys(self):
        if not self._advertise_keys:
            self._advertise_keys = AdvertiseKeys()
        return self.advertise_keys()

    def share_keys_response(self):
        return self._share_keys_response

    def has_share_keys_response(self):
        return bool(self._share_keys_response)

    def set_share_keys_response(self,share_keys_response):
        self._share_keys_response = share_keys_response

    def mutable_share_keys_response(self):
        if not self._share_keys_response:
            self._share_keys_response = ShareKeysResponse()
        return self.share_keys_response()

    def masked_input_response(self):
        return self._masked_input_response

    def has_masked_input_response(self):
        return bool(self._masked_input_response)

    def set_masked_input_response(self,masked_input_response):
        self._masked_input_response = masked_input_response

    def mutable_masked_input_response(self):
        if not self._masked_input_response:
            self._masked_input_response = MaskedInputCollectionResponse()
        return self.masked_input_response()

    def unmasking_response(self):
        return self._unmasking_response

    def has_unmasking_response(self):
        return bool(self._unmasking_response)

    def set_unmasking_response(self,unmasking_response):
        self._unmasking_response = unmasking_response

    def mutable_unmasking_response(self):
        if not self._unmasking_response:
            self._unmasking_response = UnmaskingResponse()
        return self.unmasking_response()



class ServerToClientWrapperMessage:
    MESSAGE_CONTENT_NOT_SET = 'message_content_not_set'

    def __init__(self):
        # 对象
        self._abort = None
        self._share_keys_request = None
        self._masked_input_request = None
        self._unmasking_request = None

    def message_content_case(self):
        message_content_case = ServerToClientWrapperMessage.MESSAGE_CONTENT_NOT_SET
        if not (self._abort is None and self._share_keys_request is None and self._unmasking_request is None):
            message_content_case = str({'abort': self._abort, 'share_keys_request': self._share_keys_request, 'masked_input_request': self._masked_input_request, 'unmasking_request': self._unmasking_request})
        return message_content_case

    def abort(self):
        return self._abort

    def has_abort(self):
        return bool(self._abort)

    def set_abort(self, abort):
        self._abort = abort

    def mutable_abort(self):
        if not self._abort:
            self._abort = AbortMessage()
        return self.abort()

    def share_keys_request(self):
        return self._share_keys_request

    def has_share_keys_request(self):
        return bool(self._share_keys_request)

    def set_share_keys_request(self, share_keys_request):
        self._share_keys_request = share_keys_request

    def mutable_share_keys_request(self):
        if not self._share_keys_request:
            self._share_keys_request = ShareKeysRequest()
        return self.share_keys_request()

    def masked_input_request(self):
        return self._masked_input_request

    def has_masked_input_request(self):
        return bool(self._masked_input_request)

    def set_masked_input_request(self, masked_input_request):
        self._masked_input_request = masked_input_request

    def mutable_masked_input_request(self):
        if not self._masked_input_request:
            self._masked_input_request = MaskedInputCollectionRequest()
        return self._masked_input_request

    def unmasking_request(self):
        return self._unmasking_request

    def has_unmasking_request(self):
        return bool(self._unmasking_request)

    def set_unmasking_request(self, unmasking_request):
        self._unmasking_request = unmasking_request

    def mutable_unmasking_request(self):
        if not self._unmasking_request:
            self._unmasking_request = UnmaskingRequest()
        return self.unmasking_request()

class AbortMessage:
    def __init__(self):
        self._diagnostic_info = ""
        self._early_success = True

    def diagnostic_info(self):
        return self._diagnostic_info

    def set_diagnostic_info(self,diagnostic_info):
        self._diagnostic_info = diagnostic_info

    def early_success(self):
        return self._early_success

    def set_early_success(self,early_success):
        self._early_success = early_success


class AdvertiseKeys:
    def __init__(self):
        # 对象
        self._pair_of_public_keys = None

    def pair_of_public_keys(self):
        return self._pair_of_public_keys

    def has_pair_of_public_keys(self):
        return bool(self._pair_of_public_keys)

    def set_pair_of_public_keys(self, pair_of_public_keys):
        self._pair_of_public_keys = pair_of_public_keys

    def mutable_pair_of_public_keys(self):
        if not self._pair_of_public_keys:
            self._pair_of_public_keys = PairOfPublicKeys()
        return self.pair_of_public_keys()

class PairOfPublicKeys:
    def __init__(self, noise_pk=b'', enc_pk=b''):
        #str类型
        self._noise_pk = noise_pk
        self._enc_pk = enc_pk

    def noise_pk(self):
        return self._noise_pk

    def set_noise_pk(self, noise_pk):
        self._noise_pk = noise_pk

    def enc_pk(self):
        return self._enc_pk

    def set_enc_pk(self, enc_pk):
        self._enc_pk = enc_pk

class ShareKeysRequest:
    def __init__(self):
        self._pairs_of_public_keys = [] # vector
        self._sec_agg_execution_logging_id = 0
        self._extra_data = [] #类型任意
        self._session_id = 0

    def pairs_of_public_keys(self, index=-1):
        if index < 0:
            return self._pairs_of_public_keys
        else:
            return self._pairs_of_public_keys[index]

    def has_pairs_of_public_keys(self):
        return bool(self._pairs_of_public_keys)

    def set_pairs_of_public_keys(self, pairs_of_public_keys):
        self._pairs_of_public_keys = pairs_of_public_keys[:]

    def mutable_pairs_of_public_keys(self):
        return self.pairs_of_public_keys()

    def add_pairs_of_public_keys(self, item):
        self._pairs_of_public_keys.append(item)

    def sec_agg_execution_logging_id(self):
        return self._sec_agg_execution_logging_id

    def set_sec_agg_execution_logging_id(self, sec_agg_execution_logging_id):
        self._sec_agg_execution_logging_id = sec_agg_execution_logging_id

    def extra_data(self):
        return self._extra_data

    def set_extra_data(self, extra_data):
        self._extra_data = extra_data[:]

    def add_extra_data(self, item):
        self._extra_data.append(item)

    def session_id(self):
        return self._session_id

    def set_session_id(self, session_id):
        self._session_id = session_id

class ShareKeysResponse:
    def __init__(self):
        self._encrypted_key_shares = []

    def encrypted_key_shares(self, index=-1):
        if index < 0:
            return self._encrypted_key_shares
        else:
            return self._encrypted_key_shares[index]

    def encrypted_key_shares_size(self):
        return len(self._encrypted_key_shares)

    def set_encrypted_key_shares(self, encrypted_key_shares):
        self._encrypted_key_shares = encrypted_key_shares[:]

    def add_encrypted_key_shares(self, item):
        self._encrypted_key_shares.append(item)


class PairOfKeyShares:
    def __init__(self, noise_sk_share=b'', prf_sk_share=b''):
        self._noise_sk_share = noise_sk_share
        self._prf_sk_share = prf_sk_share

    def noise_sk_share(self):
        return self._noise_sk_share

    def set_noise_sk_share(self, noise_sk_share):
        self._noise_sk_share = noise_sk_share

    def prf_sk_share(self):
        return self._prf_sk_share

    def set_prf_sk_share(self, prf_sk_share):
        self._prf_sk_share = prf_sk_share

    def SerializeAsString(self):
        return pickle.dumps(self)

class MaskedInputCollectionRequest:
    def __init__(self):
        self._encrypted_key_shares = []

    def encrypted_key_shares(self, index=-1):
        if index < 0:
            return self._encrypted_key_shares
        else:
            return self._encrypted_key_shares[index]

    def encrypted_key_shares_size(self):
        return len(self._encrypted_key_shares)

    def set_encrypted_key_shares(self, encrypted_key_shares):
        self._encrypted_key_shares = encrypted_key_shares[:]

    def add_encrypted_key_shares(self, item):
        self._encrypted_key_shares.append(item)

class MaskedInputCollectionResponse:
    def __init__(self):
        #map<string, MaskedInputVector> vectors
        self._vectors = {}

    def vectors(self):
        return self._vectors

    def set_vectors(self, vectors):
        self._vectors = vectors.copy()


class MaskedInputVector:
    def __init__(self):
        self._encoded_vector = 0
        self._extra_data = []

    def encoded_vector(self):
        return self._encoded_vector

    def set_encoded_vector(self, encoded_vector):
        self._encoded_vector = encoded_vector

    def extra_data(self):
        return self._extra_data

    def set_extra_data(self, extra_data):
        self._extra_data = extra_data[:]

    def add_extra_data(self, item):
        self._extra_data.append(item)

class UnmaskingRequest:
    def __init__(self):
        self._dead_3_client_ids = []

    def dead_3_client_ids(self):
        return self._dead_3_client_ids

    def set_dead_3_client_ids(self, dead_3_client_ids):
        self._dead_3_client_ids = dead_3_client_ids[:]

    def add_dead_3_client_ids(self, item):
        self._dead_3_client_ids.append(item)


class UnmaskingResponse:
    def __init__(self):
        self._noise_or_prf_key_shares = []

    def noise_or_prf_key_shares(self):
        return self._noise_or_prf_key_shares

    def has_noise_or_prf_key_shares(self):
        return bool(self._noise_or_prf_key_shares)

    def set_noise_or_prf_key_shares(self, noise_or_prf_key_shares):
        self._noise_or_prf_key_shares = noise_or_prf_key_shares[:]

    def mutable_noise_or_prf_key_shares(self):
        return self.noise_or_prf_key_shares()

    def add_noise_or_prf_key_shares(self, item=b''):
        self._noise_or_prf_key_shares.append(item)


class NoiseOrPrfKeyShare:
    def __init__(self):
        self._noise_sk_share = 0
        self._prf_sk_share = 0

    def noise_sk_share(self):
        return self._noise_sk_share

    def set_noise_sk_share(self, noise_sk_share):
        self._noise_sk_share = noise_sk_share

    def prf_sk_share(self):
        return self._prf_sk_share

    def set_prf_sk_share(self, prf_sk_share):
        self._prf_sk_share = prf_sk_share








