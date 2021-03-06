# -*- coding: utf-8 -*-
# @Time : 2022/7/19 10:55
# @Author : LRX
# @Site : 
# @File : aes_ctr_prng.py
# @Software: PyCharm


from .aes_key import AesKey

# 参数定义
kIvSize = 16 #IV size, in bytes

 # Constructs the PRNG with the given seed, and an IV of all zeroes.
 # This is ONLY secure if the seed is never used more than once.

# Number of AES blocks in the cache.
# The number of blocks is optimized to make kCacheSize to be a multiple
# of any possible number of bytes in a SecAgg output (i.e. 1 to 8).
kBatchSize = 3 * 5 * 7

# Block size, in bytes
kBlockSize = 16

# Size of our cache, in bytes. We cache blocks to save leftover bytes.
kCacheSize = kBatchSize * kBlockSize

# For security, we don't want to generate more than 2^32-1 blocks.
kMaxBlocks = 0xFFFFFFFF

# Fills the selected cache with deterministic pseudorandomly generated bytes.
# After this, the associated next_byte_pos counter must be set to 0.

 # This is used to generate bytes.
# kAllZeroes[kCacheSize] = {0};

class AesCtrPrng:
    def __init__(self,seed):
        # memset(iv, 0, kIvSize) 此处memset函数不知其意
        # FCP_CHECK(ctx_ = EVP_CIPHER_CTX_new());
        # FCP_CHECK(1 == EVP_EncryptInit_ex(ctx_, EVP_aes_256_ctr(), nullptr,
        #                           seed.data(), iv));
        # if ctx_ = EVP_CIPHER_CTX_new() and 1 == EVP_EncryptInit_ex(ctx_, EVP_aes_256_ctr(), nullptr, seed.data(), iv)
        self.next_byte_pos = kCacheSize
        self.blocks_generated = 0

    def GenerateBytes(self,cache,cache_size):
        if (cache_size % kBlockSize) == 0 :
            print("Number of bytes generated by AesCtrPrng must be a multiple of "+kBlockSize)
        if cache_size <= kCacheSize :
            print("Requested number of bytes "+cache_size)
            print(" exceeds maximum cache size " +kCacheSize)
        if self.blocks_generated <= kMaxBlocks :
            print("AesCtrPrng generated " +kMaxBlocks)
            print(" blocks and needs a new seed.")
        # FCP_CHECK(
        #     EVP_EncryptUpdate(ctx_, cache, &bytes_written, kAllZeroes, cache_size));
        # FCP_CHECK(bytes_written == cache_size);
        self.blocks_generated = self.blocks_generated + (cache_size) / kBlockSize

        return None

    def Rand8(self):
        if self.next_byte_pos >= kCacheSize :
            self.GenerateBytes(self.cache, kCacheSize)
            self.next_byte_pos = 0
        return self.cache[self.next_byte_pos+1]

    def Rand64(self):
        output = 0
        # typedef unsigned long long --  uint64_t
        for i in range(64):
            # output |= static_cast<uint64_t>(Rand8()) << 8 * i
            output = output | self.Rand8() << 8 * i
        return output

    def RandBuffer(self,buffer,buffer_size):
        buffer_size = min(buffer_size, kCacheSize)
        self.GenerateBytes(buffer, buffer_size)
        return buffer_size





