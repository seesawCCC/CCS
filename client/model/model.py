# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-08-31 10:52:31
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-12 00:21:58

import torch

import random
from .base import BaseModel

class DynamicNet(BaseModel):
	def __init__(self):
		N, D_in, H, D_out = 64, 1000, 100, 10
		""" 构造3个nn.Linear实例。 """
		super(DynamicNet, self).__init__()
		self.input_linear = torch.nn.Linear(D_in, H)
		self.middle_linear = torch.nn.Linear(H, H)
		self.output_linear = torch.nn.Linear(H, D_out)
	
	def forward(self, x):
		# 输入和输出层是固定的，但是中间层的个数是随机的(0,1,2)， 		# 并且中间层的参数是共享的。 		
		# 因为每次计算的计算图是动态(实时)构造的， 		# 所以我们可以使用普通的Python流程控制代码比如for循环 		# 来实现。读者可以尝试一下怎么用TensorFlow来实现。 		# 另外一点就是一个Module可以多次使用，这样就 		# 可以实现参数共享。 		
		h_relu = self.input_linear(x).clamp(min=0)
		for _ in range(random.randint(1, 3)):
			h_relu = self.middle_linear(h_relu).clamp(min=0)
			y_pred = self.output_linear(h_relu)
		return y_pred

	@staticmethod
	def train(model):
		N, D_in, H, D_out = 64, 1000, 100, 10
		x = torch.randn(N, D_in)
		y = torch.randn(N, D_out)
		criterion = torch.nn.MSELoss(size_average=False)
		optimizer = torch.optim.SGD(model.parameters(), lr=1e-4, momentum=0.9)
		y_pred = model(x)
		loss = criterion(y_pred, y)
		optimizer.zero_grad()
		loss.backward()
		optimizer.step()

