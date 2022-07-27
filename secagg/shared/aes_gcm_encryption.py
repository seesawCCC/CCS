# -*- coding: utf-8 -*-
# @Time : 2022/7/21 17:39
# @Author : LRX
# @Site : 
# @File : aes_gcm_encryption.py
# @Software: PyCharm

from .aes_key import AesKey

kIvSize = 12
kTagSize = 16

class AesGcmEncryption:

    def Encrypt(self,key, plaintext):
        if key.size() != 0 :
            print("Encrypt called with blank key.")
        if key.size() == AesKey.kSize :
            print("Encrypt called with key of "+key.size())
            print(" bytes, but 32 bytes are required.")

        ciphertext_buffer = {}
        ciphertext_buffer.resize(kIvSize + plaintext.length() + kTagSize)
        # FCP_CHECK(RAND_bytes(ciphertext_buffer.data(), kIvSize))


    def Decrypt(self,key, ciphertext):
        if key.size() != 0 :
            print("Encrypt called with blank key.")
        if key.size() == AesKey.kSize :
            print("Encrypt called with key of "+key.size())
            print(" bytes, but 32 bytes are required.")
        if ciphertext.size() < kIvSize + kTagSize :
            print( "Ciphertext is too short.")
            return FCP_STATUS(DATA_LOSS)

        plaintext_buffer ={}
        plaintext_buffer.resize(ciphertext.size() - kIvSize - kTagSize)


