# -*- coding: utf-8 -*-
# @Time : 2022/7/22 18:16
# @Author : LRX
# @Site : 
# @File : aes_key.py
# @Software: PyCharm

from .shamir_secret_sharing import ShamirSecretSharing

kLegacyKeySize = 17

# data: bytes
class AesKey:
    kSize = 32
    
    def __init__(self, data, key_size=kSize):
        self._data = data
        self._key_size = key_size
        if not ((key_size > 0 and key_size <= 17) or (key_size == 32)):
            print("(key_size > 0 and key_size <= 17) or (key_size == 32)")

    def data(self):
        return self._data


    def CreateFromShares(self, shares, threshold):
        reconstructor = ShamirSecretSharing()
        key_length = 0
        for i in range(shares.size()):
            if key_length == 0:
                if shares[i].data.size() == 36:
                    key_length = kSize
                elif shares[i].data.size() == 20:
                    key_length = kLegacyKeySize
                else:
                    if shares[i].data.empty():
                        print("shares[i].data.empty()")
            else:
                break
        # FCP_CHECK(key_length != 0)
        if key_length != 0:
            print("key_length != 0")
        #  FCP_ASSIGN_OR_RETURN函数
        # std::string reconstructed;
        reconstructed = ''
        # FCP_ASSIGN_OR_RETURN(
        # reconstructed, reconstructor.Reconstruct(threshold, shares, key_length));

        if key_length == kLegacyKeySize:
            index = 0
            while index < kLegacyKeySize - 1 and reconstructed[index]==0 and reconstructed[index + 1] <= 127 :
                index = index+1

            if index>0 :
                reconstructed.erase(0, index)
                key_length = key_length - index

        return AesKey(reconstructed.c_str(),key_length)

