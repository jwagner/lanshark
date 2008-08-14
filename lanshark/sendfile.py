#!/usr/bin/python
"""A Python wrapper arround the linux sendfile64() syscall
which falls back to a pure python implementation in case
sendfile 64 is not avaible"""
import sys
import select

def _sendfile(sock, fileobj):
    while True:
        buf = fileobj.read(16384)
        if not buf:
            break
        sock.sendall(buf)

if sys.platform == "linux2":
    import ctypes as c
    try:
        libc = c.cdll.LoadLibrary('libc.so.6')
        libc.__errno_location.restype = c.POINTER(c.c_int)
        def errnocheck(result, func, args):
            if result < 0:
                e = OSError()
                e.errno = libc.__errno_location().contents.value
                raise e
        sendfile64 = c.cdll.LoadLibrary('libc.so.6').sendfile64
        sendfile64.argtypes = [c.c_int, c.c_int, c.POINTER(c.c_longlong), c.c_longlong]
        sendfile64.errcheck = errnocheck
        sendfile64.restype = c.c_int
    except AttributeError, e:
        sendfile = _sendfile
    else:
        def sendfile(sock, fileobj):
            if not hasattr(fileobj, "fileno"):
                _sendfile(sock, fileobj)
                return
            offset = c.c_longlong(fileobj.tell())
            # seek backwards
            fileobj.seek(0, 2)
            size = fileobj.tell()
            sock.setblocking(1)
            sendfile64(sock.fileno(), fileobj.fileno(), c.byref(offset), c.c_longlong(size - offset.value))
else:
    sendfile = _sendfile

def test():
    import socket, tempfile
    import select
    if _sendfile == sendfile:
        to_test = (sendfile, )
    else:
        to_test = (sendfile, _sendfile)
    for implementation in to_test:
        if _sendfile == implementation:
            print "using python implementation"
        else:
            print "using native systemcall"
        f = tempfile.TemporaryFile()
        f.write("ttest")
        f.seek(1)
        ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssock.setblocking(0)
        ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ssock.bind(('127.0.0.1', 4632))
        ssock.listen(1)
        csock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        csock.setblocking(0)
        try:
            csock.connect(("127.0.0.1", 4632))
        except socket.error, e:
            if e[0] != 115:
                raise
        con = ssock.accept()[0]
        assert select.select([], [con], [], 10.0)
        implementation(con, f)
        assert select.select([csock], [], [], 10.0)
        text = csock.recv(4)
        print "recived", text
        assert text == "test"
        csock.close()
        ssock.close()
        print "done"

if __name__ == "__main__":
    test()
