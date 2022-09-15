 # -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-19 18:10:57
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-15 16:49:38

# FCP_CHECK到时用一个Logger代替算了

import sys
from .math import DivideRoundUp, AddModOpt, MultiplyMod

class SecAggVector():
	kMaxModulus = 1<<62

	@classmethod
	def UnpackUint64FromByteStringAt(cls, index, bit_width, byte_string, chr_width=8):
		leftmost_bit_position = index*bit_width
		leftmost_byte_index = leftmost_bit_position//chr_width
		left_boundary_bit_position = leftmost_bit_position%chr_width
		unpacked_element, leftmost_bit_position, leftmost_byte_index = cls.Decoder.UnpackByteStringIntoUint64(byte_string, bit_width, chr_width, left_boundary_bit_position, leftmost_byte_index)
		return unpacked_element

	@classmethod
	def GetBitWidth(cls, modulus):
		return len(bin(modulus))-2

	# 如果需要branchless_codec参数，使用branchless_codec=True来调用
	def __init__(self, *args, **kwargs):
		args_length = len(args)
		branchless_codec = kwargs.get('branchless_codec', False)
		self._branchless_codec = branchless_codec
		self._chr_width = kwargs.get('chr_width', 8)
		if args_length == 2:
			self._init_span(args)
		elif args_length == 3:
			self._init_packed_bytes(args)
		elif args_length == 1:
			self._init_from_other(args)

	def _init_span(self, args):
		# span类似于数组
		span, modulus = args
		self._modulus = modulus
		self._bit_width = SecAggVector.GetBitWidth(modulus)
		self._num_elements = len(span)
		
		if self._modulus < 1 or self._modulus > SecAggVector.kMaxModulus:
			raise Exception("The specified modulus is not valid: must be > 1 and <= {}; supplied value: {}".format(SecAggVector.kMaxModulus, self._modulus))
		for element in span:			
			if element < 0:
				raise Exception("Only non negative elements are allowed in the vector.")
			if element >= self._modulus:
				raise Exception("The span does not have the appropriate modulus: element with value:{} found, max value allowed{}".format(element, self._modulus))
		if self._branchless_codec:
			 self._PackUint64IntoByteStringBranchless(span)
		else:
			num_chars_needed = DivideRoundUp(self._num_elements*self._bit_width, self._chr_width)
			self._packed_bytes_list = ['\0']*num_chars_needed
			for i in range(len(span)):
				self._PackUint64IntoByteStringAt(i, span[i], self._chr_width)
			self._packed_bytes = ''.join(self._packed_bytes_list)

	def _init_packed_bytes(self, args):
		packed_bytes, modulus, num_elements = args
		self._packed_bytes = packed_bytes
		self._modulus = modulus
		self._bit_width = SecAggVector.GetBitWidth(modulus)
		self._num_elements = num_elements

		if self._modulus < 1 or self._modulus > SecAggVector.kMaxModulus:
			raise Exception("The specified modulus is not valid: must be > 1 and <= {}; supplied value: {}".format(SecAggVector.kMaxModulus, self._modulus))
		expected_num_bytes = DivideRoundUp(self._num_elements*self._bit_width, self._chr_width) 
		if len(self._packed_bytes) != expected_num_bytes:
			raise Exception("The supplied string is not the right size for {} packed elements: given string has a limit of {} bytes, {} bytes would have been needed.".format(self._num_elements, len(self._packed_bytes), expected_num_bytes))

	def _init_from_other(self, args):
		other = args[0]
		other._MoveTo(self)
		return self

	def GetAsUint64Vector(self):
		self._CheckHasValue()
		long_vector = []
		if self._branchless_codec:
			self._UnpackByteStringToUint64VectorBranchless(long_vector)
		else:
			for i in range(self._num_elements):
				long_vector.append(SecAggVector.UnpackUint64FromByteStringAt(i, self._bit_width, self._packed_bytes))
		return long_vector

	def modulus(self):
		return self._modulus

	def bit_width(self):
		return self._bit_width

	def num_elements(self):
		return self._num_elements

	# _packed_bytes是unicode
	def GetAsPackedBytes(self):
		self._CheckHasValue()
		return self._packed_bytes

	def TakePackedBytes(self):
		self._CheckHasValue()
		self._modulus = 0
		self._bit_width_ = 0
		self._num_elements = 0
		packed_bytes = self._packed_bytes
		self._packed_bytes = ''
		return packed_bytes


	class Decoder():

		def __init__(self, *args, **kwargs):
			args_length = len(args)
			self._chr_width = kwargs.get('chr_width', 8)
			if args_length == 1:
				v = args[0]
				self._init_from_vector(v)
			elif args_length == 2:
				packed_bytes, modulus = args
				self._init_default(packed_bytes, modulus)

		def _init_from_vector(self, v):
			self._init_default(v._packed_bytes, v._modulus)

		def _init_default(self, packed_bytes, modulus):
			self._packed_bytes = packed_bytes
			self._starting_position = 0
			self._starting_index = 0
			self._modulus = modulus
			self._bit_width = SecAggVector.GetBitWidth(self._modulus)

		@classmethod
		def UnpackByteStringIntoUint64(cls, packed_bytes, need_scaned_bit_num, chr_width, starting_position, starting_index):
			unpack_value = 0
			scan_bit_sum = 0
			while need_scaned_bit_num > 0:
				round_bit_scan = min(need_scaned_bit_num, chr_width-starting_position)
				if round_bit_scan < 0:
					raise Exception("Decoder.ReadValue Error: bug")
				chr_ord = ord(packed_bytes[starting_index])
				mask = ((1<<round_bit_scan)-1)<<starting_position
				part_value = mask&chr_ord
				part_value >>= starting_position
				unpack_value += (part_value<<scan_bit_sum)

				scan_bit_sum += round_bit_scan
				starting_position += round_bit_scan
				need_scaned_bit_num -= round_bit_scan
				if starting_position//chr_width:
					starting_index += 1
					starting_position %= chr_width

			return (unpack_value, starting_position, starting_index)


		def ReadValue(self):
			need_scaned_bit_num = self._bit_width
			unpack_value, self._starting_position, self._starting_index = self.UnpackByteStringIntoUint64(self._packed_bytes, need_scaned_bit_num, self._chr_width, self._starting_position, self._starting_index)
			return unpack_value

		def _c(self):
			pass

	class Coder():
		# modulus用于生成SceaggVector
		def __init__(self, modulus, bit_width, num_elements, chr_width=8):
			self._modulus = modulus
			self._bit_width = bit_width
			self._num_elements = num_elements
			self._starting_index = 0
			self._starting_position = 0
			self._chr_width = chr_width
			self._num_bytes_needed = DivideRoundUp(self._num_elements*self._bit_width, self._chr_width)
			self._packed_bytes = ['\0']*self._num_bytes_needed 	

		@classmethod
		def PackUint64IntoByteString(cls, value, need_bit_padding_num, chr_width, packed_bytes, starting_position, starting_index):
			while need_bit_padding_num > 0:
				round_bit_padding = min(chr_width-starting_position, need_bit_padding_num)
				if round_bit_padding < 0:
					raise Exception("Coder.WriteValue Error: bug")
				mask = (1<<round_bit_padding)-1
				padding_value = (value&mask)<<starting_position
				padding_value |= ord(packed_bytes[starting_index])
				packed_bytes[starting_index] = chr(padding_value)

				need_bit_padding_num -= round_bit_padding
				value >>= round_bit_padding 
				starting_position += round_bit_padding
				
				if starting_position//chr_width:
					starting_position %= chr_width
					starting_index += 1
			return (starting_position, starting_index)

		def WriteValue(self, value):
			if value >= self._modulus:
				raise Exception("value must be lower than modulus:{}".format(self._modulus))
			need_bit_padding_num = self._bit_width 
			self._starting_position, self._starting_index = self.PackUint64IntoByteString(value, need_bit_padding_num, self._chr_width, self._packed_bytes, self._starting_position, self._starting_index)

		def Create(self, string_flag=False):
			packed_bytes = ''.join(self._packed_bytes)			
			if not string_flag:
				return SecAggVector(packed_bytes, self._modulus, self._num_elements, branchless_codec=True)
			else:
				return packed_bytes

	def _MoveTo(self, target):
		target._modulus = self._modulus
		target._bit_width = self._bit_width
		target._num_elements = self._num_elements
		target._branchless_codec = self._branchless_codec
		target._packed_bytes = self._packed_bytes
		target._chr_width = self._chr_width
		# self._modulus = 0
		# self._bit_width = 0
		# self._num_elements = 0
		# self._branchless_codec = False

	def _CheckHasValue(self):
		assert self._modulus > 0, "SecAggVector has no value"

	def _PackUint64IntoByteStringAt(self, index, element, chr_width):
		has_padding_bits = index*self._bit_width
		starting_position = has_padding_bits%chr_width
		starting_index = has_padding_bits//chr_width
		need_bit_padding_num = self._bit_width
		packed_bytes = self._packed_bytes_list
		starting_position, starting_index = self.Coder.PackUint64IntoByteString(element, need_bit_padding_num, chr_width, packed_bytes, starting_position, starting_index)

	def _PackUint64IntoByteStringBranchless(self, span):
		coder = self.Coder(self._modulus, self._bit_width, self._num_elements)
		for element in span:
			coder.WriteValue(element)
		self._packed_bytes = coder.Create(True)

	def _UnpackByteStringToUint64VectorBranchless(self, long_vector):
		decoder = self.Decoder(self)
		for i in range(self._num_elements):
			element = decoder.ReadValue()
			long_vector.append(element)

