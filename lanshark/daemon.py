#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""The Lanshark Daemon serves files, discovery, and search requests"""
import BaseHTTPServer
import cgi
import mimetypes
import os
import posixpath
import re
import shutil, socket, SocketServer, stat
import threading
import urllib, urllib2
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import simplejson

from lanshark.config import config

import logging
logger = logging.getLogger('lanshark')

from lanshark import icons
from lanshark import network
from lanshark import sendfile

from cache import cached
socket.getaddrinfo = cached(config.CACHE_TIMEOUT, stats=config.debug)(
        socket.getaddrinfo)


iconpath = os.path.join(config.DATA_PATH, "icons", "32x32")
iconfactory = icons.URLIconFactory(iconpath, "/__data__/icons/128x128/", ".png")
hidden_files = [re.compile(pattern) for pattern in config.HIDDEN_FILES]

def hidden(filename):
    return any(pattern.match(filename) for pattern in hidden_files)

class FileIndex(threading.Thread):
    """
    The fileindex offers fast searching over
    a periodicaly updated file index
    """
    def __init__(self, path):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.path = path
        if not self.path.endswith("/"):
            self.path += "/"
        self.file_index = {}
        # makes sure no search queries are answered before the index is ready
        self.index_event = threading.Event()
        self.wait_event = threading.Event()
        self.start()

    def run(self):
        """updates the fileindex periodically"""
        while True:
            logger.debug("updating file index")
            self.file_index = self.index(self.path, {})
            self.index_event.set()
            logger.debug("file index updated")
            self.wait_event.wait(config.INDEX_INTERVAL)
            self.wait_event.clear()

    def update(self):
        """Does a forced asynchronous reset of the file index"""
        self.index_event.clear()
        self.wait_event.set()

    def index(self, path, index = None, links = None):
        """updates the filed_index"""
        if not index:
            index = {}
        if not links:
            links = []
        for filename in os.listdir(path):
            if hidden(filename):
                continue
            try:
                filepath = os.path.join(path, filename)
                if os.path.isdir(filepath):
                    filepath += "/"
                    filename += "/"
                # we store the keys in unicode!
                try:
                    ufilename = filename.decode(config.FS_ENCODING)
                    ufilepath = filepath.decode(config.FS_ENCODING)
                except UnicodeDecodeError:
                    if config.debug:
                        logger.exception("error while indexing file %r",
                                filepath)
                    continue
                if ufilename in index:
                    index[ufilename].append(ufilepath)
                else:
                    index[ufilename] = [ufilepath]

                if filename[-1] == "/":
                    real_path = os.path.realpath(filepath)
                    if real_path != filepath:
                        if not real_path in links:
                            links.append(real_path)
                            self.index(filepath, index, links)
                    else:
                        self.index(filepath, index, links)
            except OSError:
                if config.debug:
                    logger.exception("Caught an OSError while indexing %s",
                            path)
        return index

    def search(self, exp):
        """Search for a file matching the regular expression exp"""
        self.index_event.wait()
        results = 0
        for name in self.file_index:
            if exp.match(name):
                for result in self.file_index[name]:
                    yield result
                    results += 1
                    if results >= config.MAX_SEARCH_RESULTS:
                        return

class UDPService(threading.Thread):
    """The UDPService handles search and discovery queries"""
    def __init__(self, fi):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.fileindex = fi
        self.socket = network.broadcast_dgram_socket(config.PORT)

    def run(self):
        while True:
            try:
                msg, addr = self.socket.recvfrom(1024)
            except:
                logger.exception("Couldn't receive data from the socket")
                continue
            try:
                self.process(msg, addr)
            except:
                logger.exception("UDPService exception: msg=%r addr=%r",
                    msg, addr)

    def process(self, msg, addr):
        if config.debug:
            logger.debug("UDPService: " + repr((addr, msg)))
        if addr[0] == config.BROADCAST_IP:
            logger.warn("got message from broadcast address")
        #    continue
        if msg == config.NETWORK_NAME:
            reply = msg + " " + config.HOSTNAME
            self.socket.sendto(reply, addr)
        elif msg.startswith("search %s " % config.NETWORK_NAME):
            uwhat = msg[8 + len(config.NETWORK_NAME):]
            try:
                what = uwhat.decode('utf8')
            except UnicodeError, e:
                what = uwhat
                logger.debug('UDPService: uwhat=%r e=%r', uwhat, e)
            try:
                search = re.compile(what, re.IGNORECASE)
                results = self.fileindex.search(search)
                for result in results:
                    result = result[len(self.fileindex.path):]
                    reply = uwhat + ":" + (result).encode("utf8")
                    self.socket.sendto(reply, addr)
            except re.error,e:
                    logger.exception("Recieved an invalid regex from %s", addr)

