# -*- coding: utf-8 -*-
# @Time : 2022/8/10 11:20
# @Author : LRX
# @Site : 
# @File : rsa_encryption.py
# @Software: PyCharm

from Crypto import Random
from Crypto.PublicKey import RSA
import base64
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher

class rsa_encryption:
    server_public_key = ''
    server_private_key = ''

    def create_rsa_pair(self):
        random_generator = Random.new().read  # 生成随机偏移量
        rsa = RSA.generate(1024, random_generator)  # 生成一个私钥
        # 生成私钥
        private_key = rsa.exportKey()  # 导出私钥
        # print("private_key:",private_key.decode())
        # 生成公钥
        public_key = rsa.publickey().exportKey()  # 生成私钥所对应的公钥
        # print("public_key:",public_key.decode())
        #
        # with open('rsa_private_key.pem', 'wb')as f:
        #     f.write(private_key)  # 将私钥内容写入文件中
        #
        # with open('rsa_public_key.pem', 'wb')as f:
        #     f.write(public_key)  # 将公钥内容写入文件中
        return private_key,public_key

    # plaintext类型为str，public_key用于加密
    def Encrypt(self, public_key, plaintext):
        public_key = RSA.importKey(public_key)
        cipher = PKCS1_cipher.new(public_key)  # 生成一个加密的类
        # plaintext.encode()--str->bytes 进行加密 ;加密后再进行编码
        encrypt_text = base64.b64encode(cipher.encrypt(plaintext.encode()))  # 对数据进行加密
        encrypt_text = encrypt_text.decode()  # 对文本进行解码
        return encrypt_text

    def Decrypt(self, private_key, ciphertext):
        private_key = RSA.importKey(private_key)
        cipher = PKCS1_cipher.new(private_key)  # 生成一个解密的类
        back_text = cipher.decrypt(base64.b64decode(ciphertext), 0)  # 先解码再进行解密
        decrypt_text = back_text.decode()  # 对文本内容进行解码
        return decrypt_text


    def create_server_rsa_pair(self):
        rsa = RSA.generate(1024)  # 生成一个私钥
        self.server_private_key = rsa.exportKey()  # 导出私钥
        # private_key = rsa.exportKey()
        print("private_key:",self.server_private_key.decode())
        # 生成公钥
        self.server_public_key = rsa.publickey().exportKey()  # 生成私钥所对应的公钥
        print("public_key:",self.server_public_key.decode())

