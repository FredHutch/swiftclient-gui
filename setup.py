# -*- coding: utf-8 -*-

# A simple setup script to create an executable using Tkinter. This also
# demonstrates the method for creating a Windows executable that does not have
# an associated console.
#
# SimpleTkApp.py is a very simple type of Tkinter application
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application

import sys
from cx_Freeze import setup, Executable

base = None
basegui = None
if sys.platform == 'win32':
    basegui = 'Win32GUI'
    if 'bdist_msi' in sys.argv:
        sys.argv += ['--initial-target-dir', 'C:\\Program Files\\OpenStack\\Swift']

options = {
    'build_exe': {
        'packages': [],
        'includes': ['swiftclient'],
        #'excludes': ['Tkinter'],
        'excludes': [],
        'compressed': True,
        #'path': sys.path + ['modules'],
        'include_msvcr': True,
        'icon': 'swift.ico' 
    }
}

executables = [
    Executable(
               script='SwiftClientGUI.py',
               shortcutName='Setup Openstack Swift Client',
               shortcutDir='ProgramMenuFolder',
               #targetDir='OpenStack\\Swift',
               base=basegui),
    Executable('swift.py', base=base)
]

setup(name='OpenStack Swift Client',
      version='2.6.0',
      description='OpenStack Swift command line python based client with optional GUI',
      options=options,
      executables=executables
      )
