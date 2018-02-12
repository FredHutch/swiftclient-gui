# -*- coding: utf-8 -*-

# A simple setup script to create an executable that includes
# the python-swiftclient and easygui. 

import sys, os 
import requests.certs
from cx_Freeze import setup, Executable

pydir = os.path.dirname(sys.executable)
dlldir = os.path.join(pydir,'DLLs')

os.environ['TCL_LIBRARY'] = pydir + "\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = pydir + "\\tcl\\tk8.6"

base = None
basegui = None
if sys.platform == 'win32':
    basegui = 'Win32GUI'
    #if 'bdist_msi' in sys.argv:
    #    sys.argv += ['--initial-target-dir', 'C:\\Program Files\\OpenStack\\Swift']

options = {
    'build_exe': {
        'packages': [],
        'includes': [],
        'excludes': [],
        'include_files':[
            (requests.certs.where(),'cacert.pem'),
            'WinTail.exe',
            'README.md',
            'tail.py',
            dlldir+'\\tk86t.dll',
            dlldir+'\\tcl86t.dll',
            #('resources', 'resources'),
            #('config.ini', 'config.ini')
            ],
   # not in cx 5.0     'compressed': True,
        #'path': sys.path + ['modules'],
        'include_msvcr': True,
   # not in cx 5.0     'icon': 'swift.ico'
    },
    'bdist_msi': {
        'upgrade_code': '{1AEF9B5A-D776-4224-C8D3-EBB1A7861231}',
        'add_to_path': False,
        'initial_target_dir': 'C:\\Program Files\\OpenStack\\Swift',
    }
}

##bdist_msi_options = {
##    'upgrade_code': '{66620F3A-DC3A-11E2-B341-002219E9B01E}',
##    'add_to_path': False,
##    'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % (company_name, product_name),
##    }
##
##build_exe_options = {
##    'includes': ['atexit', 'PySide.QtNetwork'],
##    }

##setup(name=product_name,
##      version='1.0.0',
##      description='blah',
##      executables=[exe],
##      options={
##          'bdist_msi': bdist_msi_options,
##          'build_exe': build_exe_options})
##

executables = [
    Executable(
               script='SwiftClientGUI.py',
               shortcutName='Openstack Swift Client GUI',
               shortcutDir='ProgramMenuFolder',
               #compress=True,
               icon='swift.ico',
               #targetDir='OpenStack\\Swift',
               base=basegui),
    Executable('swift.py',
               icon='swift.ico',
               base=base)
]

setup(name='OpenStack Swift Client',
      version='3.5.0',
      description='OpenStack Swift Client with optional GUI',
      options=options,
      executables=executables
      )
