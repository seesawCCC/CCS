# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-09-07 16:43:55
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-08 17:07:40

import os, time
import pickle
import random
from .network_server import ServerSocket
from .user_pool import UserPool
from .model_parameter import ModelParameter
from secagg.shared.secagg_messages import ModelDistributedMessage, ServerToClientWrapperMessage
from secagg.shared.aes_ctr_prng_factory import AesCtrPrngFactory

class ServerController():

	def __init__(self, config):
		self._network = None
		self._config = config
		self._model_parameter = None
		self._user_pool = UserPool()

		# 加载初始模型
		self.load_init_model()

		# 启动网络服务器
		self.init_netword()

		# 提取安全聚合参数
		secagg_param = self._config['secagg']
		self._max_clients_expected = int(secagg_param['max_clients_expected'])
		self._minimum_surviving_clients_for_reconstruction = int(secagg_param['minimum_surviving_clients_for_reconstruction'])
		self._min_clients_to_start = int(secagg_param['min_clients_to_start'])
		self._secagg_max_timeout = int(secagg_param['max_timeout'])

	def init_netword(self):
		server_dict = self._config['server']
		host = server_dict['host']
		register_port = int(server_dict['register_port'])
		communication_port = int(server_dict['communication_port'])
		self._waitting_for_enough_clients_timeout = server_dict['waitting_for_enough_clients_timeout']
		self._network = ServerSocket(host, communication_port, register_port)
		self._network.listen()

	def load_init_model(self):
		model_dict = self._config['model']
		model_path = model_dict['path']
		model_path = model_path if os.path.isabs(model_path) else '\\'.join((os.path.dirname(__file__), model_path))
		modulus = int(model_dict['modulus'])
		integerization = int(model_dict['integerization'])
		self._model_max_timeout = int(model_dict['max_timeout'])
		self._model_train_round = int(model_dict['train_rounds'])
		self._model_parameter = ModelParameter() 
		self._model_parameter.load(model_path, modulus, integerization)

	def deliever_model(self, user_list):
		model_parameter = self._model_parameter.get_model_parameter()
		specification = self._model_parameter.get_specifications()
		integerization = self._model_parameter.get_integerization()

		distributed_message = ModelDistributedMessage()
		distributed_message.set_models(model_parameter)
		distributed_message.set_specifications(specification)
		distributed_message.set_integerization(integerization)
		distributed_message.set_max_clients_expected(self._max_clients_expected)
		distributed_message.set_minimum_surviving_clients_for_reconstruction(self._minimum_surviving_clients_for_reconstruction)

		message = {'action': 3, 'time': int(time.time()), 'data': distributed_message}
		need_pop = []
		for i in range(len(user_list)):
			user_callback = user_list[i]
			user = self._user_pool.GetUserByAddress(user_callback)
			enc_key = user['enc_key']
			encry_message = self._network.aes.Encrypt(enc_key, pickle.dumps(message))
			socket = self._user_pool.GetSocket(user_callback)
			try:
				socket.sendall(encry_message)
			except Exception as e:
				need_pop.append(i)

		success_user_list = user_list
		if need_pop:
			success_user_list = []
			for i in user_list:
				if i not in need_pop:
					success_user_list.append(user_list[i])
		return success_user_list

	# user_list是成功分发了模型参数的用户列表
	def secagg(self, init_user_list):
		# 模型参数分发之后, 根据user_list确定UserAddress
		# 等待最大超时时间或者人数或者不超过_max_clients_expected的用户
		# 用户池状态已经被刷新了

		# 用户池的消息每轮开始时都会清空
		client_message = self.wait_for_secagg(init_user_list, self._secagg_max_timeout)
		user_address = list(client_message.keys())
		self.checkout_user_list(init_user_list, user_address)
		try: 
			self._network.server_r0(client_message, self._minimum_surviving_clients_for_reconstruction, user_address)

			client_message = self.wait_for_secagg(init_user_list)
			user_address_1 = list(client_message.keys())
			self.checkout_user_list(user_address, user_address_1)
			self._network.server_r1(client_message, self._minimum_surviving_clients_for_reconstruction, user_address, user_address_1)

			client_message = self.wait_for_secagg(init_user_list)
			user_address_2 = list(client_message.keys())
			self.checkout_user_list(user_address_1, user_address_2)
			self._network.server_r2(client_message, self._minimum_surviving_clients_for_reconstruction, user_address, user_address_1, user_address_2)

			client_message = self.wait_for_secagg(init_user_list)
			user_address_3 = list(client_message.keys())			
			input_vector_specs = self._model_parameter.get_specifications()
			prng_factory = AesCtrPrngFactory()
			sum_vector = self._network.server_r3(client_message, self._minimum_surviving_clients_for_reconstruction, user_address, user_address_1, user_address_2, user_address_3, input_vector_specs, prng_factory, None)

			return sum_vector
		except Exception as e: 
			print(e)
			return {}

	def checkout_user_list(self, user_list, last_user_list):
		for user in user_list:
			if user not in last_user_list:
				self.send_abort(user)
				self._user_pool.ChangeStatus(user, 0)

	def send_abort(self, user):
		abort = ServerToClientWrapperMessage()
		abort.mutable_abort().set_early_success(False)
		message = {'action': 4, 'time': int(time.time()), 'data': abort}
		self._send_to_socket(message, user)

	def send_over(self, user_list, information=''):
		message = {'action': 5, 'time': int(time.time()), 'data': information}
		for user in user_list:
			self._send_to_socket(message, user)

	def refresh_user_pool(self):
		all_user = self._user_pool.GetAllUserAddress()
		for user in all_user:
			self._user_pool.ChangeStatus(user, 1)

	def _send_to_socket(self, message, user):
		user_info = self._user_pool.GetUserByAddress(user)
		if user_info:
			socket = user_info['socket']
			enc_key = user_info['enc_key']
			encry_message = self._network.aes.Encrypt(enc_key, pickle.dumps(message))
			socket.sendall(encry_message)


	# 等待最大时间或者user_list的用户都已经发送了数据
	# 返回: client_message: {'127.0.0.1:123': [b'xxx']}
	def wait_for_secagg(self, user_list, max_timeout):
		user_num = len(user_list)
		user_sum = 0
		curtime = int(time.time())
		client_message = {}
		while user_sum < user_num and int(time.time())-curtime<max_timeout:
			for user in user_list:
				messages = self.client_message.get(user, [])
				if messages:
					client_message[user] = [messages.pop(0)]
					user_sum += 1
			time.sleep(1) 
		return client_message 


	def run(self):
		for i in range(self._model_train_round):
			curtime = int(time.time())
			init_user_list = self._user_pool.GetAllUserAddress()
			while int(time.time())-curtime < self._waitting_for_enough_clients_timeout and len(init_user_list) < self._min_clients_to_start:
				time.sleep(1)
			if len(init_user_list) < self._min_clients_to_start:
				print('no enough clients, server over')
				return False
			if len(init_user_list) > self._max_clients_expected:
				init_user_list = random.sample(init_user_list, self._max_clients_expected)
			self.refresh_user_pool()
			init_user_list = self.deliever_model(init_user_list)
			sum_vector = self.secagg(init_user_list)
			if not sum_vector:
				print(r'secagg failed, get a {}')
				break
			self._model_parameter.set_model_parameter(sum_vector)

		self.send_over(self._user_pool.GetAllUserAddress(), 'train over')

		model_dict = self._config['model']
		model_save_path = model_dict['save_path']
		model_save_path = model_save_path if os.path.isabs(model_save_path) else '\\'.join((os.path.dirname(__file__), model_save_path))
		self._model_parameter.save(model_save_path)

		

