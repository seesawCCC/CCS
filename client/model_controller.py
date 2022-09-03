# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-08-31 13:32:27
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-02 23:11:45

import importlib
import inspect
import ctypes
from collections import OrderedDict
from .model.base import BaseModel
from secagg.shared.secagg_vector import SecAggVector

class ModelController():

	def __init__(self):
		self.__train_model_class = self.Load()
		self.__train_model = self.__train_model_class()
		self.vector_specifications = None
		self._integerization = 0

	# 从client/model目录下自动加载第一个满足条件的训练模型
	# 所有的模型都是BaseModel的一个子类u
	# 用于训练的模型需要在client/model/__init__.py下引入
	def Load(self):
		module = importlib.import_module('client.model')
		module_class = inspect.getmembers(module, inspect.isclass)
		# print(module_class)
		for class_tuple in module_class:
			class_ = class_tuple[1]
			if issubclass(class_, BaseModel):
				return class_

	def SetVectorSpecification(self, specification):
		self.vector_specifications = specification

	def SetIntegerization(self, integerization):
		self._integerization = integerization

	def SetModelParameter(self, parameter):
		if not isinstance(parameter, OrderedDict):
			return False
		try:
			self.__train_model.load_state_dict(parameter)
		except Exception as e:
			return False
		else:
			return True

	# 返回{'参数名称': SecAggVector([...])}
	# 将模型参数矩阵调整为1维列表，小数保留小数点后_integerization位，以无符号整数进行传递
	def GetModelParameter(self):
		if not self.vector_specifications:
			return None
		model_state_dict = self.__train_model.state_dict()
		print(model_state_dict['input_linear.weight'])
		input_map = {}
		for specification in self.vector_specifications:
			name = specification.name()
			modulus = specification.modulus()
			parameter_tensor = model_state_dict.get(name, None)
			parameter_list = []
			if parameter_tensor is not None:
				parameter_list = parameter_tensor.view(1,-1).tolist()[0]
				parameter_list = list(map(lambda x: ctypes.c_ulong(int(x*self._integerization)).value, parameter_list))
			secagg_vector = SecAggVector(parameter_list, modulus)
			input_map[name] = secagg_vector
		return input_map

	def Train(self):
		self.__train_model_class.train(self.__train_model)
