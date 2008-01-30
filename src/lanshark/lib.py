#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""The lanshark lib encapsulates the client logic"""
from __future__ import division
from __future__ import with_statement
__version__ = "0.0.2"
copyright = \
"""Lanshark %s - A P2P filesharing tool for local area networks
Copyright (C) 2007 Jonas Wagner

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
""" % __version__

import gc
import logging
import math
import os
import re
import select, socket, subprocess, sys
import time
import urllib2

import simplejson

from config import config
from cache import cached

logger = logging.getLogger('lanshark')

socket.getaddrinfo = cached(config.CACHE_TIMEOUT, stats=config.debug)(
        socket.getaddrinfo)

@cached()
def guess_ip():
    """guess the public ip of the system"""
    if "win" in sys.platform:
        return socket.gethostbyname(socket.gethostname())
    else:
        process = "/sbin/ifconfig"
        pattern = re.compile(r"inet\ addr\:((\d+\.){3}\d+)", re.MULTILINE)
        try:
            proc = subprocess.Popen(process, stdout=subprocess.PIPE)
            proc.wait()
            data = proc.stdout.read()
        except OSError, e:
            logger.info(e)
            return "127.0.0.1"
        try:
            return pattern.findall(data)[0][0]
        except IndexError:
            return "127.0.0.1"


