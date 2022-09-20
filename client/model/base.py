# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-08-31 10:47:56
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-17 20:07:58

import torch

class BaseModel(torch.nn.Module):

	# 初始化函数无需参数.
	def __init__(self):
		super(BaseModel, self).__init__()

	def forward(self, x):
		pass

	@staticmethod
	# 具体的训练, 此方法会被client调用来进行训练
	def Train(model):
		pass