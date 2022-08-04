# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-19 15:24:50
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-08-04 11:47:35

import struct
import random

def RandomString(length=12):
	if length < 1:
		return b'default password'
	string_list = []
	for i in range(length):
		string_list.append(chr(random.randint(33, 126)).encode('utf-8'))
	return b''.join(string_list)

class ArgumentTypeException(Exception):
	def __init__(self, arg_type):
		self.reason = "The arguments must be {}".format(arg_type)

	def __str__(self):
		return repr(self.reason)

def TypeCheck(type_check, *args):
	for arg in args:
		if not isinstance(arg, type_check):
			raise ArgumentTypeException(type_check)

# Integer division rounded up
def DivideRoundUp(a, b):
	TypeCheck(int, a, b)
	return (a+b-1)//b

# Addition modulo non-zero integer z
def AddMod(a, b, z):
	TypeCheck(int, a, b, z)
	return (a+b)%z

def AddModOpt(a, b, mod):
	TypeCheck(int, a, b, mod)
	assert a < mod and b < mod, 'arguments must be less than mod'
	assert a <= a+b and b <= a+b, 'arguments must be non-negative'
	sum = a+b
	return sum if sum < mod else sum-mod 

def SubtractMod(a, b, z):
	TypeCheck(int, a, b, z)
	return (a-b+z)%z

def SubtractModOpt(a, b, mod):
	TypeCheck(int, a, b, mod)
	assert a < mod and b < mod, 'arguments must be less than mod'
	return a-b if a>=b else mod-b+a

def MultiplyMod(a, b, z):
	TypeCheck(int, a, b, z)
	return int((a*b)%z)

def InverseModPrime(a, z):
	TypeCheck(int, a, z)
	inverse = 1
	exponent = z - 2
	while exponent > 0:
		if exponent&1:
			inverse = MultiplyMod(inverse, a, z)
		exponent = exponent >> 1
		a = MultiplyMod(a, a, z)
	return inverse

# Converts ints to big-endian byte bytes representation
def IntToByteString(input_int):
	TypeCheck(int, input_int)
	input_bytes = input_int.to_bytes(4, 'big')
	return input_bytes

def BitWidth(modulus):
	return len(bin(modulus))-2