def get_socket():
    """get a new unblocking bound udp broadcast socket"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setblocking(0)
    sock.bind(("", config.PORT + 1))
    return sock

def recv(sock, timeout, async):
    """Receive data from sock using a generator
    timeout specifies the time recv will run
    If async is set it will instantly return None instead of blocking
    """
    start = time.time()
    while time.time() - start < timeout:
        while True:
            if async:
                maxwait = 0.001
            else:
                maxwait = timeout - time.time() + start
            rwxlist = select.select((sock, ), (), (), maxwait)
            if rwxlist[0]:
                try:
                    data, addr = sock.recvfrom(1024)
                    logger.debug("recv %r %r", addr, data)
                except socket.error, e: # handle udp instability
                    logger.debug("socket.error in recv(): %r", e)
                else:
                    yield (data, addr)
                continue
            if async:
                yield None
            break

def resolve(addr):
    """resolve host if enabled in config"""
    if config.RESOLVE_HOSTS:
        try:
            return socket.gethostbyaddr(addr)[0]
        except socket.herror, e:
            logger.debug(e)
    return addr

def discover(async=False):
    """Discover other hosts in the network"""
    for item in config.STATICHOSTS:
        yield (item, item)
    s = get_socket()
    hello = config.NETWORK_NAME
    s.sendto(hello, (config.BROADCAST_IP, config.PORT))
    for data in recv(s, config.DISCOVER_TIMEOUT, async):
        if data:
            msg, (addr, port) = data
            if config.STATICHOSTS and\
                    "%s:%i" % (addr, port) in config.STATICHOSTS:
                continue
            if msg.startswith(hello):
                name = msg[len(hello)+1:]
                url = "http://%s:%i/" % (resolve(addr), port)
                yield (name, url)
            else:
                yield None
        else:
            yield None

def search(what, async=False):
    """Search for files"""
    sock = get_socket()
    what = what.encode('utf8')
    sock.sendto("search %s %s" % (config.NETWORK_NAME, what),
            (config.BROADCAST_IP, config.PORT))
    results = 0
    for data in recv(sock, config.SEARCH_TIMEOUT, async):
        if data:
            msg, (addr, port) = data
            if msg.startswith(what + ":"):
                result = msg[len(what)+1:]
                msg = urllib2.quote(result)
                yield "http://%s:%i/%s" % (resolve(addr), port, msg)
                results += 1
                if results == config.MAX_SEARCH_RESULTS:
                    return
        else:
            yield None

def ls(url):
    """list url contents"""
    if not url.endswith("/"):
        url += "/"
    # converting f from unicode to string because urllib.quote has problems
    # with certain unicode characters
    return map(lambda x: url + urllib2.quote(x[0].encode('utf-8')),
            get_json(url))

def ls_l(url):
    """list url contents returns a list of (url, size, icon) tuples"""
    if not url.endswith("/"):
        url += "/"
    # converting f from unicode to string because urllib.quote has problems
    # with certain unicode characters
    files = []
    for file, size, icon in get_json(url):
        fileurl = url + urllib2.quote(file.encode('utf-8'))
        if icon:
            icon = fileurl + icon
        elif size < config.MAX_IMAGE_SIZE and "." in file and\
            file[file.rindex(".")+1:].lower() in ("jpg", "png", "jpeg", "gif"):
            icon = fileurl
        files.append((fileurl, size, icon))
    return files

def stat(url):
    """list url status returns (size, icon)"""
    # unknown for root url
    if url[:-1].count("/") < 3:
        return (-1, None)
    for itemurl, size, icon in ls_l(url[:url.rindex("/", 0, -1)]):
            if itemurl == url:
                return (size, icon)
    # Probably a hidden file
    return (-1, None)


def ls_r(url):
    """list url contents recursive"""
    if not url.endswith("/"):
        return url
    results = []
    urls = ls(url)
    for url in urls:
        if url.endswith("/"):
            try:
                results += ls_r(url)
            except urllib2.HTTPError, e:
                logger.debug(e)
        else:
            results.append(url)
    return results

def reset_cache():
    """reset all caches"""
    get_url(reset_cache=True)
    get_json(reset_cache=True)
    socket.getaddrinfo(reset_cache=True)
    gc.collect()

@cached(config.CACHE_TIMEOUT, 64, stats=config.debug)
def get_url(url):
    """return contents of url."""
    return urllib2.urlopen(url).read()

@cached(config.CACHE_TIMEOUT, 2048, stats=config.debug)
def get_json(url):
    """return parsed json located at url"""
    req = urllib2.Request(url, None, {"Acccept": "application/json"})
    return simplejson.load(urllib2.urlopen(req))

class DownloadException(Exception):
    """Exceptions that happened while downloading"""
    def __init__(self, message, cause=None):
        Exception.__init__(self)
        self.message = message
        self.__cause__ = cause

    def __repr__(self):
        return Exception.__repr__(self) + repr(self.__cause__)

class DownloadExistsException(DownloadException):
    def __init__(self, message, file):
        DownloadException.__init__(self, message)
        self.file = file

def download(url, relpath=None, incoming=config.INCOMING_PATH):
    """Download url into folder preserving the path in the url"""
    if relpath:
        path = urllib2.unquote(url[len(relpath):])
    else:
        path = urllib2.unquote(urllib2.urlparse.urlparse(url)[2][1:])
    try:
        path = path.decode('utf8').encode(config.FS_ENCODING)
    except UnicodeError:
        pass
    parts = path.split("/")
    # sanity checks
    if os.path.pardir in parts:
        raise DownloadException("Someone tired to h4x0r you?!")
    localpath = os.path.abspath(os.path.join(incoming, os.path.sep.join(parts)))
    if os.path.exists(localpath):
        raise DownloadExistsException("%s already exists" % localpath,
                file=localpath)
    # resuming
    downloadpath = localpath + ".part"
    if os.path.exists(downloadpath):
        resume = True
    else:
        resume = False
    # create directories
    current = incoming
    for part in parts[:-1]:
        current = os.path.join(current, part)
        if not os.path.exists(current):
            os.mkdir(current)
        elif not os.path.isdir(current):
            raise DownloadException("%s is not a directory" % current)
    return do_download(url, downloadpath, localpath, resume)

def do_download(url, downloadpath, localpath, resume):
    """do_download does the dirty work"""
    # download it
    try:
        req = urllib2.Request(url)
        if resume:
            f = open(downloadpath, "ab")
            # windows is so incredibly dumb that I have to seek to the end
            # of the file manually!!!!
            f.seek(os.path.getsize(downloadpath))
            req.add_header("Range", "bytes=%i-" % f.tell())
        else:
            f = open(downloadpath, "wb")
        with f:
            u = urllib2.urlopen(req)
            # the first yield is (localpath, filesize)
            yield (localpath, int(u.headers.get("Content-Length")) + f.tell())
            # the second yield is amount already downloaded
            yield f.tell()
            # retry 3 times
            for i in range(3):
                try:
                    data = u.read(config.DOWNLOAD_BS)
                    while data:
                        f.write(data)
                        yield len(data)
                        data = u.read(config.DOWNLOAD_BS)
                    break
                except socket.error:
                    # retry every 10 seconds
                    print "retrying"
                    time.sleep(10)
                    req = urllib2.Request(url)
                    req.add_header("Range", "bytes=%i-" % f.tell())
                    u = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        logger.exception("Error while downloading %r", url)
        raise DownloadException(e.message, e)
    except socket.error, e:
        logger.exception("Error while downloading %r", url)
        raise DownloadException(e.message, e)
    except os.error, e:
        logger.exception("Error while downloading %r", url)
        raise DownloadException(e.message, e)
    os.rename(downloadpath, localpath)

def byteformat(n, units=('B', 'KiB', 'MiB', 'GiB', 'TiB')):
    """Format a number of bytes"""
    i = n and int(math.log(n, 1024)) or 0
    if i >= len(units):
        i = len(units)-1
    n /= 1024.0**i
    return "%.2f %s" % (n, units[i])

