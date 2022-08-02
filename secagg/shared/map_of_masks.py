# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-30 15:50:40
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-07-31 23:13:12
import hashlib

import secagg.shared.math as math
from base.monitoring import FCP_CHECK
from .secagg_vector import SecAggVector, SecAggVectorMap
from .aes_key import AesKey

kPrngSeedConstant = 0x02
kMaxSampleBits = 63
kMaxSampleBitsExpansion = 16

# prng_input: bytes
# prng_key: bi, sij
# return bytes[32]
def DigestKey(prng_input, bit_width, prng_key):
	input_size = len(prng_input)
	input_size_bytes = math.IntToByteString(input_size) 
	bit_width_bytes = math.IntToByteString(bit_width)
	if not isinstance(prng_input, bytes):
		prng_input = prng_input.encode('ascii')
	hsobj = hashlib.sha256()
	hsobj.update(bit_width_bytes)
	hsobj.update(prng_key.data())
	hsobj.update(int.to_bytes(kPrngSeedConstant, 1, 'little'))
	hsobj.update(input_size_bytes)
	hsobj.update(prng_input)
	digest = hsobj.digest()
	FCP_CHECK(len(digest) == AesKey.kSize)
	return AesKey(digest)

def choose_better_sample_bits(modulus, sample_bits_1, sample_bits_2):
	FCP_CHECK(sample_bits_1 <= sample_bits_2)
	FCP_CHECK(sample_bits_2 <= kMaxSampleBits)
	FCP_CHECK(sample_bits_2-sample_bits_1 <= kMaxSampleBitsExpansion)

	if sample_bits_1 == sample_bits_2:
		return sample_bits_1

	sample_modulus_1 = 1<<sample_bits_1
	FCP_CHECK(modulus <= sample_modulus_1)
	sample_modulus_2 = 1<<sample_bits_2
	sample_modulus_2_over_1 = 1<<(sample_bits_2-sample_bits_1)
	cost_per_sample_1 = math.DivideRoundUp(sample_bits_1, 8)
	cost_per_sample_2 = math.DivideRoundUp(sample_bits_2, 8)
	modulus_reps_1 = sample_modulus_1//modulus
	modulus_reps_2 = sample_modulus_2//modulus
	cost_product_1 = cost_per_sample_1*modulus_reps_1
	cost_product_2 = cost_per_sample_2*modulus_reps_2*sample_modulus_2_over_1
	return sample_bits_2 if cost_product_1 > cost_per_sample_2 else sample_bits_1

def compute_best_sample_bits(modulus):
	min_sample_bits = math.BitWidth(modulus-1)
	max_sample_bits = min(kMaxSampleBitsExpansion, min_sample_bits+kMaxSampleBitsExpansion)
	best_sample_bits = min_sample_bits
	for sample_bits in range(min_sample_bits+1, max_sample_bits+1):
		best_sample_bits = choose_better_sample_bits(modulus, best_sample_bits, sample_bits)
	return best_sample_bits

# 根据计算得到digest计算用于mask的值
class PrngBuffer():
	
	def __init__(self, prng, msb_mask, bytes_per_output):
		  self._prng = prng
		  self._msb_mask = msb_mask
		  self._bytes_per_output = bytes_per_output
		  self._buffer = [0]*self._prng.GetMaxBufferSize()
		  self._buffer_end = self._prng.GetMaxBufferSize()
		  self._buffer_ptr = 0
		  FCP_CHECK(not self._buffer_end%bytes_per_output, "PRNG buffer size must be a multiple bytes_per_output.")
		  self._FillBuffer()
	
	def NextMask(self):
		if self._buffer_ptr == self._buffer_end:
			self._FillBuffer()
		output = self._buffer[self._buffer_ptr]&self._msb_mask
		self._buffer_ptr += 1
		for i in range(self._bytes_per_output):
			output <<= 8
			output |= self._buffer[self._buffer_ptr]
			self._buffer_ptr += 1
		return output

	def _buffer_size(self):
		return len(self._buffer)

	def _FillBuffer(self):
		self._buffer_ptr = 0
		FCP_CHECK(self._prng.RandBuffer(self._buffer, self._buffer_size()) == self.buffer_size())


class AddModAdapter():
	def __init__(self):
		pass

	@staticmethod
	def AddModImpl(a, b, z):
		return math.AddMod(a, b, z)

	@staticmethod
	def SubtractModImpl(a, b, z):
		return math.SubtractModOpt(a, b, z)

