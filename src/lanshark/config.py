"""The lanshark config module loads and saves config files"""
import os, sys

import socket
import locale
locale.setlocale(locale.LC_ALL, '')

from lanshark.configuration import Boolean, Integer, String, StringList, Enum
from lanshark import configuration


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

def get_openfile():
    if sys.platform == "darwin":
        return "open"
    else:
        return select_app("xdg-open", "exo-open", "gnome-open") or ""

def get_sys_encoding():
    if sys.platform.startswith("win"):
        return "utf8"
    return locale.getpreferredencoding()

class Config(configuration.Config):
    LOG_LEVEL = Enum('CRITICAL',
                     ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'),
                     'Sets the verbosity of logging output')
    LOG_TARGET = String('-',
                        'Target of logging output. Set to - to log stderr')
    LOG_FORMAT = String('%(levelname)s:%(name)s:%(message)s',
                        'Format of logging output. '
                        'See http://docs.python.org/lib/node422.html '
                        'for format description')
    BROADCAST_IP = String("255.255.255.255",
            "IP to use for udp broadcasts")
    PORT = Integer(31337, "Port to use for both UDP and TCP")
    SEARCH_TIMEOUT = Integer(5,
            "Time to wait for search results in seconds")
    DISCOVER_TIMEOUT = Integer(5,
            "Time to wait for new hosts to answer in seconds")
    DISCOVER_INTERVAL = Integer(60,
            "Interval to search for new computers in seconds")
    NETWORK_NAME = String("HELO",
            "Word to use for discovery, might act as simple password")
    NETWORK_PASSWORD = String("", "Network password")
    CACHE_TIMEOUT = Integer(600, "HTTP cache time to live")
    SHARE_PATH = String("", "Path to the files you want to share")
    INCOMING_PATH = String("", "Path to store the downloaded files")
    MAX_SEARCH_RESULTS = Integer(128,
            "Maximal number of search results per peer")
    FOLDER_IMAGES = StringList([r"\.?folder\.(png|jpg|gif|img)$",
                         r"cover\.(png|jpg|gif)$",
                         r"(cover\-)?front\.(png|jpg|gif)$",
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
            "broadcasts are not avaible. "
            "Exmaple: example.com:31337, 192.168.1.2:31337")
    HIDDEN_FILES = StringList([r"\..*", r"Thumbs\.db"],
            "Regexps to match hidden files")
    PSYCO = Boolean(False, "Enable psyco JIT")
    OPENFILE = String(get_openfile(), "The application used to start/open files")
    # static variables
    LANGUAGES = [locale.getdefaultlocale()[0] or "en_US", "en_US"]
    WEBSITE = "http://lanshark.29a.ch/"
    VERSION = Integer(5, "Version of the config file")
    VERSION.comment_out_default = False
    DOWNLOAD_BS = 65536

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

    @property
    def debug(self):
        return self.LOG_LEVEL == 'DEBUG'

    def set_prefix(self, value):
        """Set the prexif for example /usr"""
        self.PREFIX = value
        self.DATA_PATH = os.path.join(self.PREFIX, "share", "lanshark")
        self.LOCALE_PATH = os.path.join(self.PREFIX, "share", "locale")

    def save(self, path=None):
        configuration.Config.save(self, path or self.path)

if "win" in sys.platform:
    # portable
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
        "..", "..", "conf"))
    if not os.path.exists(config_dir):
        # installed
        config_dir = os.path.expanduser("~\\lanshark")
else:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "~/.config")
    xdg_config_home = os.path.expanduser(xdg_config_home)
    if not os.path.exists(xdg_config_home):
        try:
            os.mkdir(xdg_config_home)
        except os.error, e:
            xdg_config_home = os.path.expanduser("~")
    config_dir = os.path.join(xdg_config_home, "lanshark")

if not os.path.exists(config_dir):
    os.mkdir(config_dir)
config_path = os.path.join(config_dir, "lanshark.conf")
config = Config(config_path)

import logging
logger = logging.getLogger('lanshark')
if config.LOG_TARGET == '-':
    handler = logging.StreamHandler()
else:
    handler = logging.FileHandler(config.LOG_TARGET)
handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(handler)
logger.setLevel(getattr(logging, config.LOG_LEVEL))
