#!/usr/bin/env python
from collections import defaultdict
class Observable(object):
    def __init__(self):
        self.listeners = defaultdict(list)

    def connect(self, event, callback):
        self.listeners[event].append(callback)

    def disconnect(self, event, callback):
        self.listeners[event].remove(callback)

    def notify(self, event, *args):
        for callback in self.listeners[event]:
            callback(*args)

def test():
    test.foo = 0
    observable = Observable()
    def callback(bar):
        test.foo = bar
    observable.connect("foo", callback)
    observable.notify("foo", 0x29a)
    assert test.foo == 0x29a
    observable.disconnect("foo", callback)
    observable.notify("foo", 0)
    assert test.foo == 0x29a

if __name__ == "__main__":
    test()
