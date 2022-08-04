# -*- coding: utf-8 -*-
# @Time : 2022/7/22 18:16
# @Author : LRX
# @Site : 
# @File : aes_key.py
# @Software: PyCharm

from .shamir_secret_sharing import ShamirSecretSharing
from base.monitoring import FCP_CHECK
kLegacyKeySize = 17

# data: bytes


class AesKey:

    kSize = 32

    def __init__(self, data=b'', key_size=kSize):
        self._data = data
        self._key_size = key_size
        FCP_CHECK((key_size > 0 and key_size <= 17) or (key_size == 32))

    def data(self):
        return self._data

    def size(self):
        return len(self._data)


    def CreateFromShares(self, shares, threshold):
        reconstructor = ShamirSecretSharing()
        key_length = 0
        for i in range(len(shares)):
            if key_length == 0:
                if len(shares[i].data) == 36:
                    key_length = self.kSize
                elif len(shares[i].data) == 20:
                    key_length = kLegacyKeySize
                else:
                    if shares[i].data.empty():
                        print("shares[i].data.empty()")
            else:
                break
        FCP_CHECK(key_length != 0)
        reconstructed = reconstructor.Reconstruct(threshold, shares, key_length)
        # FCP_ASSIGN_OR_RETURN(
        # reconstructed, reconstructor.Reconstruct(threshold, shares, key_length));

        if key_length == kLegacyKeySize:
            index = 0
            while index < kLegacyKeySize - 1 and reconstructed[index]==0 and reconstructed[index + 1] <= 127 :
                index = index+1
            if index>0 :
                # reconstructed.erase(0, index)
                reconstructed = reconstructed[index:]
                key_length = key_length - index

        # return AesKey(reconstructed.encode('utf-8'),key_length)
        return AesKey(reconstructed, key_length)