class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """The HTTPRequest handler serves the files/indexes, quite a mess"""
    protocol_version = "HTTP/1.1"
    server_version = "Lanshark"

    def __init__(self, request, client, server):
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self,
                request, client, server)
        self.docroot = server.docroot

    def do_GET(self):
        f = self.send_head()
        if f:
            # one minute
#            self.connection.settimeout(60)
#            shutil.copyfileobj(f, self.wfile)
            sendfile.sendfile(self.request, f)
            f.close()
        else:
            self.wfile.close()

    def send_head(self):
        self.path = self.path.split("?")[0]
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return self.list_directory(path)
        else:
            return self.send_file(path)

    def send_file(self, path):
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        fs = os.fstat(f.fileno())
        size = fs[6]
        # very very limited support for the range header
        # print self.headers["Range"]
        if "Range" in self.headers and self.headers["Range"].endswith("-"):
            try:
                crange = int(self.headers["Range"][6:-1])
                f.seek(crange)
                self.send_response(206)
                self.send_header("Content-Range",
                        "bytes %i-%i/%i" % (crange, size, size))
                size -= crange
            except ValueError:
                self.send_response(200)
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        # dont show this header until its __fully__ implemented
        #self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return f

    def guess_type(self, path):
        if path.endswith("/"):
            return "text/html"
        else:
            return mimetypes.guess_type(path)[0] or "application/ocet-stream"

    folder_images = [re.compile(exp, re.IGNORECASE)
            for exp in config.FOLDER_IMAGES]
    images = re.compile(".*\.(jpg|png|gif|svg)$")
    def get_folder_image(self, path, files):
        # so we can remove the big ones
        files = files[:]
        for folder_image in self.folder_images:
            for filename in files:
                if folder_image.match(filename):
                    filepath = os.path.join(path, filename)
                    if os.path.getsize(filepath) < config.MAX_IMAGE_SIZE:
                        return filename
                    else:
                        files.remove(filename)

    def list_directory(self, path):
        """create a directory listing"""
        self.send_response(200)
        try:
            files = []
            for filename in os.listdir(path):
                if hidden(filename):
                    continue
                filepath = os.path.join(path, filename)
                try:
                    stats = os.stat(filepath)
                    if stat.S_ISDIR(stats[stat.ST_MODE]):
                        filename += '/'
                        dirfiles = os.listdir(filepath)
                        def dir_only(name):
                            return os.path.isdir(os.path.join(filepath, name))
                        dirs = filter(dir_only, dirfiles)
                        size = (len(dirs), len(dirfiles)-len(dirs))
                        icon = self.get_folder_image(filepath, dirfiles)
                    else:
                        size = stats[stat.ST_SIZE]
                        icon = None
                    try:
                        filename = filename.decode(config.FS_ENCODING)
                        if icon:
                            icon = icon.decode(config.FS_ENCODING)
                        files.append((filename, size, icon))
                    except UnicodeError, e:
                        if config.debug:
                            logger.exception("Could not decode filename %r "
                                    "maybe %r is the wrong FS_ENCODING",
                                    filename, config.FS_ENCODING)
                except os.error, e:
                    logger.debug(e)
        except os.error, e:
            logger.exception("Exception while listing %s", path)
            self.send_error(404, "File not found")
            return None
        if "Accept" in self.headers and not "json" in self.headers["Accept"]:
            f = self.list_directory_html(files)
        else:
            f = self.list_directory_json(files)
        length = f.tell()
        self.send_header("Content-length", str(length))
        self.end_headers()
        f.seek(0)
        return f

    def list_directory_json(self, files):
        """Ouput directorylisting as json"""
        self.send_header("Content-type", "application/json")
        f = StringIO()
        simplejson.dump(files, f)
        return f

    def list_directory_html(self, files):
        """Ouput directorylisting as html"""
        # template engine anybody?
        files.sort()
        f = StringIO()
        self.send_header("Content-type", "application/xhtml+xml; charset=utf-8")
        if config.DISABLE_WEBINTERFACE:
            return f
        displaypath = cgi.escape(urllib2.unquote(self.path))
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\n'
                '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
                '<html xmlns="http://www.w3.org/1999/xhtml">'
                '<head>'
                '<title>Index of %s</title>' % displaypath)
        f.write('<link rel="stylesheet" type="text/css" '
                'href="/__data__/directoryindex.css" />'
                '<link rel="stylesheet" type="text/css" '
                'href="/__data__/thickbox.css" />'
                #'<script type="text/javascript" '
                #'src="/__data__/reflection.js"></script>'
                '<script type="text/javascript" '
                'src="/__data__/jquery.js"></script>'
                '<script type="text/javascript" '
                'src="/__data__/thickbox.js"></script>'
                '</head><body><h1>')
        paths = self.path.split("/")
        for i in xrange(self.path.count("/")):
            f.write('<a href="%s/">%s/</a>' % ("/".join(paths[:i+1]),
                cgi.escape(urllib2.unquote(paths[i]))))
        f.write('</h1><div id="container">'
                '<img src="/__data__/web/web_head.png" alt="" /><ul>')
        even = True
        for filename, size, icon in files:
            if filename.endswith("/"):
                ssize = "%i Directories, %i Files" % size
                if icon:
                    icon = (filename + icon).encode("utf-8")
                    icon = cgi.escape(urllib2.quote(icon), True)
                else:
                    icon = iconfactory.get_icon("folder")
            else:
                if size < config.MAX_IMAGE_SIZE and self.images.match(filename):
                    icon = filename.encode("utf-8")
                    icon = cgi.escape(urllib2.quote(icon), True)
                else:
                    icon = iconfactory.guess_icon(filename)
                ssize = "%i Bytes" % size
            href = urllib2.quote(filename.encode("utf8"))
            try:
                encfilename = cgi.escape(filename.encode("utf-8"))
            except UnicodeError:
                logger.debug("unable to convert filename %r to utf-8",
                        filename)
            else:
                f.write('<li><a')
                if any(filename.endswith(ext)
                    for ext in [".jpg", ".jpeg", ".gif"]):
                    f.write(' class="thickbox"')
                f.write(' href="%s" title="%s">'
                        '<img src="%s" alt="" width="96" height="96"'
                        ' class="reflect rheight25 icon" />%s</a></li>' %
                        (href, ssize, icon, encfilename))

        f.write('</ul>'#<a href="' + config.WEBSITE + '">'
                '<a href="http://lanshark.29a.ch/">'
                '<img src="/__data__/web/web_footer.png" '
                'alt="Lanshark Webinterface" class="clear reflect" /></a>')
        f.write("</div><div></div></body></html>")
        return f

    def translate_path(self, path):
        path = urllib2.unquote(path).decode('utf-8').encode(config.FS_ENCODING)
        path = posixpath.normpath(path)
        words = filter(None, path.split('/'))
        # todo: make generic
        if path.startswith("/__data__"):
            words.pop(0)
            path = config.DATA_PATH
        else:
            path = config.SHARE_PATH
        for word in words:
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        return path

    def log_message(self, format, *args):
        logger.info(format % args)

