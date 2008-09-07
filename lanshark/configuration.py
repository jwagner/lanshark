#!/usr/bin/python
"""A hopefuly reusable configuration library

Example:

class MyConfig(Config):
    n = Integer(10, "Some doc")
    foobar = String("bar", "Some more doc")
    trve = IsTrve(True, "Even more doc")

config = MyConfig()
config.load("foo.conf")
config.n = 0x29a
config.save()

"""
from __future__ import with_statement
import os

import simplejson

from lanshark import observable

class Error(Exception):
    """Raised when an error occures while parsing the confiuration file"""
    def __init__(self, lineno, line, cause):
        self.line = line
        self.lineno = lineno
        self.__cause__ = cause
        self.message = "Error while parsing configuration on line %i: '%s'\n"\
                       "%s" % (lineno, line, str(cause))
    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message

# TODO:  Add some kind of onchange events
class Config(observable.Observable):
    """Config - represents a configuration file"""
    def __init__(self):
        observable.Observable.__init__(self)
        for name in dir(self.__class__):
            attr = getattr(self.__class__, name)
            if isinstance(attr, Key):
                setattr(self, name, attr.default)

    def __setattr__(self, attr, value):
        if attr not in self.__dict__ or self.__dict__[attr] != value:
            self.__dict__[attr] = value
            if hasattr(self.__class__, attr)\
                    and isinstance(getattr(self.__class__, attr), Key):
                self.notify("changed", attr)
                self.notify(attr)

    def load(self, f):
        """load configuration from path might raise (IO)Error"""
        if isinstance(f, basestring):
            with open(f, "r") as f:
                self._load(f)
        else:
            self._load(f)

    def _load(self, f):
        for lineno, line in enumerate(f):
            if line[0] == "#": continue
            try:
                if line.strip():
                    name, value = map(str.strip, line.split("=", 1))
                    if hasattr(self.__class__, name):
                        key = getattr(self.__class__, name)
                        if isinstance(key, Key):
                            setattr(self, name, key.parse(value))
            except Exception, e:
                raise Error(lineno, line, e)

    def save(self, f):
        """save configuration to file"""
        if isinstance(f, basestring):
            with open(f, "w") as f:
                self._save(f)
        else:
            self._save(f)

    def _save(self, f):
        for name in dir(self.__class__):
            attr = getattr(self.__class__, name)
            if isinstance(attr, Key):
                doc = "# " + attr.__doc__.replace(os.linesep,
                        os.linesep + "# ")
                f.write(doc + os.linesep)
                value = attr.dump(getattr(self, name))
                if attr.comment_out_default and value == attr.default:
                    fmt = '# %s = %s%s'
                else:
                    fmt = '%s = %s%s'
                f.write(fmt % (name, value, os.linesep*2))
                f.flush()
class Key:
    """Key - base class for configuration keys"""
    keytype = str
    # comment out the value as long it equals the default
    comment_out_default = True
    def __init__(self, default, doc):
        self.keytype.__init__(self)
        self.__doc__ = doc
        self.default = default

    def parse(self, value):
        "load value from string"
        return self.keytype(value)

    def dump(self, value):
        "dump value to its string from"
        return str(value)

    def __repr__(self):
        return "<Key type=%s default=%s>" % (repr(self.keytype), 
                repr(self.default))

class String(Key):
    """Represents a str"""
    keytype = str

class Integer(Key):
    """Represents a int"""
    keytype = int

class Float(float):
    """Represents a float"""

class Boolean(Key):
    """Represents a bool"""
    keytype = bool
    def parse(self, value):
        return (value.lower() != "false")

class Enum(String):
    """Represents an enum"""
    def __init__(self, default, values, doc):
        """Creates new instance. `values` is a tuple of all valid enum
        values"""
        String.__init__(self, default, doc)
        self.values = values

    def parse(self, value):
        retval = String.parse(self, value)
        if retval not in self.values:
            raise ValueError('Invalid enum value %s' % retval)
        return retval

class List:
    """List mixin"""
    def parse(self, value):
        def parse(value):
            return self.keytype(value.replace("\\,", ","))
        return map(parse, value.split(", "))

    def dump(self, value):
        def dump(value):
            return str(value).replace(",","\\,")
        return ", ".join(map(dump, value))

class StringList(List, String):
    "list of strings"
    pass

class JSON(Key):
    def parse(self, value):
        return simplejson.loads(value)

    def dump(self, value):
        return simplejson.dumps(value)

def test():
    from StringIO import StringIO
    class TestConfig(Config):
        s = String("default", "doc of s")
        i = Integer(0x29a, "doc of i")
        b = Boolean(False, "doc of b")
        j = JSON({"something": ["more", "complex\\"]}, "doc of j")
        j2 = JSON({"something": ["more", "complex"]}, "doc of j")
    config = TestConfig()
    assert TestConfig.s.__doc__ == "doc of s"
    assert config.s == "default"
    assert config.j["something"][1] == "complex\\"
    config.j["something"] = "different\\"
    assert config.j["something"] == "different\\"
    assert not config.b
    config.s = "not"
    config.s += " default"
    config.i = 0
    config.b = True
    f = StringIO()
    config.save(f)
    val = f.getvalue()
    assert "doc of s" in val
    assert "doc of j" in val
    assert "not default" in val
    config = TestConfig()
    assert config.s == "default"
    f.seek(0)
    config.load(f)
    assert config.j2["something"][1] == "complex"
    assert config.j["something"] == "different\\"
    assert config.s == "not default"
    assert config.i == 0
    assert config.b is True
    observable.test()
    print "test complete"

if __name__ == "__main__":
    test()
