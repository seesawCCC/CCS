# -*- coding: utf-8 -*-
# @Time : 2022/8/17 10:49
# @Author : LRX
# @Site : 
# @File : network_server.py
# @Software: PyCharm

import socket
import select
import time
import threading
import random
import pickle
import sys
from base.monitoring import FCP_CHECK
from base.rsa_encryption import RsaEncryption
from secagg.shared.aes_gcm_encryption import AesGcmEncryption
from Crypto.Random import get_random_bytes
from secagg.shared.aes_key import AesKey
import os
from service.user_pool import UserPool

class ServerSocket:
    def __init__(self, host, communication_port,register_port):
        # host = '127.0.0.1'
        self.host = host
        self.communication_port = communication_port
        self.register_port = register_port
        # 连接套接字
        self.register_socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.register_socket.bind((host,register_port))
        self.register_socket.listen(20)
        # 通信套接字
        self.communication_socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.communication_socket.bind((host,communication_port))
        self.communication_socket.listen(20)
        self.inputs = [self.communication_socket,self.register_socket]
        self.outputs = []
        self.excepts = [self.communication_socket,self.register_socket]
        self.client_message = {}
        self.message_lock = threading.Lock()
        self.rsa = RsaEncryption()
        self.server_public_key = self.rsa.server_public_key
        self.server_private_key = self.rsa.server_private_key
        # self.client_list = []
        self.client_flag = 0
        self._plus_nonce = random.randint(1, 4096)
        self.UserPool = UserPool()

    # def sing(s, inputs, outputs, excepts, client_message, message_lock):
    def sing(self):
        socket_table = {}
        while self.inputs:
            # time.sleep(1)
            print('start select')
            print("client_message-----",self.client_message)
            print(self.inputs)
            readable, writeable, exception = select.select(self.inputs, self.outputs, self.excepts)
            print(readable)
            if readable:
                print(readable)
            for sock in readable:
                if getattr(sock, '_closed'):
                    print('Threading: this socket is closed', sock)
                    self.inputs.remove(sock)
                    self.excepts.remove(sock)
                    continue
                # 服务器套接字
                if sock is self.communication_socket:
                    client_socket, client_address = sock.accept()
                    print(client_address, ' start link')
                    client_tag = ''.join([str(item) for item in client_address])
                    print("client_tag",client_tag)
                    socket_table[client_socket] = client_tag
                    self.client_message[client_tag] = []
                    # 将客户套接字存入input
                    self.inputs.append(client_socket)
                    # outputs.append(client_socket)
                    self.excepts.append(client_socket)
                # 客户套接字
                else:
                    try:
                        # 从套接字中取出数据
                        data = sock.recv(4096)
                        if data:
                            # print(pickle.loads(data))
                            print(data)
                            # 此处调用data_process()
                            sock.send(b'ok')
                            with self.message_lock:
                                self.client_message[socket_table[sock]].append(data)
                            # # 存放需要进行回复操作的socket
                            # if sock not in self.outputs:
                            #     self.outputs.append(sock)
                        else:
                            raise Exception('no data, need to be closed')
                    # raise Exception('close the socket')
                    except Exception as e:
                        print(e)
                        print(sock, ' need to be closed')
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()
                        self.inputs.remove(sock)
                        # outputs.remove(sock)
                        self.excepts.remove(sock)

            if exception:
                print('some socket exception')
                print(exception)
            for sock in exception:
                if sock is self.communication_socket:
                    print('server exception')
                    # 关了所有的连接
                    self.communication_socket.close()
                    exit(-1)
                print(sock, 'in exceptions')
                self.excepts.remove(sock)
                # outputs.remove(sock)
                self.inputs.remove(sock)
                with self.message_lock:
                    self.client_message.pop(sock)
                sock.close()
        print('ok, threading over')

    # action1--服务器任务:
    # 1.处理客户注册，使用数字签名验证身份，利用私钥解密数据
    # 2.将注册客户添加进客户列表中，当数量大于n值，执行生成图算法
    # 3.返回给客户信息：回调地址、客户ID、通信密钥（随机生成32位）、时间戳
    # 输入：message{}
    # 输出：data{}
    # 65行进行调用

    def data_process_1(self,message):
        data={}

        # 解密数据，转换类型
        message_pickle = self.rsa.Decrypt(self.server_private_key,message)
        message = pickle.loads(message_pickle)

        FCP_CHECK(message['action'] == 1)
        client_nonce = message['nonce']
        client_callback = message['callback']
        register_information = {'callback': client_callback, 'nonce': client_nonce}
        client_public_key = message['public'].encode()
        sign = message['sign']

        # 验证数字签名 结果为bool，签名内容为register_information
        sign_result = self.rsa.rsa_public_check_sign(client_public_key,sign,register_information)
        data['sign_result'] = sign_result

        callback = "{}:{}".format(self.host, self.communication_port)
        data['callback'] = callback
        nonce = int(time.time())+self._plus_nonce
        data['nonce'] = nonce
        data['action'] = 1

        # 利用AesKey生成通信密钥
        seed = os.urandom(32)
        enc_key = AesKey(seed,32)
        data['enc_key'] = enc_key

        # 完成注册
        User={}
        msg = {}
        msg['client_id'] = self.client_flag
        msg['enc_key'] = enc_key
        # msg['callback'] = client_callback
        msg['public_key'] = client_public_key
        msg['status'] = 1
        msg['last_nonce'] = client_nonce
        User[client_callback] = msg
        # 在用户池中添加用户
        self.UserPool.AddUser(callback,User)

        data['clientId'] = self.client_flag
        self.client_flag = self.client_flag+1

        server_encry_data = self.rsa.Encrypt(client_public_key, pickle.dumps(data))

        return server_encry_data

    def GenerateGraph(self):
        pass