class HTTPService(threading.Thread, SocketServer.ThreadingMixIn,
        SocketServer.TCPServer):
    """Some wrapper arround SocketServer"""
    allow_reuse_address = True
    logRequests = config.debug
    protocol_version = "HTTP/1.1"
    daemon_threads = True
    def __init__(self, docroot):
        threading.Thread.__init__(self)
        SocketServer.TCPServer.__init__(self,
                ("", config.PORT), HTTPRequestHandler)
        self.setDaemon(True)
        self.docroot = docroot

    def handle_error(self, request, client):
        logger.exception("Exception occured while serving request "
                "for client %s", client)

    def run(self):
        self.serve_forever()

class Daemon:
    """The container for the lanshark http, udp and fileindex service"""
    def __init__(self):
        self.httpservice = HTTPService(config.SHARE_PATH)
        if not config.INVISIBLE:
            self.fileindex = FileIndex(config.SHARE_PATH)
            self.udpservice = UDPService(self.fileindex)
        config.connect("SHARE_PATH", self.share_path_changed)

    def share_path_changed(self):
        """update the paths of all the managed services"""
        if not config.SHARE_PATH.endswith("/"):
            config.SHARE_PATH += "/"
        else:
            if not config.INVISIBLE:
                self.fileindex.path = config.SHARE_PATH
                self.fileindex.update()
            self.httpservice.docroot = config.SHARE_PATH

    def start(self):
        """starts the services in the background"""
        if not config.INVISIBLE:
            self.udpservice.start()
        self.httpservice.start()

    def run(self):
        """starts the services in the foreground"""
        self.udpservice.start()
        self.httpservice.run()

if __name__ == "__main__":
    Daemon().run()
