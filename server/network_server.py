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
import traceback
from base.rsa_encryption import RsaEncryption
from secagg.shared.aes_gcm_encryption import AesGcmEncryption
from secagg.shared.aes_key import AesKey
from secagg.shared.secagg_messages import ServerToClientWrapperMessage,ShareKeysRequest,MaskedInputCollectionRequest
from secagg.shared.secagg_messages import UnmaskingRequest
import os
from secagg.shared.secagg_vector import SecAggVector
from server.user_pool import UserPool
from secagg.shared.shamir_secret_sharing import ShamirSecretSharing,ShamirShare
from secagg.shared.ecdh_key_agreement import EcdhKeyAgreement
from secagg.shared.map_of_masks import MapOfMasks
from secagg.shared.compute_session_id import ComputeSessionId

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
        self.pairs_of_public_keys=[]
        self.share_keys = ShareKeysRequest()
        self.session_id = None

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
            readable, writeable, exception = select.select(inputs, outputs, excepts)
            # print('start register')
            # print("client_message-----",self.client_message)
            # if readable:
            #     print(readable)
            for sock in readable:
                if getattr(sock, '_closed'):
                    # print('Threading: this socket is closed', sock)
                    inputs.remove(sock)
                    excepts.remove(sock)
                    continue
                # 服务器套接字
                if sock is register_socket:
                    client_socket, client_address = sock.accept()
                    # print(client_address, ' start link')
                    client_tag = ''.join([str(item) for item in client_address])
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
                            # print(data)
                            # 此处调用data_process()
                            result = self.data_process_1(data)
                            sock.sendall(result)
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

            # if exception:
            #     print('some socket exception')
            #     print(exception)
            for sock in exception:
                if sock is register_socket:
                    print('server exception')
                    # 关了所有的连接
                    register_socket.close()
                    exit(-1)
                print(sock, 'in exceptions')
                excepts.remove(sock)
                # outputs.remove(sock)
                inputs.remove(sock)
                sock.close()
        print('ok, threading over')


    # 通信线程
    # def sing(s, inputs, outputs, excepts, client_message, message_lock):
    def communication(self,communication_socket):
        socket_table = {}
        inputs = [communication_socket]
        outputs = []
        excepts = [communication_socket]
        need_close=[]
        while inputs:
            # time.sleep(1)
            readable, writeable, exception = select.select(inputs, outputs, excepts)
            # print('start communication')
            # print("communication client_message-----",self.client_message)
            # print(inputs)
            # if readable:
            #     print(readable)
            for sock in readable:
                print('communication', sock)
                if getattr(sock, '_closed'):
                    if sock is communication_socket:
                        inputs.remove(sock)
                        excepts.remove(sock)
                        need_close = inputs[:]
                        inputs.clear()
                    else:
                        print('Threading: this socket is closed', sock)
                        inputs.remove(sock)
                        excepts.remove(sock)
                    continue
                # 服务器套接字
                if sock is communication_socket:
                    client_socket, client_address = sock.accept()
                    callback = '{}:{}'.format(*client_address)
                    # 提前判断client_address是否已注册
                    # existed = self.UserPool.existed(client_address)
                    existed = self.UserPool.existed(callback)
                    if existed:
                        callback = "{}:{}".format(*client_address)
                        print(client_address, ' start link')
                        # client_tag = ''.join([str(item) for item in client_address])
                        print("client_tag",callback)
                        socket_table[client_socket] = callback
                        self.client_message[callback] = []
                        # 将客户套接字存入input
                        inputs.append(client_socket)
                        # outputs.append(client_socket)
                        excepts.append(client_socket)
                        self.UserPool.SetSocket(callback,client_socket)
                        self.UserPool.SetConnection(callback, True)
                # 客户套接字
                else:
                    print('communication recv data from ', sock)
                    try:
                        # 从套接字中取出数据
                        # data = sock.recv(4096)
                        data = self.recv(sock)
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
                        # 调用socket_table
                        inputs.remove(sock)
                        # 移走掉线用户
                        callback = socket_table[sock]
                        self.UserPool.Remove(callback)
                        # outputs.remove(sock)
                        excepts.remove(sock)

            # if exception:
            #     print('some socket exception')
            #     print(exception)
            for sock in exception:
                if sock is communication_socket:
                    print('server exception')
                    # 关了所有的连接
                    communication_socket.close()
                    exit(-1)
                print(sock, 'in exceptions')
                excepts.remove(sock)
                # outputs.remove(sock)
                inputs.remove(sock)
                callback = socket_table[sock]
                self.UserPool.Remove(callback)
                with self.message_lock:
                    self.client_message.pop(sock)
                sock.close()
        for sock in need_close:
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

        # FCP_CHECK(message['action'] == 1)
        client_nonce = message['nonce']
        client_callback = message['callback']
        register_information = {'callback': client_callback, 'nonce': client_nonce}
        client_public_key = message['public'].encode()
        sign = message['sign']

        # 验证数字签名 结果为bool，签名内容为register_information
        # rsa.rsa_public_check_sign 将register_information修改为bytes
        sign_result = self.rsa.rsa_public_check_sign(client_public_key,sign,pickle.dumps(register_information))
        data['sign_result'] = sign_result

        callback = "{}:{}".format(self.host, self.communication_port)
        data['callback'] = callback
        nonce = int(time.time())+self._plus_nonce
        data['nonce'] = nonce
        data['action'] = 1

        # 利用AesKey生成通信密钥
        seed = os.urandom(32)
        enc_key = AesKey(seed,32)
        data['enc_key'] = enc_key.data()

        # 完成注册
        msg = {}
        msg['client_id'] = self.client_flag
        msg['enc_key'] = enc_key
        # msg['callback'] = client_callback
        msg['public_key'] = client_public_key
        # communication_socket状态
        msg['status'] = 0
        msg['last_nonce'] = client_nonce
        msg['socket'] = None
        msg['connection'] = False
        # 在用户池中添加用户
        self.UserPool.AddUser(client_callback,msg)

        data['clientId'] = self.client_flag
        self.client_flag = self.client_flag+1

        server_encry_data = self.rsa.Encrypt(client_public_key, pickle.dumps(data))

        return server_encry_data


    def Data_Decrypt(self,callback,client_message):
        user = self.UserPool.GetUserByAddress(callback)
        encry_message = client_message[callback]
        if bool(encry_message):
            encry_message = encry_message.pop(0)
        enc_key = user['enc_key']
        decry_message = self.aes.Decrypt(enc_key, encry_message)
        message = pickle.loads(decry_message)
        #再从message['data']中取出数据 -----ClientToServerWrapperMessage对象
        message = message['data']
        # 判断是否是abort
        abort = message.has_abort()
        return message,abort

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
                result = {}
                # 循环取出客户的两个公钥
                for i in UserAddress:
                    message,abort = self.Data_Decrypt(i,client_message)
                    if abort is False:  #指代用户在线
                        keys = message.advertise_keys().pair_of_public_keys()
                        self.share_keys.add_pairs_of_public_keys(keys)
                        self.pairs_of_public_keys.append(keys)
                    else:
                        user = self.UserPool.GetUserByAddress(i)
                        user['status'] = 0
                        self.pairs_of_public_keys.append('')
                self.session_id = ComputeSessionId(self.share_keys)
                Keys = ShareKeysRequest()
                Keys.set_pairs_of_public_keys(self.pairs_of_public_keys)
                Keys.set_session_id(self.session_id.data)
                msg=ServerToClientWrapperMessage()
                msg.set_share_keys_request(Keys)
                

                # 将msg发送至客户套接字   ---msg为ServerToClientWrapperMessage类型
                result['data'] = msg
                result['action'] = 4
                result ['time'] = int(time.time())
                for j in UserAddress:
                    user = self.UserPool.GetUserByAddress(j)
                    enc_key = user['enc_key']
                    try:
                        sock = self.UserPool.GetSocket(j)
                        # 序列化之后进行enc_key加密
                        encry_message = self.aes.Encrypt(enc_key,pickle.dumps(result))
                        # sock.send(encry_message)
                        self.send(sock, encry_message)
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
    def server_r1(self,client_message,t,UserAddress,UserAddress1):
        try:
            # 判断在线用户数量
            if len(UserAddress1) < t:
                raise Exception('abort')
            else:
                n = len(UserAddress)
                # 生成一个二维数组
                encrypted_key_shares = [[0 for i in range(n)] for j in range(n)]
                # 循环取出客户发送的cij
                for i in UserAddress1:
                    #message  -----ClientToServerWrapperMessage对象
                    message,abort = self.Data_Decrypt(i,client_message)
                    # 利用UserAddress确定下标
                    index = UserAddress.index(i)
                    if abort is False:
                        # -----------------------二维数组赋值--------------------------
                        key_shares = message.share_keys_response().encrypted_key_shares()

                        encrypted_key_shares[index] = key_shares
                    else:
                        user = self.UserPool.GetUserByAddress(i)
                        user['status'] = 0
                        encrypted_key_shares[index] = [0]*n
                # encrypted_key_shares此时为二维数组 ,利用zip函数进行转置
                aT=list(map(list,zip(*encrypted_key_shares)))
                for j in UserAddress1:
                    result={}
                    index = UserAddress.index(j)
                    MaskedInput = MaskedInputCollectionRequest()
                    MaskedInput.set_encrypted_key_shares(aT[index])
                    msg=ServerToClientWrapperMessage()
                    msg.set_masked_input_request(MaskedInput)
                    # 将msg发送至客户套接字   ---msg为ServerToClientWrapperMessage类型
                    result['data'] = msg
                    result['action'] = 4
                    result ['time'] = int(time.time())
                    user = self.UserPool.GetUserByAddress(j)
                    enc_key = user['enc_key']
                    try:
                        sock = self.UserPool.GetSocket(j)
                        # 序列化之后进行enc_key加密
                        encry_message = self.aes.Encrypt(enc_key,pickle.dumps(result))
                        # sock.send(encry_message)
                        self.send(sock, encry_message)
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
                dead_3_client_ids = []
                # 循环取出客户发送的掩码
                for i in UserAddress2:
                    message,abort = self.Data_Decrypt(i,client_message)
                    if abort is False:
                        #masked为掩码,服务器存储掩码
                        masked = message.masked_input_response().vectors()
                        self.MaskedInput.append(masked)
                    else:
                        user = self.UserPool.GetUserByAddress(i)
                        user['status'] = 0
                        client_id = UserAddress.index(i)+1
                        dead_3_client_ids.append(client_id)
                # 分发用户集合
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
                result = {}
                result['data'] = msg
                result['action'] = 4
                result ['time'] = int(time.time())
                for k in UserAddress2:
                    user = self.UserPool.GetUserByAddress(k)
                    enc_key = user['enc_key']
                    try:
                        sock = self.UserPool.GetSocket(k)
                        # 序列化之后进行enc_key加密
                        encry_message = self.aes.Encrypt(enc_key,pickle.dumps(result))
                        # sock.send(encry_message)
                        self.send(sock, encry_message)
                    except Exception as e:
                        self.UserPool.Remove(k)
                        print(e)
        except Exception as e:
            print(e)

    # 返回SecAggVector对象
    def AddSecAggVectors(self, v1, v2):
        # FCP_CHECK(v1.modulus() == v2.modulus());
        if v1.modulus() == v2.modulus():
            modulus = v1.modulus()
        vec1 = SecAggVector(v1).GetAsUint64Vector()
        vec2 = SecAggVector(v2).GetAsUint64Vector()
        # FCP_CHECK(vec1.size() == vec2.size());
        for i in range(vec1.size()):
            vec1[i] = ((vec1[i] + vec2[i]) % modulus)
        return SecAggVector(vec1, modulus)
    # R3--服务器任务:
    # 1.根据不同用户集恢复秘密---恢复ri和mij----调用ShamirSecretSharing.Reconstruct
    # 2.进行聚合
    # 输入：client_message客户信息列表，t阈值，UserAddress在线用户列表
    # 输出：通过套接字向用户集合分发秘密
    def server_r3(self,client_message,t,UserAddress,UserAddress1,UserAddress2,UserAddress3,input_vector_specs,
                     prng_factory, async_abort):
        sum_vector = {}
        try:
            # 判断在线用户数量
            if len(UserAddress3) < t:
                raise Exception('abort')
            else:
                n = len(UserAddress)
                # 生成一个二维数组
                ss = ShamirSecretSharing()

                self.ri = [0]*n
                self.mij = [[0 for i in range(n)] for j in range(n)]
                noise_sk_share = [[0 for i in range(n)] for j in range(n)]
                prf_sk_share = [[0 for i in range(n)] for j in range(n)]
                # 循环取出客户发送的秘密
                for i in UserAddress3:
                    message,abort = self.Data_Decrypt(i,client_message)
                    m = UserAddress.index(i)
                    if abort is False:
                        # 获取NoiseOrPrfKeyShare对象列表
                        unmasking_response = message.unmasking_response().noise_or_prf_key_shares()
                        # 构造二维数组
                        for j in UserAddress1:
                            if j not in UserAddress2:
                                index = UserAddress.index(j)
                                # r1在线但是r2不在线的用户，获取noise_sk
                                noise_sk = unmasking_response[index].noise_sk_share()
                                noise_sk_share[m][index] = ShamirShare(noise_sk)
                            else:
                                index = UserAddress.index(j)
                                # r2在线用户，获取prf_sk
                                prf_sk = unmasking_response[index].prf_sk_share()
                                prf_sk_share[m][index] = ShamirShare(prf_sk)
                    else:
                        user = self.UserPool.GetUserByAddress(i)
                        user['status'] = 0
                # 秘密恢复
                # noise_sk_share、prf_sk_share此时为二维数组 ,利用zip函数进行转置
                prng_keys_to_add = []
                prng_keys_to_subtract = []
                noise_sk_share_aT=list(map(list,zip(*noise_sk_share)))
                prf_sk_share_aT=list(map(list,zip(*prf_sk_share)))
                for j in UserAddress1:
                    if j not in UserAddress2:
                        index = UserAddress.index(j)
                        # r1在线但是r2不在线的用户，根据noise_sk恢复ski----mij
                        noise = noise_sk_share_aT[index]
                        ski = ss.Reconstruct(t,noise,32)
                        KA = EcdhKeyAgreement()
                        ka = KA.CreateFromPrivateKey(ski).value()
                        for k in range(len(UserAddress)):
                            if k!=index:
                                pk = self.pairs_of_public_keys[k].noise_pk()
                                if bool(pk):
                                    sij = ka.ComputeSharedSecret(pk).data()
                                    # 此处传一个公钥 比较ij后放入add/substract    i----index j----k
                                    if index > k:
                                        prng_keys_to_add.append(sij)
                                    else:
                                        prng_keys_to_subtract.append(sij)
                    else:
                        index = UserAddress.index(j)
                        # r2在线用户，根据prf_sk恢复出bi-----ri
                        prf = prf_sk_share_aT[index]
                        bi = ss.Reconstruct(t,prf,32)
                        prng_keys_to_subtract.append(bi)
                # 计算掩码
                session_id = self.session_id
                if not session_id:                
                    session_id = ComputeSessionId(self.share_keys)
                mask = MapOfMasks(prng_keys_to_add,prng_keys_to_subtract, input_vector_specs,
                                  session_id, prng_factory, async_abort)
                c_number = len(UserAddress2)
                for spec in input_vector_specs:
                    key = spec.name()
                    for m in self.MaskedInput:
                        sum_vector[key] = self.AddSecAggVectors(sum_vector[key],m[key])
                    sum_vector[key] = self.AddSecAggVectors(sum_vector[key],mask[key])
                    # 计算均值
                    vec = sum_vector[key].GetAsUint64Vector()
                    for i in range(vec.size()):
                        vec[i] = vec[i]/c_number
                    sum_vector[key] = SecAggVector(vec, vec.modulus)
        except Exception as e:
            print(e)
        return sum_vector

    def GenerateGraph(self):
        pass

    def Close(self):
        self._close_socket(self.register_socket)
        self._close_socket(self.communication_socket)

    def _close_socket(self, socket):
        try:
            socket.close()
        except Exception as e:
            print(e)
            return False
        return True

    def send(self, socket_, message):
        message_length = len(message)
        length_bytes = message_length.to_bytes(4, 'little')
        message = length_bytes + message
        socket_.sendall(message)

    def recv(self, socket_):
        length_limit = 4096
        data = b''
        recv_data = socket_.recv(length_limit)
        if recv_data:
            data_length = int.from_bytes(recv_data[:4], 'little')
            data += recv_data[4:]
        else:
            return recv_data

        while len(data) < data_length:
            recv_data = socket_.recv(length_limit)
            data += recv_data
        return data        