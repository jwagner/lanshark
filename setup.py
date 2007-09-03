#!/usr/bin/env python
#from distutils.core import setup
from distutils.core import setup
import os
try:
    import py2exe
except ImportError:
    pass

def ls_r(dir):
    def do_reduce(a, b):
        files = []
        for f in b[2]:
            files.append(os.path.join(b[0], f))
        a.append((b[0], files))
        return a
    return reduce(do_reduce, os.walk(dir), [])

options = []

setup(name='lanshark',
      version='0.0.1',
      description='Filesharing tool for local area networks',
      author='Jonas Wagner',
      author_email='veers@gmx.ch',
      url='http://lanshark.29a.ch',
      packages=['lanshark', 'simplejson'],
      package_dir={'lanshark': 'src/lanshark',
          'simplejson': 'src/lanshark/simplejson'},
      scripts=['src/lansharkgui', 'src/lansharkc'],
      windows=[{'script': 'src/lansharkgui',
          'icon_resources': [(1, 'lanshark.ico')],
          'dest_base': 'lanshark'}],
      options={'py2exe':{
          'packages': 'encodings',
          'includes': 'cairo, pango, pangocairo, atk, gobject',
          'dist_dir': 'dist/win32',
          'optimize': 2,
          }},
      license='GNU GPL v3',
      data_files=ls_r('share')+ls_r('bin'),
      #install_requires=["pygtk >= 2.10"],
      classifiers=['Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Environment :: Web Environment',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Natural Language :: German',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Communications :: File Sharing']
      )
