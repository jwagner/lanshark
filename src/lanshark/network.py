import socket

from lanshark.crypto.helper import Cipher

class NullCipher:
    def encrypt(self, message):
        return message

    def decrypt(self, message):
        return message

class SecureUDPSocket:
    """An encrypted nonblocking broadcasting udp socket"""
    def __init__(self, port, key):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setblocking(0)
        self.sock.settimeout(None)
        self.sock.bind(("", port))
        self.set_key(key)

    def set_key(self, key):
        if key:
            self.cipher = Cipher(key)
        else:
            self.cipher = NullCipher()

    def __getattr__(self, name):
        return getattr(self.sock, name)

    def sendto(self, msg, host):
        self.sock.sendto(self.cipher.encrypt(msg), host)

    def recvfrom(self, size):
        data, host = self.sock.recvfrom(size)
        return (self.cipher.decrypt(data), host)
