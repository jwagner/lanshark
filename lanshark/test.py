#!/usr/bin/python
# vim: set fileencoding=utf-8 :
import os
import unittest
import urllib
import tempfile, time
import random

from lanshark.config import config

config.SHARE_PATH = tempfile.mkdtemp()
# no collisions with real instances
config.PORT += random.randint(1, 100)
config.INCOMING_PATH = os.path.join(config.SHARE_PATH, "incoming")
config.MAX_SEARCH_RESULTS = 5
config.SEARCH_TIMEOUT = 0.5
config.DISCOVER_TIMEOUT = 0.5

from lanshark import lib
from lanshark import icons
from lanshark import configuration

def rm_r(path):
    if not os.path.isdir(path):
        os.unlink(path)
        return
    for file in [os.path.join(path, file) for file in os.listdir(path)]:
        rm_r(file)
    os.rmdir(path)

class LibTestCase(unittest.TestCase):
    huge_size = 1024*100
    def setUp(self):
        self.url = u"http://localhost:" + str(config.PORT) + "/"
        os.mkdir(config.INCOMING_PATH)
        foo = os.path.join(config.SHARE_PATH, "Foo")
        os.mkdir(foo)
        bar = os.path.join(foo, "bar")
        os.mkdir(bar)
        for name in [".invisible", u"fooö", "Foo/oOo","Foo/cover.jpg",
                "Foo/bar/spam"]:
            name = name.replace("/", os.path.sep).encode(config.FS_ENCODING)
            fname = os.path.join(config.SHARE_PATH, name)
            f = open(fname, "w")
            f.write("test")
            f.close()
        for name in ["huge", "Foo/bar/huge"]:
            name.replace("/", os.path.sep)
            fname = os.path.join(config.SHARE_PATH, name)
            f = open(fname, "w")
            data = "ABCDEFGH"*128
            for i in xrange(self.huge_size/len(data)):
                f.write(data)
            f.close()
        lib.reset_cache()

    def test_discover(self):
        discovered = list(lib.discover())
        self.assert_(discovered)
        self.assert_(config.HOSTNAME in  [host[0] for host in discovered])

    def test_stat(self):
        lib.stat(self.url)
        size, icon = lib.stat(self.url + ".invisible")
        self.assertEquals(size, -1) # size is not provided for invisible files
        size, icon = lib.stat(self.url + "Foo/")
        self.assert_(icon)
        self.assertEquals(size, [1, 2])
        size, icon = lib.stat(self.url + "huge")
        self.assertEquals(size, self.huge_size)

    def test_guessip(self):
        lib.guess_ip()

    def test_search(self):
        daemon.fileindex.update()
        self.assertEquals(len(list(lib.search(u"fooö"))), 1)
        self.assertEquals(len(list(lib.search("\\.invisible"))), 0)
        self.assertEquals(len(list(lib.search("huge"))), 2)
        foo = sorted(lib.search("foo"))
        self.assertEquals(len(foo), 2)
        self.assert_(foo[0].endswith("/"))
        self.assertEquals(sorted(lib.search('')), sorted(lib.search('')))
        self.assertEquals(len(list(lib.search(""))), config.MAX_SEARCH_RESULTS)

    def test_search_async(self):
        daemon.fileindex.update()
        start = time.time()
        for result in lib.search("\\.invisible", True):
            self.assertEquals(result, None)
            time.sleep(0.1)
        self.assert_(time.time()-start >= config.SEARCH_TIMEOUT)

        results = []
        for result in lib.search("", True):
            if result:
                self.assert_(result.startswith("http://"))
                results.append(result)
            else:
                time.sleep(config.MAX_SEARCH_RESULTS)
        self.assertEquals(len(results), config.MAX_SEARCH_RESULTS)
        self.assertEquals(sorted(filter(None, lib.search("foo", True))),
                              sorted(lib.search("foo")))

    def test_get_url(self):
        url = (self.url + u"fooö").encode("utf8")
        print repr(url)
        self.assertEquals(lib.get_url(url), "test")

    def test_download(self):
        path = "Foo/bar/huge"
        download = lib.download(self.url + path)
        name, bytes = download.next()
        self.assertEquals(name,
                os.path.join(config.INCOMING_PATH,
                    path.replace("/", os.path.sep)))
        self.assertEquals(bytes, self.huge_size)
        self.assertEquals(sum(download), bytes)
        self.assert_(os.path.exists(name))

    def test_resume(self):
        path = "Foo/bar/huge"
        download = lib.download(self.url + path)
        name, bytes = download.next()
        n = download.next()
        del download
        download = lib.download(self.url + path)
        name, bytes = download.next()
        self.assertEquals(n, download.next())
        self.assertEquals(sum(download) + n, bytes)
        shared = os.path.join(config.SHARE_PATH, path.replace("/", os.path.sep))
        shared_data = open(shared).read()
        downloaded_data = open(name).read()
        self.assertEquals(len(downloaded_data), len(shared_data))
        self.assertEquals(downloaded_data, shared_data)

    def test_download_404(self):
        try:
            lib.download(self.url + "does_not_exists").next()
            self.assert_(False)
        except lib.DownloadException:
            pass

    def test_ls(self):
        expected = sorted([self.url + ex for ex in ("Foo/",
                 urllib.quote(u"fooö".encode("utf-8")),
                 "huge",
                 "incoming/")])
        self.assertEqual(sorted(lib.ls(self.url)), expected)
        foobarpath = os.path.join(config.SHARE_PATH, "foobar")
        open(foobarpath, "w").close()
        self.assertEqual(sorted(lib.ls(self.url)), expected)
        lib.reset_cache()
        self.assertEqual(sorted(lib.ls(self.url)), sorted(expected + [self.url + "foobar"]))
        os.remove(foobarpath)

    def test_ls_l(self):
        expected = sorted([(self.url + ex, size, icon) for ex, size, icon in
                (("Foo/", [1, 2], self.url + u"Foo/cover.jpg"),
                 (urllib.quote(u"fooö".encode("utf-8")), len("test"), None),
                 ("huge", self.huge_size, None),
                 ("incoming/", [0, 0], None))])
        self.assertEqual(sorted(lib.ls_l(self.url)), expected)

    def test_statichosts(self):
        hosts = ["127.0.0.1:31337", "example.com:31337"]
        map(config.STATICHOSTS.append, hosts)
        discovered = list(lib.discover())
        for host in hosts:
            self.assert_((host, host) in discovered)

    def tearDown(self):
        for file in os.listdir(config.SHARE_PATH):
            rm_r(os.path.join(config.SHARE_PATH, file))

    def testCache(self):
        import cache
        cache.run_test()

    def runTest(self):
        pass

