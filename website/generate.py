#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Renders a bunch of mako templates

Todo:
    Better Errorhandling
    mtime Checks
    commandline interface
"""

from __future__ import with_statement

import os
from os import path

import mako.lookup
import mako.exceptions

def generate(source, dest):
    lookup = mako.lookup.TemplateLookup(directories=[source])

    def generate_dir(dirpath):
        sourcepath = path.join(source, dirpath)
        destpath = path.join(dest, dirpath)
        pages = filter(lambda p: p[0] != "." and not p.endswith(".mako"),
                os.listdir(sourcepath))
        for page in pages:
            template_path = path.join(dirpath, page)
            template_sourcepath = path.join(source, template_path)
            template_destpath = path.join(dest, 
                    template_path.replace(".mako.",""))
            if path.isdir(template_sourcepath):
                if not path.exists(template_destpath):
                    os.mkdir(template_destpath)
                generate_dir(template_path)
            else:
                template = lookup.get_template(template_path)
                print "* Generating " + template_destpath
                try:
                    html = template.render(dirpath=dirpath, page=page)
                except:
                    print mako.exceptions.text_error_template().render()
                else:
                    with open(template_destpath, "w") as f:
                        f.write(html)

    generate_dir("")
    print "Done"

if __name__ == "__main__":
    generate("mako", "htdocs")
