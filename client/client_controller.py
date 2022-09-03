# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-09-01 16:15:48
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-03 00:32:31

import sys

from .network import Network, ServerAddr
from .client_stream import ClientStream, TaskOver
from .model_controller import ModelController

from secagg.client.secagg_client import SecAggClient
from secagg.client.state_transition_listener_interface import StateTransitionListenerInterface
from secagg.shared.aes_ctr_prng import AesCtrPrng
from secagg.shared.aes_ctr_prng_factory import AesCtrPrngFactory
from secagg.shared.math import RandomString
from secagg.shared.aes_key import AesKey
from secagg.shared.secagg_messages import ModelDistributedMessage, ServerToClientWrapperMessage
from base.monitoring import StatusWarp, FCP_STATUS, StatusCode
exit(0)
class ClientController():
	# 初始化函数中负责进行声明,
	def __init__(self, config):
		self._config = config

		self._network = None
		self._client_stream = None

		self._model_controller = ModelController()
		self._model_controller.Load()

		self._max_clients_expected = 0
		self._minimum_surviving_clients_for_reconstruction = 0
		self._secagg_client = None

	def set_network(self):
		# 设置客户端的ip与相应的端口号
		# 单机上通过命令行启动多台客户端
		# python client_main.py 127.0.0.1 12003 12004 (ip, 注册端口, 通讯端口)
		if self._network:
			return False
		if len(sys.argv) > 1:
			client_ip, register_port, communication_port = sys.argv[1:]
		else:
			client_dict = self._config['client']
			client_ip = client_dict['host']
			register_port = client_dict['register_port']
			communication_port = client_dict['communication_port']

		server_register_dict = self._config['server']
		server_addr = ServerAddr(server_register_dict['host'], server_register_dict['register_port'])
		server_public_key = server_register_dict['public_key'].encode('utf-8')

		self._network = Network(client_ip, register_port, communication_port, server_addr, server_public_key)
		enc_key = self._network.register()
		if not enc_key:
			raise Exception('register failed, get a empty enc key.')
		self._network.connect_to_server()
		self._network.listen()
		# 设置Sender
		self._client_stream = ClientStream(self._network, enc_key)

		return True

	# 模型接收阶段被调用
	# ModelDistributedMessage model_distributed_message
	def set_model_parameter(self, model_distributed_message):
		self._model_controller.SetVectorSpecification(model_distributed_message.specifications())
		self._model_controller.SetModelParameter(model_distributed_message.models())
		self._model_controller.SetIntegerization(model_distributed_message.integerization())

		self._max_clients_expected = model_distributed_message.max_clients_expected()
		self._minimum_surviving_clients_for_reconstruction = model_distributed_message.minimum_surviving_clients_for_reconstruction()

	def init_secagg_client(self, input_vector_specs, abort_signal_for_test=None):
		max_clients_expected = self._max_clients_expected
		minimum_surviving_clients_for_reconstruction = self._minimum_surviving_clients_for_reconstruction
		seed_bytes = math.RandomString(AesKey.kSize)
		seed = AesKey(seed_bytes)
		prng = AesCtrPrng(seed)
		transition_listener = StateTransitionListenerInterface()
		prng_factory = AesCtrPrngFactory()
		if self._secagg_client:
			self._secagg_client.Close()
		self._secagg_client = SecAggClient(max_clients_expected, minimum_surviving_clients_for_reconstruction, input_vector_specs, prng,\
				self._client_stream, transition_listener, prng_factory, abort_signal_for_test)

	def run(self):
		self.set_network()
		# 等待服务器发送模型参数
		while True:
			# client向服务器注册后一直等待直到服务器分发模型或者训练结束
			message = self._client_stream.Receive()
			# 训练任务结束
			if isinstance(message, TaskOver):
				self._client_stream.Close()
				if self._secagg_client:
					self._secagg_client.Close()
				break
			# 模型分发阶段
			elif isinstance(message, ModelDistributedMessage):
				self.set_model_parameter(message)
				self._model_controller.Train()
				model_parameter = self._model_controller.GetModelParameter()
			else:
				self.close()
				raise Exception("receive wrong message from server, client except to receive a ModelDistributedMessage or TaskOver")

			# 开始安全聚合
			self.init_secagg_client(message.specifications())
			result = self._secagg_client.Start()
			FCP_CHECK(result.ok())
			result = self._secagg_client.SetInput(model_parameter)
			FCP_CHECK(result.ok())
			while not self._secagg_client.IsCompletedSuccessfully() and not self._secagg_client.IsAborted():
				message = self._client_stream.Receive()
				if not isinstance(message, ServerToClientWrapperMessage):
					self._secagg_client.Abort("secagg_client receive wrong message from server")
				else:
					result = self._secagg_client.ReceiveMessage(message)
					FCP_CHECK(result.ok())
		self.close()

	def close(self):
		self._client_stream.Close()





		