class ByteFormatTestCase(unittest.TestCase):
    def test_byteformat(self):
        assertions = ((0, '0.00 B'), (999, '999.00 B'),
                (1024, '1.00 KiB'), (1025, '1.00 KiB'),
                (1024**2, '1.00 MiB'), (1024**3, '1.00 GiB'),
                (1024**4, '1.00 TiB'), (1024**5, '1024.00 TiB'))
        for n, assertion in assertions:
            self.assertEquals(lib.byteformat(n,
                ('B', 'KiB', 'MiB', 'GiB', 'TiB')), assertion)

class IconsTestCase(unittest.TestCase):
    def setUp(self):
        iconpath = os.path.join(os.path.join(config.DATA_PATH, "icons"),
                "32x32")
        self.iconurl = "http://localhost/__data__/icons/32x32/"
        self.factory = icons.URLIconFactory(iconpath, self.iconurl, ".png")

    def test_guess(self):
        self.assertEqual(self.factory.guess_icon("foo/"),
            self.iconurl + "folder.png")
        self.assertEqual(self.factory.guess_icon("foo.ogg"),
            self.iconurl + "audio-x-generic.png")
        self.assertEqual(self.factory.guess_icon("foo.jpg"),
            self.iconurl + "image-x-generic.png")
        self.assertEqual(self.factory.guess_icon("foo.png"),
            self.iconurl + "image-x-generic.png")
        self.assertEqual(
            self.factory.guess_icon(self.iconurl + "foo.png"),
            self.iconurl + "image-x-generic.png")
        self.assertEqual(self.factory.guess_icon(""),
                self.iconurl + "text-x-generic-template.png")

    def test_get(self):
        self.assertEqual(self.factory.get_icon("image-x-generic"),
                self.iconurl + "image-x-generic.png")
        self.assertEqual(self.factory.get_icon("doesntexists"), None)

class ConfigurationTestCase(unittest.TestCase):
    def run_test(self):
        configuration.test()

class AutostartTestCase(unittest.TestCase):
    def run_test(self):
        from lanshark import autostart
        autostart.test()

class SendfileTestCase(unittest.TestCase):
    def run_test(self):
        from lanshark import sendfile
        sendfile.test()

if __name__ == "__main__":
    from daemon import Daemon
    try:
        daemon = Daemon()
        daemon.start()
        unittest.main()
    finally:
        os.rmdir(config.SHARE_PATH)
