# -*- coding: utf-8 -*-
# @Time : 2022/7/21 17:39
# @Author : LRX
# @Site : 
# @File : aes_gcm_encryption.py
# @Software: PyCharm

from .aes_key import AesKey
from Crypto.Cipher import AES
import base64
from base.monitoring import FCP_STATUS, StatusCode

kIvSize = 12
kTagSize = 16

class AesGcmEncryption:

    def Encrypt(self, key, plaintext):
        if len(key) != 0 :
            print("Encrypt called with blank key.")
        if len(key) == AesKey.kSize :
            print("Encrypt called with key of "+str(len(key)))
            print(" bytes, but 32 bytes are required.")

        ciphertext_buffer = [0]*(kIvSize + plaintext.length() + kTagSize)
        # FCP_CHECK(RAND_bytes(ciphertext_buffer.data(), kIvSize))

        # *****  aes-256-gcm 加密 ******
        # key: 为str，hex字符串,64字符
        # plaintext: 为bytes, 明文
        # 返回: 为bytes, base64 的密文

        iv = [0]*kIvSize
        key = bytes.fromhex(key.data())
        text = bytes.fromhex(plaintext.c_str())
        # 初始化加密器
        cipher = AES.new(key, AES.MODE_GCM)
        # 加密
        cipher_text, tag = cipher.encrypt_and_digest(text)
        enc_result = base64.b64encode(tag + cipher_text)

        return enc_result


    def Decrypt(self, key, ciphertext):
        if len(key) != 0 :
            print("Encrypt called with blank key.")
        if len(key) == AesKey.kSize :
            print("Encrypt called with key of "+key.size())
            print(" bytes, but 32 bytes are required.")
        if len(ciphertext) < kIvSize + kTagSize :
            print( "Ciphertext is too short.")
            return FCP_STATUS(StatusCode.DATA_LOSS)

        plaintext_buffer = [0] * (ciphertext.size() - kIvSize - kTagSize)

        #         aes-256-gcm 解密
        #     key: 为str，hex字符串,64字符(32字节)
        #     ciphertext: 为bytes, base64 的密文
        #    返回: bytes 的明文

        key = bytes.fromhex(key.data())
        text = bytes.fromhex(ciphertext.data())
        data = base64.b64decode(text)
        tag = data[0:kTagSize]
        data = data[kTagSize:]

        # 初始化解密器
        cipher = AES.new(key, AES.MODE_GCM)
        try:
            dec_result = cipher.decrypt_and_verify(data,tag)
        except Exception as e:
            return e
        return dec_result




