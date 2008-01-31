#!/usr/bin/python
import random
import hmac
import sha

from lanshark.crypto import rijndael

BLOCK_SIZE = 16

def xor(a, b):
    return "".join(chr(ord(a[i]) ^ ord(b[i])) for i in xrange(len(a)))

class DecryptionException(Exception): pass

class Cipher:
    def __init__(self, key):
        self.key = sha.new(key).digest()[:BLOCK_SIZE]
        self.cipher = rijndael.rijndael(self.key)

    def encrypt(self, message):
        iv = "".join(chr(random.randint(0, 255)) for i in xrange(BLOCK_SIZE))
        # padding
        if len(message) % BLOCK_SIZE:
            message += (BLOCK_SIZE - len(message) % BLOCK_SIZE)  * "\0"
        # cbc encryption
        ciphertext = [iv]
        block = iv
        while message:
            block = xor(block, message[:BLOCK_SIZE])
            message = message[BLOCK_SIZE:]
            block = self.cipher.encrypt(block)
            ciphertext.append(block)
        ciphertext = "".join(ciphertext)
        mac = hmac.new(self.key, ciphertext, sha.new).digest()
        return mac + ciphertext

    def decrypt(self, ciphertext):
        mac = ciphertext[:20]
        ciphertext = ciphertext[20:]
        # check integrity using mac
        if not hmac.new(self.key, ciphertext, sha.new).digest() == mac:
            raise DecryptionException("Invalid mac")
        # iv
        lastblock = ciphertext[:BLOCK_SIZE]
        ciphertext = ciphertext[BLOCK_SIZE:]
        plaintext = []
        while ciphertext:
            block = ciphertext[:BLOCK_SIZE]
            ciphertext = ciphertext[BLOCK_SIZE:]
            plaintext.append(xor(lastblock, self.cipher.decrypt(block)))
            lastblock = block
        # remove padding
        plaintext[-1] = plaintext[-1].rstrip("\0")
        return "".join(plaintext)

def main():
    cipher = Cipher("test")
    assert cipher.decrypt(cipher.encrypt("foo")) == "foo"
    try:
        cipher.decrypt("\0"*48)
        assert False
    except DecryptionException:
        pass

if __name__ == "__main__":
    main()
