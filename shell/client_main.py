# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-09-03 00:20:37
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-15 14:32:50

import sys, os, traceback

file_abs_path = __file__

if not os.path.isabs(file_abs_path):
	file_abs_path = os.path.abspath(__file__)

project_path = os.path.dirname(os.path.dirname(file_abs_path))

sys.path.append(project_path)

from client.client_controller import ClientController
from client.client_stream import ServerNetWorkOver
from base.config import Config

config_ini = '\\'.join((project_path, 'client', 'config.ini'))

config = Config(config_ini)
client_controller = ClientController(config)

try:
	client_controller.run()
except Exception as e:
	if not isinstance(e, ServerNetWorkOver):
		traceback.print_exc()
	else:
		print('train over')
finally:
	client_controller.close()