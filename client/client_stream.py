# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-08-17 17:31:35
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-02 23:57:12
import pickle, traceback, time
from collections import OrderedDict

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

	def Send(self, message, action=4):
		self._check_connect()
		unserialized_message = {'action': action, 'time': int(time.time())}
		unserialized_message['data'] = message
		# if isinstance(message, ClientToServerWrapperMessage):
		# 	unserialized_message['data'] = message.SerializeAsString()
		# else:
		# 	unserialized_message['data'] = pickle.dumps(message) 
		serialized_message = pickle.dumps(unserialized_message)
		encry_message = self._aes_gcm.Encrypt(self._enc_key, serialized_message)
		return self._network.send_to_server(encry_message)

	def Receive(self, timeout=0):
		start = int(time.time())
		server_message = None
		while not timeout or int(time.time())-start <= timeout:
			print(int(time.time())-start)
			server_message = self.receive_from_socket()
			if server_message or self._network.isOver():
				break
			time.sleep(1) 
		return server_message

	def receive_from_socket(self):
		lock = self._network.get_message_lock()
		server_message = None

		if lock.acquire(blocking=True,  timeout=2):
			try:
				receive_messages = self._network.get_receive_messages()
				for encry_message in receive_messages[::-1]:
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
								server_message.set_models(data.get('models', OrderedDict()))
								# specification: {'conv1_weight': (length, module)}
								server_message.set_specifications(data.get('specification', {}))
								server_message.set_neighboors(data.get('neighbor', []))
								server_message.set_integerization(data.get('integerization', 0))
								server_message.set_max_clients_expected(data.get('max_clients_expected', 0))
								server_message.set_minimum_surviving_clients_for_reconstruction(data.get('minimum_surviving_clients_for_reconstruction', 0))								
								self._last_receive = timestamp
							elif action == 4:
								if isinstance(data, ServerToClientWrapperMessage):
									server_message = data
									self._last_receive = timestamp
							elif action == 5:
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

	def Clear(self):
		lock = self._network.get_message_lock()
		server_message = None

		with lock:
			receive_messages = self._network.get_receive_messages()
			receive_messages.clear()


	def Close(self):
		self._network.close()

	def _check_connect(self):
		if self._network.isOver():
			raise Exception('connection to server\' communication socket has been closed')