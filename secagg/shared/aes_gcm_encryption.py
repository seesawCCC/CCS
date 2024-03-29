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
import pickle

kIvSize = 12
kTagSize = 16

class AesGcmEncryption:

    def Encrypt(self, key, plaintext):
        result={}
        if key.kSize == 0 :
            print("Encrypt called with blank key.")
        if key.kSize != AesKey.kSize :
            print("Encrypt called with key of "+str(key.kSize)+"bytes, but 32 bytes are required.")
        ciphertext_buffer = [0]*(kIvSize + len(plaintext) + kTagSize)
        # FCP_CHECK(RAND_bytes(ciphertext_buffer.data(), kIvSize))

        # *****  aes-256-gcm 加密 ******
        # key: 为bytes，64字符
        # plaintext: 为bytes, 明文
        # 返回: 为bytes, base64 的密文
        iv = [0]*kIvSize
        # 设置为byte类型
        key = key.data()
        # text = plaintext.encode('utf-8')
        text = plaintext
        # 初始化加密器
        cipher = AES.new(key, AES.MODE_GCM)
        # 加密
        cipher_text, tag = cipher.encrypt_and_digest(text)
        # self.nonce = cipher.nonce
        enc_result = base64.b64encode(tag + cipher_text)

        result['enc'] = enc_result
        result['nonce'] = cipher.nonce
        result = pickle.dumps(result)

        return result


    def Decrypt(self, key,message):

        message = pickle.loads(message)
        ciphertext = message['enc']
        nonce = message['nonce']

        if key.kSize == 0 :
            print("Encrypt called with blank key.")
        if key.kSize != AesKey.kSize :
            print("Encrypt called with key of "+key.kSize+" bytes, but 32 bytes are required.")
        if len(ciphertext) < kIvSize + kTagSize :
            print( "Ciphertext is too short.")
            return FCP_STATUS(StatusCode.DATA_LOSS)

        plaintext_buffer = [0] * (len(ciphertext) - kIvSize - kTagSize)

        #         aes-256-gcm 解密
        #     key: 为bytes，64字符(32字节)
        #     ciphertext: 为bytes, base64 的密文
        #    返回: bytes 的明文
        message['enc'] = ciphertext
        key = key.data()
        data = base64.b64decode(ciphertext)
        tag = data[0:kTagSize]
        data = data[kTagSize:]
        # 初始化解密器
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        # cipher = AES.new(key, AES.MODE_GCM)
        try:
            dec_result = cipher.decrypt(data)
            # dec_result = dec_result.decode('utf-8')
            # cipher.verify(tag)  此处有一个BUG，MAC验证无法通过
        except Exception as e:
            return e
        return dec_result




