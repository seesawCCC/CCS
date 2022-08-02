# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-29 18:14:46
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-29 22:13:07

import hmac, hashlib, base64
from .math import IntToByteString
from base.monitoring import FCP_CHECK

kSha256Length = 32

class SessionId():
	def __init__(self, data):
		self.data = data

# request: ShareKeysRequest 
# return SessionId
def ComputeSessionId(request):
	hsobj = hashlib.sha256()
	for keys in request.pairs_of_public_keys():
		noise_pk_size = len(keys.noise_pk())
		noise_pk_size_data = IntToByteString(noise_pk_size)
		enc_pk_size = len(keys.enc_pk())
		enc_pk_size_data = IntToByteString(enc_pk_size)
		hsobj.update(noise_pk_size_data)
		hsobj.update(enc_pk_size_data)
	session_id = hsobj.hexdigest()
	FCP_CHECK(len(session_id) >= kSha256Length)
	return SessionId(session_id[:kSha256Length])