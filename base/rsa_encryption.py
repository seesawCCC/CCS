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
from Crypto.Signature import PKCS1_v1_5 as PKCS1_signature
from Crypto.Hash import SHA

class RsaEncryption:
    server_public_key = b'-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC/DAJ9fhXoUEnzLRVMNY3Mijjp\n3fvWJcuFFqd3+3RecfV6nOHGRcbSkd1qWQbqvGAi9RcGgfgrmAV7n+tipsqSQXcH\nZgA6w54J1b0khzOQPDp1PoaRQ6i1cSbdYV/56DKxQVBUmvxyyYaufkDgwS8ROhk6\nLPUk9xPQPfNhJ1ZwwwIDAQAB\n-----END PUBLIC KEY-----'
    server_private_key = b'-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAKBgQC/DAJ9fhXoUEnzLRVMNY3Mijjp3fvWJcuFFqd3+3RecfV6nOHG\nRcbSkd1qWQbqvGAi9RcGgfgrmAV7n+tipsqSQXcHZgA6w54J1b0khzOQPDp1PoaR\nQ6i1cSbdYV/56DKxQVBUmvxyyYaufkDgwS8ROhk6LPUk9xPQPfNhJ1ZwwwIDAQAB\nAoGABIAcF5MJTBQxccTi8WJ6Pn0WaHfzZJuLpvfI0SbqGlwf4W1hqiyJnvs9q9wr\nXAs8+TCB2YQ6nDhJZMdNzGChI/S3fM2VqalskpHmCDdXReGCaUsbsTjl1sHpQtS0\nLHPoKFYmsYGenFEcK5C6NYR/S4qQ5kqlvVUT28gCywLPvoUCQQDFjhhnt8pMeIYU\nWkASmRiyR2ceRdCUB4C8gZ42w7Dvx+ZTQknt2yJtkG57e/UgykJaRKTuthROJcum\nitw7QynvAkEA95EEe5gTUJwMz69tasQ3kWsPM1o06WFsBVB42bBoBVU5JlGISgFL\nGWohPYjvfTcsXXotympK3aESn/2zAMnKbQJBAMNwXt6E6YKbnXGXE1oS0WbV0sMV\nKFK51Xcn+CCPmoSsy0TFCKRiLP4da9+H8yqcTeZFkLGDujTRmVZKe7O5L0sCQH6N\n1XrQ7N7CRxJMHWT81WMzFVws+utq7+tvjbfKpAJF5Kcf+snKC3f8du2b+MFL2RQY\nBxx4ZbkSRBEhgcYfYakCQDnB9anCnf588HIecx6TeX2T6evPdWk5LnJZHqZMH3mC\nLmjWP2qEdZWFU0kF77qf9xXJtGH0OKi97JhRwF/wDtg=\n-----END RSA PRIVATE KEY-----'

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

    # plaintext类型为bytes，public_key用于加密,返回值encrypt_text为bytes
    def Encrypt(self, public_key, plaintext):
        public_key = RSA.importKey(public_key)
        cipher = PKCS1_cipher.new(public_key)  # 生成一个加密的类
        # plaintext.encode()--str->bytes 进行加密 ;加密后再进行编码
        encrypt_text = base64.b64encode(cipher.encrypt(plaintext))  # 对数据进行加密
        # encrypt_text = encrypt_text.decode()  # 对文本进行解码
        return encrypt_text

    # ciphertext类型为bytes，private_key用于解密,返回值decrypt_text为bytes
    def Decrypt(self, private_key, ciphertext):
        private_key = RSA.importKey(private_key)
        cipher = PKCS1_cipher.new(private_key)  # 生成一个解密的类
        decrypt_text = cipher.decrypt(base64.b64decode(ciphertext.decode()), 0)  # 先解码再进行解密
        # decrypt_text = decrypt_text.decode()  # 对文本内容进行解码
        return decrypt_text

    # 数字签名，使用私钥对数据进行签名，data为bytes类型
    def rsa_private_sign(self,private_key,data):
        private_key = RSA.importKey(private_key) # 导入私钥
        signer = PKCS1_signature.new(private_key)  # 设置签名的类
        digest = SHA.new() # 创建sha加密的类
        digest.update(data)  # 将要加密的数据进行sha加密
        sign = signer.sign(digest)  # 对数据进行签名
        # 对签名进行处理
        signature = base64.b64encode(sign)  # 对数据进行base64加密
        signature = signature.decode()  # 再进行编码
        return signature

    # 数字签名，使用公钥钥对签名进行验证，data为bytes类型，与rsa_private_sign()的data参数值一致
    def rsa_public_check_sign(self,public_key,sign,data):
        publick_key = RSA.importKey(public_key)  # 导入公钥
        verifier = PKCS1_signature.new(publick_key)  # 生成验证信息的类
        digest = SHA.new()  # 创建一个sha加密的类
        digest.update(data)  # 将获取到的数据进行sha加密
        Check_sign = verifier.verify(digest, base64.b64decode(sign))  # 对数据进行验证，返回bool值
        return Check_sign


    # def create_server_rsa_pair(self):
    #     rsa = RSA.generate(1024)  # 生成一个私钥
    #     self.server_private_key = rsa.exportKey()  # 导出私钥
    #     # private_key = rsa.exportKey()
    #     print("private_key:",self.server_private_key.decode())
    #     # 生成公钥
    #     self.server_public_key = rsa.publickey().exportKey()  # 生成私钥所对应的公钥
    #     print("public_key:",self.server_public_key.decode())

