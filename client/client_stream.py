# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-08-17 17:31:35
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-08-18 20:10:23
import pickle, traceback, time

from .network import Network
from secagg.shared.aes_key import AesKey
from secagg.shared.aes_gcm_encryption import AesGcmEncryption
from secagg.shared.secagg_messages import ClientToServerWrapperMessage, ModelDistributedMessage, ServerToClientWrapperMessage, SecaggStart

class TaskOver():
	def __init__(self, message):
		self.message = message


class ClientStream():

	def __init__(self, network, enc_key=b''):
		self._network = network
		self._enc_key = AesKey(enc_key)
		self._aes_gcm = AesGcmEncryption()
		self._last_receive = int(time.time())

	def SendHello(self):
		message = {'action': 2, 'user_id': self._network.get_client_id()}
		return self.Send(message)

	def Send(self, message):
		serialized_message = b''
		if isinstance(message, ClientToServerWrapperMessage):
			serialized_message = message.SerializeAsString()
		else:
			serialized_message = pickle.dumps(message) 
		encry_message = self._aes_gcm.Encrypt(self._enc_key, serialized_message)
		return self._network.send_to_server(encry_message)

	def Receive(self, timeout=0):
		start = int(time.time())
		server_message = None
		while int(time.time())-start <= timeout:
			print(int(time.time())-start)
			server_message = self.receive_from_socket()
			if server_message:
				break
			time.sleep(1)
		return server_message

	def receive_from_socket(self):
		lock = self._network.get_message_lock()
		server_message = None

		if lock.acquire(blocking=True,  timeout=2):
			try:
				receive_messages = self._network.get_receive_messages()
				for encry_message in receive_messages:
					try:
						decry_message = self._aes_gcm.Decrypt(self._enc_key, encry_message)
						message = pickle.loads(decry_message)
						print(message)
					except Exception as e:
						traceback.print_exc()
					else:
						action = message.get('action', 0)
						timestamp = message.get('time', 0)
						data = message.get('data', None)
						if timestamp > self._last_receive and action > 0 and data:
							if action == 3:
								server_message = ModelDistributedMessage()
								server_message.set_models(data.get('models', {}))
								server_message.set_specifications(data.get('specification', {}))
								server_message.set_neighboors(data.get('neighbor', []))
								self._last_receive = timestamp
							elif action == 4:
								if data:
									print(data)
									server_message = SecaggStart()
									self._last_receive = timestamp
							elif action == 5 or action == 6:
								if isinstance(data, ServerToClientWrapperMessage):
									server_message = data
									self._last_receive = timestamp
							elif action == 7:
								server_message = TaskOver(data)
					if server_message:
						break
				receive_messages.clear()
			except Exception as e:
				traceback.print_exc()
				server_message = None
			finally:
				lock.release()

		return server_message

	def Close(self):
		self._network.close()





			