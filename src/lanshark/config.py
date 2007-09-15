"""The lanshark config module loads and saves config files"""
import os, sys

import configuration
import socket
from configuration import Boolean, Integer, String, StringList

def in_pathlist(file, pathlist = os.environ.get("PATH").split(os.pathsep)):
    for path in pathlist:
        if os.path.exists(os.path.join(path, file)):
            return True

def select_app(*apps):
    for app in apps:
        if in_pathlist(app):
            return app
    return ""

def get_mediaplayer():
    if sys.platform.startswith("win"):
        import _winreg
        def get_registry_value (subkey, name):
            value = None
            for hkey in _winreg.HKEY_LOCAL_MACHINE, _winreg.HKEY_CURRENT_USER:
                try:
                    reg = _winreg.OpenKey(hkey, subkey)
                    value = _winreg.QueryValue(reg, name)
                    _winreg.CloseKey(reg)
                except _winreg.error:
                    pass
            return value
        player = '"%s"' % get_registry_value('Software\\VideoLAN','VLC') or ''
    else:
        player = select_app("gmplayer", "gxine", "totem", "kaffeine", "vlc",
                "mplayer", "xine")
    if player:
        player = player + " %s"
    return player

def get_imageviewer():
    return sys.platform.startswith("win") and "browser" or select_app(
            "kuickshow", "display") + " %s" or "browser"

def get_sys_encoding():
    try:
        return sys.stdout.encoding
    except AttributeError:
        # frozen or so
        return 'cp1252'

class Config(configuration.Config):
    DEBUG = Boolean(False, "Show debugging information")
    VERBOSE = Boolean(False, "Be more verbose")
    BROADCAST_IP = String("255.255.255.255",
            "IP to use for udp broadcasts")
    PORT = Integer(31337, "Port to use for both UDP and TCP")
    SEARCH_TIMEOUT = Integer(5,
            "Time to wait for search results in seconds")
    DISCOVER_TIMEOUT = Integer(5,
            "Time to wait for new hosts to answer in seconds")
    DISCOVER_INTERVAL = Integer(60,
            "Interval to search for new computers in seconds")
    HELLO = String("HELO",
            "Word to use for discovery, might act as simple password")
    CACHE_TIMEOUT = Integer(600, "HTTP cache time to live")
    SHARE_PATH = String("", "Path to the files you want to share")
    INCOMING_PATH = String("", "Path to store the downloaded files")
    MAX_SEARCH_RESULTS = String(128,
            "Maximal number of search results per peer")
    FOLDER_IMAGES = StringList([r"\.?folder\.(png|jpg|gif|img)$",
                         r"cover\.(png|jpg|gif)$",
                         r"cover\-front\.(png|jpg|gif)$",
                         r"cover.*?\.(png|jpg|gif)$",
                         r"albumart.*?large\.jpg$",
                         r"albumart.*?\.jpg"],
            "regexps to match the folder images/covers")
    MAX_IMAGE_SIZE = Integer(250000,
            "Maximal size of preview images/covers to use")
    DAEMON_IN_GUI = Boolean(True,
            "Integrates daemon in the gui process")
    RESOLVE_HOSTS = Boolean(False, "Resolve hostnames")
    INDEX_INTERVAL = Integer(3600,
            "Interval to update the fileindex in seconds")
    GUI_ICON_SIZE = Integer(48, "Icon size in the gtkui")
    # thats a little hacky but works well ;)
    PID_FILE = String(os.path.join("$configdir", "lanshark.pid"),
            "Location of the pid file")
    SOCKET_TIMEOUT = Integer(5000, "The timeout of tcp sockets in ms")
    VIDEO_PLAYER = String(get_mediaplayer(),
            "Command to play video files %s gets replaced with "
            "the url to the video")
    AUDIO_PLAYER = String(get_mediaplayer(),
            "Command to play audio files %s gets replaced with"
            "the url to the audio file ")
    IMAGE_VIEWER = String(get_imageviewer(),
            "Command to view images files %s gets replaced with"
            "the url to the image ")
    DISABLE_WEBINTERFACE = Boolean(False, "Do not show html interface")
    FS_ENCODING = String(sys.getfilesystemencoding(), "Filesystem encoding")
    SYS_ENCODING = String(get_sys_encoding(), 'System Encoding')
    HOSTNAME = String(socket.gethostname(), "The name of your host/share")
    DOWNLOAD_RELPATH = Boolean(True, "Use relative paths for downloads"
            "instead of absolute ones")
    INVISIBLE = Boolean(False, "Do not answer to discovery or search requests")
    STATUSICON = Boolean(True, "Show icon in statusbar")
    STATICHOSTS = StringList([], "Static peer entries for networks where udp"
            "broadcasts are not avaible. Exmaple: example.com:31337, 192.168.1.2:31337")
    HIDDEN_FILES = StringList([r"\..*", r"Thumbs\.db"],
            "Regexps to match hidden files")
    PSYCO = Boolean(False, "Enable psyco JIT")
    # static variables
    WEBSITE = "http://lanshark.29a.ch/"
    VERSION = Integer(2, "Version of the config file")
    DOWNLOAD_BS = 65536
    VERSION.comment_out_default = False

    def __init__(self, path):
        configuration.Config.__init__(self)
        self.dir = os.path.dirname(path)
        self.PID_FILE = self.PID_FILE.replace("$configdir", self.dir)
        if os.path.exists(path):
            self.load(path)
            if self.VERSION < self.__class__.VERSION.default:
                self.VERSION = self.__class__.VERSION.default
                self.save(path)
        else:
            self.save(path)
        self.set_prefix(os.path.abspath(os.path.join(os.path.dirname(__file__),
                os.pardir, os.pardir)))
        self.path = path
        socket.setdefaulttimeout(self.SOCKET_TIMEOUT/1000.0)
        if self.PSYCO:
            try:
                import psyco
                psyco.profile()
                print "Psyco JIT optimization active"
            except ImportError:
                print "Psyco enabled but not installed"
        sys.path.append(os.path.dirname(__file__))

    def set_prefix(self, value):
        """Set the prexif for example /usr"""
        self.PREFIX = value
        self.DATA_PATH = os.path.join(self.PREFIX, "share", "lanshark")
        self.LOCALE_PATH = os.path.join(self.PREFIX, "share", "locale")

    def save(self, path=None):
        configuration.Config.save(self, path or self.path)

if "win" in sys.platform:
    # todo: make freezable
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
        "..", "..", "conf"))
else:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "~/.config")
    xdg_config_home = os.path.expanduser(xdg_config_home)
    if not os.path.exists(xdg_config_home):
        try:
            os.path.mkdir(xdg_config_home)
        except os.error, e:
            xdg_config_home = os.path.expanduser("~")
    config_dir = os.path.join(xdg_config_home, "lanshark")

if not os.path.exists(config_dir):
    os.mkdir(config_dir)
config_path = os.path.join(config_dir, "lanshark.conf")
config = Config(config_path)

import logging
LOGLEVEL = config.DEBUG and logging.DEBUG or config.VERBOSE and\
           logging.INFO or logging.WARN
logging.basicConfig(level=LOGLEVEL)
