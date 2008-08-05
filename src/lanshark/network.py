import socket

def broadcast_dgram_socket(port):
    """A nonblocking broadcasting udp socket"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setblocking(0)
    sock.settimeout(None)
    sock.bind(("", port))
    return sock
