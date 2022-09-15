# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-09-08 17:01:03
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-13 10:46:45

import sys, os, traceback
file_abs_path = __file__
if not os.path.isabs(file_abs_path):
	file_abs_path = os.path.abspath(__file__)

project_path = os.path.dirname(os.path.dirname(file_abs_path))
sys.path.append(project_path)

from server.server_controller import ServerController
from base.config import Config

config_ini = '\\'.join((project_path, 'server', 'config.ini'))

config = Config(config_ini)
server_controller = ServerController(config)

try:
	server_controller.run()
except Exception as e:
	traceback.print_exc()
finally:
	server_controller.close()
	exit(1)