def MapOfMasksImpl(prng_keys_to_add, prng_keys_to_subtract, input_vector_specs, session_id, prng_factory, async_abort, rt_class):
	FCP_CHECK(prng_factory.SupportsBatchMode())

	map_of_masks = SecAggVectorMap()
	for vector_spec in input_vector_specs:
		if async_abort and async_abort.Signalled():
			return None
		bit_width = math.BitWidth(vector_spec.modulus()-1)
		prng_input = session_id.data.encode('ascii')+math.IntToByteString(bit_width)+math.IntToByteString(vector_spec.length())+vector_spec.name().encode('ascii')
		mask_vector_buffer = [0]*vector_spec.length()

		modulus_is_power_of_two = (1<<bit_width == vector_spec.modulus())
		if modulus_is_power_of_two:
			bytes_per_output = math.DivideRoundUp(bit_width, 8)
			bits_in_msb = bit_width-((bytes_per_output-1)*8)
			msb_mask = (1<<bits_in_msb)-1

			for prng_key in prng_keys_to_add:
				if async_abort and async_abort.Signalled():
					return None
				digest_key = DigestKey(prng_input, bit_width, prng_key)
				prng = PrngBuffer(prng_factory.MakePrng(digest_key), msb_mask, bytes_per_output)
				for i in range(len(mask_vector_buffer)):
					mask_vector_buffer[i] = AddModAdapter.AddModImpl(mask_vector_buffer[i], prng.NextMask(), vector_spec.modulus())

			for prng_key in prng_keys_to_subtract:
				if async_abort and async_abort.Signalled():
					return None
				digest_key = DigestKey(prng_input, bit_width, prng_key)
				prng = PrngBuffer(prng_factory.MakePrng(digest_key), msb_mask, bytes_per_output)
				for i in range(len(mask_vector_buffer)):
					mask_vector_buffer[i] = AddModAdapter.SubtractModImpl(mask_vector_buffer[i], prng.NextMask(), vector_spec.modulus())
		else:
			sample_bits = compute_best_sample_bits(vector_spec.modulus())
			bytes_per_output = math.DivideRoundUp(sample_bits, 8)
			bits_in_msb = sample_bits-((bytes_per_output-1)*8)
			msb_mask = (1<<bits_in_msb)-1
			sample_modulus = 1<<sample_bits
			rejection_threshold = (sample_modulus-vector_spec.modulus())%vector_spec.modulus()

			for prng_key in prng_keys_to_add:
				if async_abort and async_abort.Signalled():
					return None
				digest_key = DigestKey(prng_input, sample_bits, prng_key)
				prng = PrngBuffer(prng_factory.MakePrng(digest_key), msb_mask, bytes_per_output)
				i = 0
				while i < vector_spec.length():
					mask = prng.NextMask() 
					reject = mask < rejection_threshold
					inc = (not reject)&1
					if reject:
						mask = 0
					mask_vector_buffer[i] = AddModAdapter.AddModImpl(mask_vector_buffer[i], mask%vector_spec.modulus(), vector_spec.modulus())
					i += inc
			for prng_key in prng_keys_to_subtract:
				if async_abort and async_abort.Signalled():
					return None
				digest_key = DigestKey(prng_input, sample_bits, prng_key)
				prng = PrngBuffer(prng_factory.MakePrng(digest_key), msb_mask, bytes_per_output)
				i = 0
				while i < vector_spec.length():
					mask = prng.NextMask() 
					reject = mask < rejection_threshold
					inc = (not reject)&1
					if reject:
						mask = 0
					mask_vector_buffer[i] = AddModAdapter.SubtractModImpl(mask_vector_buffer[i], mask%vector_spec.modulus(), vector_spec.modulus())
					i += inc
		if async_abort and async_abort.Signalled():
			return None
		map_of_masks[vector_spec.name()] = SecAggVector(mask_vector_buffer, vector_spec.modulus())
	return map_of_masks

def MapOfMasks(prng_keys_to_add, prng_keys_to_subtract, input_vector_specs, session_id, prng_factory, async_abort):
	MapOfMasksImpl(prng_keys_to_add, prng_keys_to_subtract, input_vector_specs, session_id, prng_factory, async_abort, rt_class=AddModAdapter)

# def MapOfMasksV3(prng_keys_to_add, prng_keys_to_subtract, input_vector_specs, session_id, prng_factory, async_abort):
# 	MapOfMasksImpl(prng_keys_to_add, prng_keys_to_subtract, input_vector_specs, session_id, prng_factory, async_abort, rt_class=AddModOptAdapter)

def AddVectors(a, b):
	FCP_CHECK(a.modulus() == b.modulus() and a.num_elements() == b.num_elements())
	modulus = a.modulus()
	decoder_a = SecAggVector.Decoder(a)
	decoder_b = SecAggVector.Decoder(b)	
	sum_coder = SecAggVector.Coder(modulus, a.bit_width(), a.num_elements())

	for remaining_elements in range(a.num_elements()):
		sum_coder.WriteValue((decoder_a.ReadValue()+decoder_b.ReadValue())%modulus)
	return sum_coder.Create()

def AddMaps(a, b):
	result = SecAggVectorMap()
	for key in a:
		result[key] = AddVectors(a[key], b[key])
	return result
