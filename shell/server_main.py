# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-09-08 17:01:03
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-08 17:15:01

import sys, os

project_path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_path)

from server.server_controller import ServerController
from base.config import Config

config_ini = '\\'.join((project_path, 'server', 'config.ini'))

config = Config(config_ini)
server_controller = ServerController(config)

server_controller.run()