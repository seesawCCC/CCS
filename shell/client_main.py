# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-09-03 00:20:37
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-07 17:05:18

import sys, os

project_path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_path)

from client.client_controller import ClientController
from base.config import Config

config_ini = '\\'.join((project_path, 'client', 'config.ini'))

config = Config(config_ini)
client_controller = ClientController(config)

client_controller.run()