# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-30 15:27:42
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-30 15:38:47

from base.monitoring import FCP_CHECK
from .secagg_vector import SecAggVector

class InputVectorSpecification():

	def __init__(self, name, length, modulus):
		self._name = name
		self._length = length
		self._modulus = modulus
		FCP_CHECK(self._length >=0, "Length must be >= 0, given value was {}".format(self._length))
		modulus_fail = "The specified modulus is not valid: must be > 1 and <= {}, supplied value : {}".format(SecAggVector.kMaxModulus, self._modulus)
		FCP_CHECK(self._modulus > 1 and self._modulus <= SecAggVector.kMaxModulus, modulus_fail)

	def name(self):
		return self._name

	def length(self):
		return self._length

	def modulus(self):
		return self._modulus