# {'name': SecAggVector}
class SecAggVectorMap(dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

class SecAggUnpackedVectorMap(dict):

	# a,b: SecAggUnpackedVectorMap
	@staticmethod
	def AddMaps(a, b): 
		result = SecAggUnpackedVectorMap()
		for key in a:
			a_at_key = a[key]
			b_at_key = b[key]
			length = a_at_key.num_elements()
			modulus = a_at_key.modulus()
			result_vector = SecAggUnpackedVector(length, modulus)
			for i in range(length):
				result_vector[i] = AddModOpt(a_at_key[i], b_at_key[i], modulus)
			result[key] = result_vector
		return result

	# other: SecAggVectorMap
	def __init__(self, other=None):
		super().__init__()
		if other:
			for name in other:
				vector = other[name]
				self[name] = SecAggUnpackedVector(vector)

	# other: SecAggVectorMap
	def Add(self, other):
		assert len(self) == len(other)
		for key in self:
			value = self[key]
			plus_value = other.get(key, None)
			if plus_value is None:
				raise Exception("other SecAggVectorMap must have the same key {}".format(key))
			value.Add(plus_value)


class SecAggUnpackedVector(list):
	def __init__(self, first_arg, modulus=0):
		self._modulus = modulus
		init_list = []
		if isinstance(first_arg, int):
			init_list = [0]*first_arg
		elif isinstance(first_arg, list):
			init_list = first_arg[:]
		elif isinstance(first_arg, SecAggVector):
			self._modulus = first_arg.modulus()
			num_elements = first_arg.num_elements()
			init_list = [0]*num_elements
			decoder = SecAggVector.Decoder(first_arg)
			for i in range(num_elements):
				init_list[i] = decoder.ReadValue()
		elif isinstance(first_arg, type(self)):
			init_list = first_arg[:]
			self._modulus = first_arg._modulus
			first_arg._modulus = 0
		super().__init__(init_list)

	def modulus(self):
		return self._modulus

	def num_elements(self):
		return len(self)

	def Add(self, other):
		if isinstance(other, SecAggVector):
			self._AddPackedVector(other)
		else:
			self._AddUnpackedVector(other)

	def _AddPackedVector(self, other):
		assert self.num_elements() == other.num_elements()
		assert self.modulus() == other.modulus()
		decoder = SecAggVector.Decoder(other)
		for i in range(self.num_elements()):
			self[i] = AddModOpt(self[i], decoder.ReadValue(), self.modulus())

	def _AddUnpackedVector(self, other):
		assert self.num_elements() == other.num_elements()
		assert self.modulus() == other.modulus()
		for i in range(self.num_elements()):
			self[i] = AddModOpt(self[i], other[i], self.modulus())



