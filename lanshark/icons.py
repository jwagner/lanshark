#!/usr/bin/python
from __future__ import with_statement
"""Icons - A library to do some common icon stuff"""
import mimetypes
import os
mime2icon = {
    "application-x-bzip2": "package-x-generic",
    "application-x-tar": "package-x-generic",
    "application-zip": "package-x-generic",
    "application-ogg": "audio-x-generic",
    "text-html": "text-html"
}

for mime, ext in (("application/x-bzip2", "bz2"), ("application/x-rar", "rar")):
    mimetypes.add_type(mime, ext)

class IconFactory:
    """
       The IconFactory base class implements some common
       stuff like name guessing
    """
    def guess_icon_name(self, filename):
        """guess the icon name from the filename"""
        #import pdb
        #pdb.set_trace()
        if filename.endswith("/"):
            return "folder"
        mimetype = mimetypes.guess_type(filename)[0]
        if mimetype:
            mimetype = mimetype.replace("/", "-")
            media = mimetype.split("-")[0]
            for icon in (mimetype, "gnome-mime-" + mimetype,
                media + "-x-generic", "gnome-mime-" + media,
                media):
                if self.has_icon(icon):
                    return icon
            if mimetype in mime2icon:
                if self.has_icon(mime2icon[mimetype]):
                    return mime2icon[mimetype]
        if filename.lower().endswith(".ogg"):
            # ogg files do mostly contain (only) audio
            return "audio-x-generic"
        return "text-x-generic-template"

    def guess_icon(self, filename):
        """guess the icon from the filename"""
        return self.get_icon(self.guess_icon_name(filename))

    def has_icon(self, name):
        """check if the icon is in the factory"""
        return not self.get_icon(name) is None

    def get_icon(self, name):
        """Implement at least this method in the factory implementation"""
        pass

class URLIconFactory(IconFactory):
    """The URLIconFactory returns a url to the icon"""
    def __init__(self, documentroot, urlroot, ext=".png"):
        self.documentroot = documentroot
        self.urlroot = urlroot
        self.ext = ext

    def get_icon(self, name):
        path = os.path.join(self.documentroot, name) + self.ext
        if os.path.exists(path):
            return self.urlroot + name + self.ext
        return None
