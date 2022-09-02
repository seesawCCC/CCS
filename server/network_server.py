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
from secagg.shared.secagg_messages import ServerToClientWrapperMessage,ShareKeysRequest,MaskedInputCollectionRequest
from secagg.shared.secagg_messages import UnmaskingRequest
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

        # 改成局部变量
        # self.inputs = [self.communication_socket,self.register_socket]
        # self.outputs = []
        # self.excepts = [self.communication_socket,self.register_socket]

        self.client_message = {}
        self.message_lock = threading.Lock()
        self.rsa = RsaEncryption()
        self.server_public_key = self.rsa.server_public_key
        self.server_private_key = self.rsa.server_private_key
        # self.client_list = []
        self.client_flag = 0
        self._plus_nonce = random.randint(1, 4096)
        self.UserPool = UserPool()
        self.aes = AesGcmEncryption()
        self.MaskedInput = []

    # 监听两个线程
    def listen(self):
        # 注册线程
        listen_thread = threading.Thread(target=self.register,args=(self.register_socket,))
        listen_thread.start()
        # 通信线程
        listen_thread = threading.Thread(target=self.communication,args=(self.communication_socket,))
        listen_thread.start()
        return True

    # 注册线程
    def register(self,register_socket):
        socket_table = {}
        inputs = [register_socket]
        outputs = []
        excepts = [register_socket]
        while inputs:
            # time.sleep(1)
            print('start select')
            print("client_message-----",self.client_message)
            print(inputs)
            readable, writeable, exception = select.select(inputs, outputs, excepts)
            print(readable)
            if readable:
                print(readable)
            for sock in readable:
                if getattr(sock, '_closed'):
                    print('Threading: this socket is closed', sock)
                    inputs.remove(sock)
                    excepts.remove(sock)
                    continue
                # 服务器套接字
                if sock is register_socket:
                    client_socket, client_address = sock.accept()
                    print(client_address, ' start link')
                    client_tag = ''.join([str(item) for item in client_address])
                    print("client_tag",client_tag)
                    socket_table[client_socket] = client_tag
                    self.client_message[client_tag] = []
                    # 将客户套接字存入input
                    inputs.append(client_socket)
                    # outputs.append(client_socket)
                    excepts.append(client_socket)
                # 客户套接字
                else:
                    try:
                        # 从套接字中取出数据
                        data = sock.recv(4096)
                        if data:
                            # print(pickle.loads(data))
                            print(data)
                            # 此处调用data_process()
                            result = self.data_process_1(data)
                            sock.send(result)
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
                        inputs.remove(sock)
                        # outputs.remove(sock)
                        excepts.remove(sock)

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
                excepts.remove(sock)
                # outputs.remove(sock)
                inputs.remove(sock)
                with self.message_lock:
                    self.client_message.pop(sock)
                sock.close()
        print('ok, threading over')


    # 通信线程
    # def sing(s, inputs, outputs, excepts, client_message, message_lock):
    def communication(self,communication_socket):
        socket_table = {}
        inputs = [communication_socket]
        outputs = []
        excepts = [communication_socket]
        while inputs:
            # time.sleep(1)
            print('start select')
            print("client_message-----",self.client_message)
            print(inputs)
            readable, writeable, exception = select.select(inputs, outputs, excepts)
            print(readable)
            if readable:
                print(readable)
            for sock in readable:
                if getattr(sock, '_closed'):
                    print('Threading: this socket is closed', sock)
                    inputs.remove(sock)
                    excepts.remove(sock)
                    continue
                # 服务器套接字
                if sock is communication_socket:
                    client_socket, client_address = sock.accept()
                    # 提前判断client_address是否已注册
                    existed = self.UserPool.existed(client_address)
                    if existed:
                        callback = "{}:{}".format(*client_address)
                        self.UserPool.SetSocket(callback,client_socket)
                        print(client_address, ' start link')
                        # client_tag = ''.join([str(item) for item in client_address])
                        print("client_tag",callback)
                        socket_table[client_socket] = callback
                        self.client_message[callback] = []
                        # 将客户套接字存入input
                        inputs.append(client_socket)
                        # outputs.append(client_socket)
                        excepts.append(client_socket)
                # 客户套接字
                else:
                    try:
                        # 从套接字中取出数据
                        data = sock.recv(4096)
                        if data:
                            # sock.send(b'ok')
                            with self.message_lock:
                                # 要用client_message的话，可以只用client_message[callback]，将socket_table[sock]替换为回调地址
                                # client_message用于存储客户发送的数据
                                callback = socket_table[sock]
                                self.client_message[callback].append(data)
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
                        inputs.remove(sock)
                        # outputs.remove(sock)
                        excepts.remove(sock)

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
                excepts.remove(sock)
                # outputs.remove(sock)
                inputs.remove(sock)
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
        # communication_socket状态
        msg['status'] = 0
        msg['last_nonce'] = client_nonce
        # User[client_callback] = msg
        # 在用户池中添加用户
        self.UserPool.AddUser(client_callback,msg)

        data['clientId'] = self.client_flag
        self.client_flag = self.client_flag+1

        server_encry_data = self.rsa.Encrypt(client_public_key, pickle.dumps(data))

        return server_encry_data

    # action2--服务器任务:
    # 1.处理客户
    # 输入：
    # 输出：
    def data_process_2(self,message):
        pass

    # R0--服务器任务:仅分发客户的两个公钥
    # 1.记录当前在线用户集合，判断是否到达阈值t
    # #client_message[callback]   可取出消息  ----根据callback取出两个公钥以及用户id
    # 2.向用户集合U1分发客户的两个公钥
    # 输入：client_message客户信息列表，t阈值, UserAddress是在线用户的回调地址列表
    # 输出：通过套接字向用户集合分发公钥
    def server_r0(self,client_message,t,UserAddress):
        try:
            # 判断在线用户数量
            if len(UserAddress) < t:
                raise Exception('abort')
            else:
                # UserAddress = self.UserPool.GetAllUserAddress()
                pair_of_public_keys = []
                # 循环取出客户的两个公钥
                for i in UserAddress:
                    user = self.UserPool.GetUserByAddress(i)
                    # 取出对应客户的加密数据和通信密钥
                    encry_message = client_message[i]
                    enc_key = user['enc_key']
                    decry_message = self.aes.Decrypt(enc_key, encry_message)
                    message = pickle.loads(decry_message)
                    #再从message中取出两个公钥  -----ClientToServerWrapperMessage对象
                    keys = message.advertise_keys().pair_of_public_keys()
                    pair_of_public_keys.append(keys)
                Keys = ShareKeysRequest()
                Keys.set_pairs_of_public_keys(pair_of_public_keys)
                msg=ServerToClientWrapperMessage()
                msg.set_share_keys_request(Keys)
                # 将msg发送至客户套接字   ---msg为ServerToClientWrapperMessage类型
                for j in UserAddress:
                    user = self.UserPool.GetUserByAddress(j)
                    enc_key = user['enc_key']
                    try:
                        sock = self.UserPool.GetSocket(j)
                        # 序列化之后进行enc_key加密
                        encry_message = self.aes.Decrypt(enc_key,pickle.dumps(msg))
                        sock.send(encry_message)
                    except Exception as e:
                        self.UserPool.Remove(j)
                        print(e)
        except Exception as e:
            print(e)

    # R1--服务器任务:仅分发cij---用通信密钥加密的秘密共享内容bi,ski1
    # 1.从ClientToServerWrapperMessage对象取出share_keys_response.encrypted_key_shares cij
    # 将encrypted_key_shares放入ServerToClientWrapperMessage对象的_masked_input_request中
    # 输入：client_message客户信息列表，t阈值，UserAddress1表示R0在线用户列表
    # 输出：通过套接字向用户集合分发秘密
    def server_r1(self,client_message,t,UserAddress1):
        try:
            # 判断在线用户数量
            if len(UserAddress1) < t:
                raise Exception('abort')
            else:
                # UserAddress = self.UserPool.GetAllUserAddress()
                encrypted_key_shares = []
                # 循环取出客户发送的cij
                for i in UserAddress1:
                    user = self.UserPool.GetUserByAddress(i)
                    # 取出对应客户的加密数据和通信密钥
                    encry_message = client_message[i]
                    enc_key = user['enc_key']
                    decry_message = self.aes.Decrypt(enc_key, encry_message)
                    message = pickle.loads(decry_message)
                    #message  -----ClientToServerWrapperMessage对象
                    key_shares = message.share_keys_response().encrypted_key_shares()
                    # noise_pk = pair_of_public_keys.noise_pk()
                    # enc_pk = pair_of_public_keys.enc_pk()
                    encrypted_key_shares.append(key_shares)
                MaskedInput = MaskedInputCollectionRequest()
                MaskedInput.set_encrypted_key_shares(encrypted_key_shares)
                msg=ServerToClientWrapperMessage()
                msg.set_masked_input_request(MaskedInput)
                # 将msg发送至客户套接字   ---msg为ServerToClientWrapperMessage类型
                for j in UserAddress1:
                    user = self.UserPool.GetUserByAddress(j)
                    enc_key = user['enc_key']
                    try:
                        sock = self.UserPool.GetSocket(j)
                        # 序列化之后进行enc_key加密
                        encry_message = self.aes.Decrypt(enc_key,pickle.dumps(msg))
                        sock.send(encry_message)
                    except Exception as e:
                        self.UserPool.Remove(j)
                        print(e)
        except Exception as e:
            print(e)

    # R2--服务器任务:在一定时间内，接收用户发来的掩码，向当前仍在线的用户发送用户集
    # 1.从ClientToServerWrapperMessage对象取出掩码 服务器存储掩码
    # 服务器发送当前在线用户以及上一轮掉线用户分发出去
    # 输入：client_message客户信息列表，t阈值，UserAddress列表，UserAddress1表示R0在线用户列表,UserAddress2表示R1在线用户列表
    # UserAddress列表和公钥列表id相同
    # 输出：通过套接字向用户集合分发秘密
    def server_r2(self,client_message,t,UserAddress,UserAddress1,UserAddress2):
        try:
            # 判断在线用户数量
            if len(UserAddress2) < t:
                raise Exception('abort')
            else:
                # 循环取出客户发送的掩码
                for i in UserAddress2:
                    user = self.UserPool.GetUserByAddress(i)
                    # 取出对应客户的加密数据和通信密钥
                    encry_message = client_message[i]
                    enc_key = user['enc_key']
                    decry_message = self.aes.Decrypt(enc_key, encry_message)
                    message = pickle.loads(decry_message)
                    #masked为掩码,服务器存储掩码
                    masked = message.masked_input_response().vectors()
                    self.MaskedInput.append(masked)
                # 分发用户聚合
                dead_3_client_ids = []
                for j in UserAddress1:
                    # R2掉线的用户
                    if j not in UserAddress2:
                        client_id = UserAddress.index(j)+1
                        dead_3_client_ids.append(client_id)
                unmasking_request = UnmaskingRequest()
                unmasking_request.set_dead_3_client_ids(dead_3_client_ids)
                msg=ServerToClientWrapperMessage()
                msg.set_unmasking_request(unmasking_request)
                # 将msg发送至客户套接字   ---msg为ServerToClientWrapperMessage类型
                for k in UserAddress2:
                    user = self.UserPool.GetUserByAddress(k)
                    enc_key = user['enc_key']
                    try:
                        sock = self.UserPool.GetSocket(k)
                        # 序列化之后进行enc_key加密
                        encry_message = self.aes.Decrypt(enc_key,pickle.dumps(msg))
                        sock.send(encry_message)
                    except Exception as e:
                        self.UserPool.Remove(k)
                        print(e)
        except Exception as e:
            print(e)
        pass

    # R3--服务器任务:
    # 1.根据不同用户集恢复秘密---恢复ri和mij
    # 2.进行聚合
    # 输入：client_message客户信息列表，t阈值，UserAddress在线用户列表
    # 输出：通过套接字向用户集合分发秘密
    def server_r3(self,client_message):
        pass

    def GenerateGraph(self):
        pass

