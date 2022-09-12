# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-09-03 00:20:37
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-12 20:40:03

import sys, os, traceback

file_abs_path = __file__

if not os.path.isabs(file_abs_path):
	file_abs_path = os.path.abspath(__file__)

project_path = os.path.dirname(os.path.dirname(file_abs_path))

sys.path.append(project_path)

from client.client_controller import ClientController
from base.config import Config

config_ini = '\\'.join((project_path, 'client', 'config.ini'))

config = Config(config_ini)
client_controller = ClientController(config)

try:
	client_controller.run()
except Exception as e:
	traceback.print_exc()

client_controller.close()