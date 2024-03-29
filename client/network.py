# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-08-12 21:30:31
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-21 17:24:56

import socket
import traceback
# import json
import pickle
import threading
import random
import hashlib
import select
import time

from base.monitoring import FCP_CHECK
from base.rsa_encryption import RsaEncryption
from secagg.shared.aes_gcm_encryption import AesGcmEncryption

class ServerAddr():
    def __init__(self, register_ip, register_port):
        self._server_register_ip = register_ip
        self._server_register_port = int(register_port)
        self._communication_ip = ''
        self._communication_port = 0

    def set_communication_address(self, callback):
        host, port = callback.split(':')
        port = int(port)
        self._communication_ip = host
        self._communication_port = port

    def get_register_address(self):
        return (self._server_register_ip, self._server_register_port)

    def get_communication_address(self):
        return (self._communication_ip, self._communication_port)

class CloseSocketException(Exception):
    def __init__(self, socket_tuple):
        self._socket_ip, self._socket_port = socket_tuple

    def __str__(self):
        return "socket {}:{} has been closed by other side".format(self._socket_ip, self._socket_port)

class Network():

    # example:
    # server_addr = ServerAddr(server_register_ip, server_register_port)
    # network = Network('127.0.0.1', communication_port, register_port, server_addr, server_public_key)
    # enc_key = network.register()
    # network.connect_to_server()
    # network.listen()
    # 可以通过network.send_to_server 方法向服务器发送数据

    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._class_lock:
            if not cls.__dict__.get('_instance', None):
                cls._instance = super(Network, cls).__new__(cls)
        return cls._instance

    # communication_port, register_port 都是客户端的端口
    # 对应的服务器地址存储在server_addr中
    def __init__(self, host, communication_port, register_port, server_addr, server_public_key):
        self._host = host
        self._communication_port = communication_port
        self._register_port = register_port
        self._server_addr = server_addr
        self._client_id = ''

        self._server_public_key = server_public_key
        self._rsa_encryption = RsaEncryption()
        # 公私钥都是 bytes
        self._private_key, self._public_key = self._rsa_encryption.create_rsa_pair()
        self._plus_nonce = random.randint(1, 4096)

        # self._connect_server_socket = self._get_socket(self._host, self._communication_port)
        self._connect_server_socket = None
        self._message_list_lock = threading.Lock()
        self._receive_messages = []

        self._aes_gcm = AesGcmEncryption()
        self._other_client_addrs = []

        self._over = True


    def get_message_lock(self):
        return self._message_list_lock

    def get_receive_messages(self):
        return self._receive_messages

    def get_client_id(self):
        return self._client_id

    def isOver(self):
        return self._over or getattr(self._connect_server_socket, '_closed')

    def register(self):
        register_socket = None
        server_enc_key = b''
        
        register_socket = self._get_socket(self._host, self._register_port)
        register_socket.settimeout(6.0)
        FCP_CHECK(self._connect(register_socket, self._server_addr.get_register_address()))
        try:
            # message内部数据str只能是unicode(utf-8)
            message = {}
            message['action'] = 1
            message['public'] = self._public_key.decode()
            # 自己的与服务器通信地址，以及一个不重数
            callback = "{}:{}".format(self._host, self._communication_port)
            nonce = int(time.time())+self._plus_nonce
            # hash_str = self._compute_hash(self._public_key, ','.join(callback, str(nonce)))
            register_information = {'callback': callback, 'nonce': nonce}
            message['callback'] = callback
            message['nonce'] = nonce


            # sign 对register_information进行数字签名--要求在服务器端能取出以验证身份
            sign_register_information = self._rsa_encryption.rsa_private_sign(self._private_key, pickle.dumps(register_information))
            message['sign'] = sign_register_information
            server_encry_data = self._rsa_encryption.Encrypt(self._server_public_key, pickle.dumps(message))

            register_socket.sendall(server_encry_data)
            # 服务器处理

            encry_reply = register_socket.recv(4096)
            # Check reply
            decry_reply_pickle = self._rsa_encryption.Decrypt(self._private_key, encry_reply)
            decry_reply = pickle.loads(decry_reply_pickle)
            FCP_CHECK(decry_reply['action'] == 1)
            # resign
            FCP_CHECK(decry_reply['sign_result'])
            # reply_json = self._rsa_encryption.Decrypt(self._server_public_key, decry_reply['sign'])
            # reply = json.loads(reply_json)
            server_enc_key = decry_reply['enc_key']

            self._client_id = decry_reply['clientId']
            callback = decry_reply['callback']
            self._server_addr.set_communication_address(callback)
            # hash_str = self._compute_hash(reply['enc_key'], ','.join(callback, reply['client_id']))
            # FCP_CHECK(hash_str == reply['hash'])
        except Exception as e:
            traceback.print_exc()
            server_enc_key = b''
        finally:
            if register_socket:
                register_socket.shutdown(socket.SHUT_RDWR)
                register_socket.close()
            return server_enc_key

    # 连接服务器的通讯套接字
    def connect_to_server(self):
        try:
            # 生成套接字
            self._connect_server_socket = self._get_socket(self._host, self._communication_port)
            # self._connect_server_socket.settimeout(1.0)
            # 建立TCP连接
            self._connect(self._connect_server_socket, self._server_addr.get_communication_address())
            self._over = False
            return True
        except Exception as e:
            traceback.print_exc()
            if self._connect_server_socket:
                self._connect_server_socket.close()
                self._connect_server_socket = None
            return False

    def send_to_server(self, data):
        try:
            length = len(data)
            length_bytes = length.to_bytes(4, 'little')
            message = length_bytes+data
            print('send bytes: ', len(message))
            self._connect_server_socket.sendall(message)
            return True
        except Exception as e:
            traceback.print_exc()
            return False

    def listen(self):
        if not self._connect_server_socket:
            return False
        listen_thread = threading.Thread(target=self._listen_to_server)
        listen_thread.start()
        return True

    def _listen_to_server(self):
        inputs = [self._connect_server_socket]
        outputs = []
        excepts = [self._connect_server_socket]
        need_closed = []

        while inputs:
            need_closed.clear()
            readable, writeable, exception = select.select(inputs, outputs, excepts)
            for sock in readable:
                # 该socket已经关闭了, 客户端自己关闭socket
                if getattr(sock, '_closed'):
                    inputs.remove(sock)
                    excepts.remove(sock)
                else:
                    try:
                        data = self._recv_from_socket(sock)
                        if data:
                            with self._message_list_lock:
                                self._receive_messages.append(data)
                        else:
                            # 服务器关闭了连接
                            raise CloseSocketException(sock.getsockname())
                    except Exception as e:
                        print('the socket is closed ', sock)
                        need_closed.append(sock)
                        inputs.remove(sock)
                        excepts.remove(sock)

            for sock in exception:
                print('exception: ', sock)
                excepts.remove(sock)
                inputs.remove(sock)
                need_closed.append(sock)

            for sock in need_closed:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except Exception as e:
                    pass
                finally:
                    sock.close()
        self._over = True
        print('over threading')

    def close(self):
        self._over = True
        if not self._connect_server_socket:
            return None
        try:
            if not getattr(self._connect_server_socket, '_closed'):
                self._connect_server_socket.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            traceback.print_exc()
        finally:
            self._connect_server_socket.close()
            self._connect_server_socket = None

    def _connect(self, socket_, addr):
        try:
            socket_.connect(addr)
        except Exception as e:
            traceback.print_exc()
            return False
        else:
            return True

    def _get_socket(self, host, port):
        # 生成了一个TCP套接字
        socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket_.bind((host, port))
        return socket_

    # key: bytes
    # data: unicode
    # return unicode
    def _compute_hash(self, key, data):
        hobj = hashlib.sha256(key)
        hobj.update(data.encode('utf-8'))
        return hobj.hexdigest().upper()[:32]

    def _recv_from_socket(self, socket_):
        length_limit = 8192
        data = b''
        has_recv_len = 0

        recv_data = socket_.recv(length_limit)
        if recv_data:
            data_length = int.from_bytes(recv_data[:4], 'little')
            data += recv_data[4:]
            has_recv_len += len(data)
        else:
            return data

        data_set = [data]

        while has_recv_len < data_length:
            recv_data = socket_.recv(length_limit)
            has_recv_len += len(recv_data)
            data_set.append(recv_data)

        return b''.join(data_set)