# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-09-02 11:04:55
# @Last Modified by:   shanzhuAndfish
# @Last Modified time: 2022-09-02 14:05:29

import configparser

class Config():

	def __init__(self, file_path):
		self._config_path = file_path
		self._config_parser = configparser.ConfigParser()
		self._config_parser.read(self._config_path)

	def get(self, key, default=None):
		if key in self._config_parser.sections():
			return self._config_parser._transfer_to_dict(key)
		else:
			return default

	def sections(self):
		return self._config_parser.sections()

	def __getitem__(self, key):
		return self._transfer_to_dict(key)

	def _transfer_to_dict(self, key):
		option_dict = {}
		options = self._config_parser.options(key)
		for option in options:
			option_dict[option] = self._config_parser.get(key, option)
		return option_dict
