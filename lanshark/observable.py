#!/usr/bin/env python
"""implements the observer pattern"""
from collections import defaultdict
class Observable(object):
    """An observable object"""
    def __init__(self):
        self.listeners = defaultdict(list)

    def connect(self, event, callback):
        """connect to an event"""
        self.listeners[event].append(callback)

    def disconnect(self, event, callback):
        """disconnect from an event"""
        self.listeners[event].remove(callback)

    def notify(self, event, *args):
        """notify all observers connected to a certain event"""
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
