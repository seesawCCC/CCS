# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-22 17:03:02
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-08-02 18:01:33

# Reconstruct返回的StatusOr还没写
import random

from .math import MultiplyMod, DivideRoundUp, IntToByteString


kSubsecretSize = 4


class ShamirShare():
	def __init__(self, string=b''):
		self.data = string

class ShamirSecretSharing():
	kPrime = 2147483659
	_kBitsPerSubsecret = 31


	def __init__(self):
		self._inverses = []
		self._last_lc_input = []
		self._last_lc_output = []

	def Share(self, threshold, num_shares, to_share):
		if not isinstance(to_share, str):
			to_share = to_share.AsString()
		assert len(to_share), "to_share must not be empty"
		assert num_shares > 1, "num_shares must be greater than 1"
		assert 2 <= threshold and threshold <= num_shares, "threshold must be at least 2 and at most num_shares"

		subsecrets = self._DivideIntoSubsecrets(to_share)
		shares = []
		for i in range(num_shares):
			shares.append([])

		for subsecret in subsecrets:
			coefficients = []
			coefficients.append(subsecret)
			for i in range(1, threshold):
				coefficients.append(self._RandomFieldElement())
			for i in range(num_shares):
				subshare = self._EvaluatePolynomial(coefficients, i+1)
				shares[i].append(IntToByteString(subshare))
		for i in range(num_shares):
			shares[i] = ShamirShare(b''.join(shares[i]))
		return shares

	def Reconstruct(self, threshold, shares, secret_length):
		assert threshold > 1, "threshold must be at least 2"
		assert secret_length > 0, "secret_length must be positive"
		assert len(shares) >= threshold, "A vector of size {} was provided, but threshold was specified as {}".format(len(shares), threshold) 

		max_num_subsecrets = ((8*secret_length)+kSubsecretSize-1)//kSubsecretSize
		num_subsecrets = 0
		x_values = []

		i = 0
		while i < len(shares) and len(x_values) < threshold:
			share_string = shares[i].data
			if not share_string:
				continue
			assert not len(share_string)%kSubsecretSize, "Share with index {} is invalid: a share of size {} was provided but a multiple of {} is expected".format(i, len(share_string), kSubsecretSize)
			if num_subsecrets == 0:
				num_subsecrets = len(share_string)//kSubsecretSize
				assert num_subsecrets > 0 and num_subsecrets <= max_num_subsecrets, "Share with index {} is invalid:the number of subsecrets is {} but between 1 and {}is expected".format(i, num_subsecrets, max_num_subsecrets)
			else:
				assert len(share_string) == num_subsecrets*kSubsecretSize, "Share with index {} is invalid: all shares must match sizes:shares[i].data.size()={}, num_subsecrets ={}".format(i, len(share_string), num_subsecrets)
			x_values.append(i+1)
			i += 1

		if len(x_values) < threshold:
			return None

		coefficients = self._LagrangeCoefficients(x_values)
		subsecrets = []
		for i in range(num_subsecrets):
			subsecrets.append(0)
			for j in range(len(x_values)):
				share_index = x_values[j]-1
				subshare = 0
				for k in range(kSubsecretSize):
					subshare <<= 8
					subshare += shares[share_index].data[kSubsecretSize*i+k]
				subsecrets[i] += MultiplyMod(subshare, coefficients[j], self.kPrime)
				subsecrets[i] %= self.kPrime

		return self._RebuildFromSubsecrets(subsecrets, secret_length)

	def _ModInverse(self, n):
		assert n > 0 and n < self.kPrime, "Invalid value {} for ModInverse".format(n)
		inverse_len = len(self._inverses)
		while inverse_len < n:
			# n^p-1 = 1modp, n*n^p-2 =1modp
			self._inverses.append(ModPow(inverse_len+1, self.kPrime-2)) 
			inverse_len += 1
		return self._inverses[n-1]

	def _LagrangeCoefficients(self, x_values):
		assert len(x_values) > 1, "Must have at least 2 x_values"
		for x_val in x_values:
			assert x_val > 0, "x_values must all be positive, but got a value of {}".format(x_val)
		if x_values == self._last_lc_input:
			return self._last_lc_input
		self._last_lc_input = x_values
		self._last_lc_output.clear()
		x_values_len = len(x_values)
		for i in range(x_values_len):
			self._last_lc_output.append(1)
			for j in range(x_values_len):
				if i == j:
					continue
				self._last_lc_output[i] = MultiplyMod(self._last_lc_output[i], x_values[j], self.kPrime) 
				if x_values[j] > x_values[i]:
					self._last_lc_output[i] = MultiplyMod(self._last_lc_output[i], self._ModInverse(x_values[j] - x_values[i]), self.kPrime)
				else:
					self._last_lc_output[i] = MultiplyMod(self._last_lc_output[i], self.kPrime-1, self.kPrime)
					self._last_lc_output[i] = MultiplyMod(self._last_lc_output[i], self._ModInverse(x_values[i] - x_values[j]), self.kPrime)

		return self._last_lc_output			

	def _DivideIntoSubsecrets(self, to_share):
		secret_parts = [0]*DivideRoundUp(len(to_share)*8, self._kBitsPerSubsecret)
		bits_done = 0
		secret_index = len(secret_parts)-1
		i = len(to_share)-1 
		while i>=0:
			current_byte = to_share[i] if not isinstance(to_share[i], str) else ord(to_share[i])
			if self._kBitsPerSubsecret-bits_done > 8:
				secret_parts[secret_index] |= (current_byte<<bits_done)
				bits_done += 8
			else:
				current_byte_right = current_byte&(0xFF>>(8-(self._kBitsPerSubsecret-bits_done)))
				secret_parts[secret_index] |= current_byte_right<<bits_done
				if not (i == 0 and bits_done+8 == self._kBitsPerSubsecret):
					bits_done = (bits_done+8)%self._kBitsPerSubsecret
					secret_index -= 1
					secret_parts[secret_index] |= current_byte>>(8-bits_done)
			i -= 1
		assert secret_index<=0
		return secret_parts

	def _RebuildFromSubsecrets(self, secret_parts, secret_length):
		secret = [0]*secret_length
		bits_done = 0
		secret_index = len(secret_parts)-1
		i = secret_length-1
		while i >=0 and secret_index >= 0:
			if self._kBitsPerSubsecret-bits_done > 8:
				secret[i] = (secret_parts[secret_index]>>bits_done)&0xFF
				bits_done += 8
			else:
				next_low_bits = secret_parts[secret_index]>>bits_done
				secret_index -= 1
				if secret_index >= 0:
					secret[i] = secret_parts[secret_index]&(0xFF>>(self._kBitsPerSubsecret-bits_done))
				bits_done = (bits_done+8)%self._kBitsPerSubsecret
				secret[i] <<= 8-bits_done
				secret[i] |= next_low_bits
			i -= 1
		secret = [chr(item) for item in secret]
		return ''.join(secret)

	def _RandomFieldElement(self):
		rand = 0
		max_element = (1<<32)-1
		return random.randrange(self.kPrime, max_element)


	def _EvaluatePolynomial(self, polynomial, x):
		poly_sum = 0
		for i in range(1, len(polynomial))[::-1]:
			poly_sum += polynomial[i]
			poly_sum *= x
			poly_sum %= self.kPrime
		poly_sum += polynomial[0]
		poly_sum %= self.kPrime
		return poly_sum

def ModPow(x, y):
	if y == 0:
		return 1
	p = ModPow(x, y>>1)%ShamirSecretSharing.kPrime
	q = MultiplyMod(p, p, ShamirSecretSharing.kPrime)
	return q if not y&0x01 else MultiplyMod(x, q, ShamirSecretSharing.kPrime)