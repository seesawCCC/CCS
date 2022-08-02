# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-29 20:02:55
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-31 00:39:45

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from base.monitoring import StatusWarp, FCP_STATUS, StatusCode, Status
from .math import RandomString
from .aes_key import AesKey

class EcdhPrivateKey():

	@staticmethod
	def LoadFromBytes(private_key_str, password):
		private_key_bytes = private_key_str.decode('ascii')
		private_key = serialization.load_pem_private_key(private_key_bytes, password)
		return EcdhPrivateKey(private_key, password)

	def __init__(self, private_key, password):
		self._private_key = private_key
		self._password = password

	def PublicKey(self):
		return EcdhPublicKey(self._private_key.public_key())

	# 返回unicode
	# 编码PEM, 格式PrivateFormat.PKCS8 
	# https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ec/?highlight=encryption_algorithm#serialization
	def AsString(self):
		seria_private_key = self._private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.BestAvailableEncryption(self._password))
		return seria_private_key.decode('ascii')

	# return bytes string
	def ComputeSharedSecret(self, other_pbk):
		shared_key = self._private_key.exchange(ec.ECDH(), other_pbk)
		derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'').derive(shared_key)
		return derived_key

class EcdhPublicKey():

	@staticmethod
	def LoadFromBytes(public_key_str):
		public_key_bytes = public_key_str.encode('ascii')
		public_key =  serialization.load_pem_public_key(public_key_bytes)
		return EcdhPublicKey(public_key)

	def __init__(self, public_key):
		if isinstance(public_key, str):
			public_key_bytes = public_key.encode('ascii')
			public_key =  serialization.load_pem_public_key(public_key_bytes)
		self._public_key = public_key

	def GetECPublicKey(self):
		return self._public_key

	def AsString(self):
		public_bytes = self._public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
		return public_bytes.decode('ascii')

	def __eq__(self, other_pk):
		return self.AsString() == other_pk.AsString()

class EcdhKeyAgreement():

	# return Status
	@staticmethod
	def CreateFromRandomKeys():
		# ecp256r1, NIST P-256
		try:
			private_key = ec.generate_private_key(ec.SECP256R1())
			result = EcdhKeyAgreement(private_key)
			status = StatusCode.OK
			message = ''
			return Status(status, result, message)
		except Exception as e:
			return FCP_STATUS(StatusCode.INTERNAL, e)

	# private_key: EcdhPrivateKey or bytes
	# return Status
	@staticmethod
	def CreateFromPrivateKey(private_key, password=''):
		try:
			if isinstance(private_key, EcdhPrivateKey):
				pass
			elif isinstance(private_key, bytes):
				private_key = serialization.load_pem_private_key(private_key, password)
			else:
				raise TypeError("private key must be ec.EllipticCurvePrivateKey or bytes")
			result = EcdhKeyAgreement(private_key)
			return FCP_STATUS(StatusCode.OK, '', result)
		except Exception as e:
			return FCP_STATUS(StatusCode.INVALID_ARGUMENT, e, None)

	# private_key: EcdhPrivateKey
	@staticmethod
	def CreateFromKeypair(private_key, public_key):
		mirror_public_key = private_key.PublicKey().AsString()
		if mirror_public_key != public_key.AsString():
			return FCP_STATUS(StatusCode.INVALID_ARGUMENT, "Invalid keypair.")

		ecdh = EcdhKeyAgreement.CreateFromPrivateKey(private_key)
		return ecdh

	def __init__(self, key):
		self._password = RandomString()
		private_key = EcdhPrivateKey(key, self._password) if not isinstance(key, EcdhPrivateKey) else key 
		self._private_key = private_key
		
	def PrivateKey(self):
		return self._private_key

	def PublicKey(self):
		return self._private_key.PublicKey()

	@StatusWarp
	def ComputeSharedSecret(self, other_key):
		other_ec_key = other_key
		if isinstance(other_key, EcdhPublicKey):
			other_ec_key = other_key.GetECPublicKey()
		elif isinstance(other_key, bytes):
			other_ec_key = serialization.load_der_public_key(other_key)
		shared_secret = self._private_key.ComputeSharedSecret(other_ec_key)
		return AesKey(shared_secret, len(shared_secret))