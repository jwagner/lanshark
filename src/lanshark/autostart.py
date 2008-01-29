#!/usr/bin/env python
"""A simple crossplatform autostart helper"""
from __future__ import with_statement

import os
import sys

if sys.platform == 'win32':
    import _winreg
    _registry = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
    def get_runkey():
        return _winreg.OpenKey(_registry,
                r"Software\Microsoft\Windows\CurrentVersion\Run", 0, 
		_winreg.KEY_ALL_ACCESS)

    def add(name, application):
        """add a new autostart entry"""
        key = get_runkey()
        _winreg.SetValueEx(key, name, 0, _winreg.REG_SZ, application)
        _winreg.CloseKey(key)

    def exists(name):
        """check if a autostart entry exists"""
        key = get_runkey()
        exists = True
        try:
            _winreg.QueryValueEx(key, name)
        except WindowsError:
            exists = False
        _winreg.CloseKey(key)
        return exists

    def remove(name):
        """delete a autostart entry"""
        key = get_runkey()
        _winreg.DeleteValue(key, name)
        _winreg.CloseKey(key)
else:
    _xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "~/.config")
    _xdg_user_autostart = os.path.join(os.path.expanduser(_xdg_config_home),
            "autostart")

    def getfilename(name):
        """get the filename of a autostart (.desktop) file"""
        return os.path.join(_xdg_user_autostart, name + ".desktop")

    def add(name, application):
        """add a new autostart entry"""
        desktop_entry = "[Desktop Entry]\n"\
            "Name=%s\n"\
            "Exec=%s\n"\
            "Type=Application\n"\
            "Terminal=false\n" % (name, application)
        with open(getfilename(name), "w") as f:
            f.write(desktop_entry)

    def exists(name):
        """check if a autostart entry exists"""
        return os.path.exists(getfilename(name))

    def remove(name):
        """delete a autostart entry"""
        os.unlink(getfilename(name))

def test():
    try:
        add("test_xxx", "test")
        assert exists("test_xxx")
    finally:
        remove("test_xxx")

if __name__ == "__main__":
    test()
