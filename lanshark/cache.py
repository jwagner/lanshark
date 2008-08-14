#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Generic cache decorator with some special features
...and limitations ;)"""
import time

DEBUG = True

class _Cached:
    """do not use this class directly use cached() instead"""
    def __init__(self, func, timeout=600, max_items=128, stats=False):
        self.func = func
        self.timeout = timeout
        self.max = max_items
        self.results = {}
        self.heap = []
        self.stats = stats
        if stats:
            self.hits = 0
            self.misses = 0

    def __call__(self, *args, **kwargs):
        if "reset_cache" in kwargs:
            self.results = {}
            self.heap = []
            return
        hash_ = hash(args)
        t = time.time()
        while self.heap and self.heap[0][0] < t:
            del self.results[self.heap.pop(0)[1]]
        if hash_ in self.results:
            if self.stats: self.hits += 1
            return self.results[hash_]
        if self.stats: self.misses += 1
        result = self.func(*args, **kwargs)
        self.results[hash_] = result
        self.heap.append((t + self.timeout, hash_))
        if len(self.heap) > self.max:
            del self.results[self.heap.pop(0)[1]]
        return result

def cached(timeout=600, max_items=128, stats=False):
    """cache decorator with variable timeout and maximal items"""
    return lambda func: _Cached(func, timeout, max_items, stats)

i = 0
@cached(0.4, 3)
def test(x):
    global i
    i += x
    return x

def run_test():
    """test the cache module using assertions"""
    def t(n):
        assert test(n) == n
    t(1)
    assert i == 1
    t(1)
    assert i == 1
    t(2)
    time.sleep(0.1)
    assert i == 3
    time.sleep(0.1)
    t(3)
    assert i == 6
    time.sleep(0.1)
    t(4)
    assert i == 10
    t(2)
    assert i == 10
    t(4)
    assert i == 10
    t(1)
    assert i == 11
    time.sleep(0.1)
    t(2)
    assert i == 13
    t(2)
    assert i == 13
    test(reset_cache = True)
    t(2)
    assert i == 15
    t(2)
    assert i == 15
    time.sleep(0.5)
    t(2)
    assert i == 17

if __name__ == "__main__":
    print "running test"
    run_test()
    print "done"
