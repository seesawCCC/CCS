# -*- coding: utf-8 -*-
# @Time : 2022/7/19 12:08
# @Author : LRX
# @Site : 
# @File : aes_ctr_prng_factory.py
# @Software: PyCharm

from .aes_ctr_prng import AesCtrPrng

class AesCtrPrngFactory:
    # def __init__(self):

    def MakePrng(self,key):
        return AesCtrPrng(key)
