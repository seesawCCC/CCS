# -*- coding: utf-8 -*-
# @Time : 2022/7/19 10:03
# @Author : LRX
# @Site : 
# @File : add_maps_bench.py
# @Software: PyCharm

from .secagg_vector import SecAggVector

# 此处用到了C++的性能测试工具--benchmark, 后续需要继续查找Python中的同类工具进行改写
def CustomArguments(b):
    bit_widths = {8, 25, 38, 53, len(SecAggVector.kMaxModulus - 1)}
    for bit_width in bit_widths:
        # for (int size = 32; size <= 32 * 1024 * 1024; size *= 32)
        #size *= 32---size = size*32
        for size in range(32,32 * 1024 * 1024+1):
            b.ArgPair(bit_width, size)
            size = size*32
    return None


def MakeMap(bit_width,size, start, step):
    vec = {}
    vec.resize(size)

    # 1ULL--后缀ULL为整数表示类型说明符,它的意思是nsigned long long
    # modulus = 1ULL << bit_width; "<<"左移操作符
    modulus = 1 << bit_width
    v = start
    for i in range(size):
        vec[i] = v
        v = (v + step) % modulus
    map = SecAggVectorMap()
    map.emplace("test", SecAggVector(vec, modulus))
    return map

def BM_AddMaps(state):
    map_a = MakeMap(state.range(0), state.range(1), 1, 1)
    map_b = MakeMap(state.range(0), state.range(1), 2, 3)
    for i in state:
        map_sum = AddMaps(*map_a, *map_b)
        benchmark.DoNotOptimize(map_sum)
    return None

BENCHMARK(BM_AddMaps).Apply(CustomArguments)





