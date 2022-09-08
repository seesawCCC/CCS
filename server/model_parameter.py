# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-09-04 21:14:52
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-07 17:26:04

import torch
import ctypes
import traceback
from functools import reduce

from secagg.shared.input_vector_specification import InputVectorSpecification

class ModelParameter():

	def __init__(self):
		self._model_state_dict = None
		self._specifications = []
		self._integerization = 0

	# 从model.dat中提取初始模型参数
	# modulus设置在配置文件里
	# integerization: 10^x次方，保留n位小数，在配置文件中设置
	# 同时设置对应的input_vector_specification列表
	def load(self, path, modulus, integerization):
		self._model_state_dict = torch.load(path)
		self._specifications.clear()
		self._integerization = integerization
		for name in self._model_state_dict:
			length = reduce(lambda x,y: x*y, self._model_state_dict[name].size())
			specification = InputVectorSpecification(name, length, modulus)
			self._specifications.append(specification)

	def get_model_parameter(self):
		return self._model_state_dict

	def get_specifications(self):
		return self._specifications

	def get_integerization(self):
		return self._integerization

	# 在每轮训练的最后阶段调用，存储每轮训练后更新的模型参数
	def set_model_parameter(self, input_map):
		for param_name in self._model_state_dict:
			try:
				recv_secagg_vector = input_map[param_name]
				size = self._model_state_dict[param_name].size()
				un_recv_unpack_list = recv_secagg_vector.GetAsUint64Vector()
				recv_unpack_list = list(map(lambda x: ctypes.c_long(x).value/self._integerization, un_recv_unpack_list)) 
				recv_tensor = torch.Tensor(recv_unpack_list).view(*size)
				self._model_state_dict[param_name] = recv_tensor
			except Exception as e:
				traceback.print_exc()

	def save(self, path):
		torch.save(self._model_state_dict, path)



		


