# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-29 19:48:22
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-29 19:54:59

from .prng import SecurePrng
from random import randint

class CryptoRandPrng(SecurePrng):
	def __init__(self):
		super().__init__()

	def Rand8(self):
		return self._rand(8)

	def Rand64(self):
		return self._rand(64)

	def _rand(self, bits):
		threshold = (1<<bits)-1
		return randint(1, threshold)