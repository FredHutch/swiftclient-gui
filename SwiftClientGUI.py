#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SwiftClientGUI is a simple wrapper for the Python Swift client that
allows users to upload and download files to/from a swift object store
"""

import sys, os, inspect, argparse, logging, json
import easygui
import swiftclient, keystoneclient
from swiftclient.service import SwiftService

logger = logging.getLogger('SWG')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('c:/python/py/swift/debug.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)

class KeyboardInterruptError(Exception): pass

__app__ = "Swift Client GUI"
__ver__ = "0.10"
__ver_date__ = "2015-09-18" 
__copy_date__ = "2015"
__author__ = "Dirk Petersen <dirk14@fredhutch.org>"
__company__ = "Fred Hutch, Seattle"

#constants
APPFILE = "SwiftClientGUI.exe"
APPDIR="SwiftClientGUI" # script will be installed under %ProgramFiles%\%APPDIR% or %USERPROFILE%\%APPDIR%
WINDOMAIN="FHCRC"  
HKEY_CURRENT_USER = -2147483647
HKEY_LOCAL_MACHINE = -2147483646
REG_SZ = 1

#variables
USERNAME = os.environ["USERNAME"]
TEMP = os.environ["TEMP"]
#easygui.msgbox(USERNAME,TEMP)
logger.info('username: %s  temp: %s' % (USERNAME, TEMP))
ADGroupCache = {}
BATCHMODE=False
swifttenant="AUTH_Swift_xxxxxx"

def main(args):
    """ main entry point """
    # set environment var for valid CA SSL cert
    os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(get_script_dir(), "cacert.pem")

    global BATCHMODE
    BATCHMODE = False

    _default_global_options = {
        #"os_auth_token": args.os_auth_token,
        #"os_storage_url": args.os_storage_url,
        "segment_size": 1073741824,
        "use_slo": True,
        "changed": True,
                
        
        #"os_auth_token": 'AUTH_tk4d25ddf78b414d9597a296e4f90aacf6',
        "os_auth_token": 'AUTH_tk58475fcbce87465c887f98eb4601e19a',
        "os_storage_url": 'https://tin.fhcrc.org/v1/AUTH_Swift__ADM_SciComp'   
        }

    stats=SwiftService(options=_default_global_options).stat()
    swifttenant=stats["items"][0][1]
        
        #jsonarr=json.dumps(stat,sort_keys=True, indent=2)
        #print(jsonarr)
        #for item in stat:
        #    print(item[[headers])
        #    #easygui.msgbox (

    args.uploadfolder='d:\tmp\dirk'

    if args.downloadtofolder:
        #easygui.msgbox("Will now download from Swift to folder %s" % args.downloadtofolder, "%s launched from %s" % (__app__, args.downloadtofolder))
        folder=selSwiftFolder(_default_global_options,swifttenant,"download")

    elif args.uploadfolder:
        #easygui.msgbox("Will now upload folder %s to Swift" % args.uploadfolder, "%s launched from %s" % (__app__, args.downloadtofolder))
        target=selSwiftFolder(_default_global_options,swifttenant,"upload")
        ret=uploadFolder(args.uploadfolder,target) 
        #print(something)

    else:
        authdata=setup()
        swiftauthurl=authdata[0]
        swifttenant=authdata[1]
        swiftaccount=authdata[2]
        swiftpassword=authdata[3]
        
        easygui.msgbox("To copy Data from and to Swift please right click on a folder in Explorer and select 'Swift:...'", "%s (%s)" % (__app__, myPath))

def uploadFolder(src,targ):
    pass
    

def selSwiftFolder(options,swifttenant,mode):
    visible_containers = []
    visible_containers.append("----------- Switch Account (current: %s) --------------------" % swifttenant)
    if mode=="upload":
        visible_containers.append("------------ Create new root folder (Container) -----------")    
    with SwiftService(options=options) as swift:
        # Do work here
        #x=swift.stat(container=None, objects=None, options=None)
        #logger.info('swift stat: %s' % x)
        listing=swift.list(container=None, options=None)
        for o in listing:
            #easygui.msgbox (o,"o in listing")
            for i in o['listing']:
                if not i['name'].startswith('.'):
                    visible_containers.append(i['name'])
           #print(o['name'])
    if mode=="upload":
        msg="Please pick a root folder (container) to upload to"
    elif mode=="download":
        msg="Please pick a root folder (container) to download from"
    choice = easygui.choicebox(msg,"Select Folder/Container for data transfer",visible_containers)
    return choice
                
def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)

def getMyFile():
    try:
        myFile = os.path.abspath( __file__ )
    except:
        #if hasattr(sys,"frozen") and sys.frozen == "windows_exe": ... does not work
        myFile = os.path.abspath(sys.executable)
    return myFile

def setup():
    """ setup is executed if this program is started without any command line args. """    
    myPath = getMyFile()
    # sys.path.append(myDir)
    # sys.path.insert(0, os.path.dirname(sys.executable))             
    homeDir = os.environ["USERPROFILE"]
    try:
        programFiles = os.environ["ProgramFiles(x86)"]
    except:
        programFiles = os.environ["ProgramFiles"]
        
    # check if this executable is under program files or Users
    targetPath = ""
    MyHKEY = HKEY_CURRENT_USER
##    if myPath.startswith(programFiles):
##        MyHKEY = HKEY_LOCAL_MACHINE
##        targetPath = programFiles+'\\'+APPDIR+'\\'+APPFILE
##    elif myPath.startswith(homeDir):
##        MyHKEY = HKEY_CURRENT_USER
##        targetPath = homeDir+'\\'+APPDIR+'\\'+APPFILE
##            
##    if MyHKEY == "":
##        msg.showerror("This is not properly installed", "The Software should be copied to 'Program Files' or to a user profile and then be executed.")
##        return

    ret = winreg.SetValue(MyHKEY,'SOFTWARE\Classes\Directory\shell\OpenStackSwiftClient1',REG_SZ,'Swift: Upload folder...')
    mykey = winreg.OpenKey(MyHKEY,'SOFTWARE\Classes\Directory\shell\OpenStackSwiftClient1', 0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(mykey, "Icon", None, REG_SZ, '"%s",0' % myPath)
    mykey.Close()
    ret = winreg.SetValue(MyHKEY,'SOFTWARE\Classes\Directory\shell\OpenStackSwiftClient1\command',REG_SZ,'"%s" --upload-folder "%%1"' % myPath)
    
    ret = winreg.SetValue(MyHKEY,'SOFTWARE\Classes\Directory\shell\OpenStackSwiftClient2',REG_SZ,'Swift: Download here ...')
    mykey = winreg.OpenKey(MyHKEY,'SOFTWARE\Classes\Directory\shell\OpenStackSwiftClient2', 0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(mykey, "Icon", None, REG_SZ, '"%s",0' % myPath)
    mykey.Close()
    ret = winreg.SetValue(MyHKEY,'SOFTWARE\Classes\Directory\shell\OpenStackSwiftClient2\command',REG_SZ,'"%s" --download-to-folder "%%1"' % myPath)
        
    #ret = winreg.SetValue(MyHKEY,'SOFTWARE\Classes\Directory\shell\OpenStackSwiftClient3',REG_SZ,'Swift: other options...')
    #ret = winreg.SetValue(MyHKEY,'SOFTWARE\Classes\Directory\shell\OpenStackSwiftClient3\command',REG_SZ,'"%s" -o "%%1"' % targetPath)

    msg = "Enter the Swift connection settings"
    title = "OpenStack Swift V2 connectivity"
    fieldNames = ["Swift Auth URL", "Swift Tenant Name", "AD User Name", "AD Password"]
    fieldValues = ["https://tin.fhcrc.org/auth/v2.0", "AUTH_Swift_xxxxxxxx_x", USERNAME, ""]
    fieldValues = easygui.multpasswordbox(msg,title, fieldNames, fieldValues)

    return fieldValues 
    
 
def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='SwiftClientGUI.py',
        description='a simple GUI wrapper for the Python Swift client')
    parser.add_argument( '--download-to-folder', '-d', dest='downloadtofolder',
        action='store',
        help='a folder on a posix file system ',
        default='' )
    parser.add_argument( '--upload-folder', '-u', dest='uploadfolder',
        action='store',
        help='a folder on a posix file system ',
        default='' )
    parser.add_argument( '--upload-file', '-f', dest='uploadfile',
        action='store',
        help='a folder on a posix file system ',
        default='' )
    parser.add_argument( '--install', '-i', dest='setup',
        action='store_true',
        help='execute the setup',
        default=False)
    parser.add_argument( '--threads', '-t', dest='maxthreads',
        action='store',
        type=int,
        help='maximum number of threads to run (default=10)',
        default=10 )
    parser.add_argument( '--container', '-c', dest='container',
        action='store',
        help='a container in the swift object store',
        default='' )
    parser.add_argument( '--prefix', '-x', dest='prefix',
        action='store',
        help='a swift object prefix',
        default=None)
    parser.add_argument( '--auth-token', '-a', dest='os_auth_token',
        action='store',
        help='a swift authentication token (required when storage-url is used)',
        default=os.environ.get('OS_AUTH_TOKEN'))
    parser.add_argument( '--storage-url', '-s', dest='os_storage_url',
        action='store',
        help='a swift storage url (required when authtoken is used)',
        default=os.environ.get('OS_STORAGE_URL'))                                 
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    if sys.hexversion > 0x03000000:
        import winreg as winreg   
    else:
        import _winreg as winreg 
    # Parse command-line arguments
    args = parse_arguments()
    sys.exit(main(args))
