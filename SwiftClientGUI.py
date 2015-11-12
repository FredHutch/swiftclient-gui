#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SwiftClientGUI is a simple wrapper for the Python Swift client that
allows users to upload and download files to/from a swift object store
"""

import sys, os, inspect, argparse, logging, json, subprocess
import getpass, optparse, tempfile, socket, base64
import easygui
import swiftclient, keystoneclient
#import decryptsme

from swiftclient import shell
from swiftclient import RequestException
from swiftclient.exceptions import ClientException
from swiftclient.multithreading import OutputManager

# the new way of using swift 
from swiftclient.service import SwiftService

class KeyboardInterruptError(Exception): pass

#constants
__app__ = "Swift Client GUI"
__ver__ = "0.17"
__ver_date__ = "2015-11-08" 
__copy_date__ = "2015"
__author__ = "Dirk Petersen <dirk11@fredhutch.org>"
__company__ = "Fred Hutch, Seattle"

HKEY_CURRENT_USER = -2147483647
HKEY_LOCAL_MACHINE = -2147483646
REG_SZ = 1
REG_DWORD = 4
KEY = 'gjkdjgndfhdgfgdldfgj902u54nkk34u8os'
USERNAME = getpass.getuser()
OS = sys.platform
IP = socket.gethostbyname(socket.gethostname())

if IP.startswith('140.107.'):
    DEFAULT_AUTH_URL="https://tin.fhcrc.org/auth/v2.0"
    DEFAULT_TENANT="AUTH_Swift_llllllllll_f"
else:
    DEFAULT_AUTH_URL="https://host.domain.org/auth/v2.0"
    DEFAULT_TENANT="AUTH_xxxxxxxxxxxx"
    
#variables
_default_global_options = {}

logger = logging.getLogger('SWG')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(os.path.join(tempfile.gettempdir(),"SwiftClientGUI.debug.txt"))
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.info('username: %s  temp: %s' % (USERNAME, tempfile.gettempdir()))

#sys.stdout = open(os.path.join(tempfile.gettempdir(),"SwiftClientGUI.out.txt"), 'w')
#sys.stderr = open(os.path.join(tempfile.gettempdir(),"SwiftClientGUI.err.txt"), 'w')

def main(args):
    """ main entry point """

    global _default_global_options
    # set environment var for valid CA SSL cert
    if not OS.startswith('linux'):
        os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(get_script_dir(), "cacert.pem")
        
    meta=[]
    authlist=setup_read()
    
##    print('os_auth_token', _default_global_options['os_auth_token'])
##    print('os_storage_url', _default_global_options['os_storage_url'])
##    print('os_auth_url', _default_global_options['os_auth_url'])
##    print('os_username', _default_global_options['os_username'])
##    print('os_password', _default_global_options['os_password'])
##    print('os_tenant_name', _default_global_options['os_tenant_name'])
##    print('os_region_name', _default_global_options['os_region_name'])
##    print('auth', _default_global_options['auth'])
##    print('user', _default_global_options['user'])
##    print('key', _default_global_options['key'])

##    _default_global_options['os_storage_url'] = 'https://tin.fhcrc.org/v1/AUTH_Swift__ADM_SciComp'
##    _default_global_options['os_auth_token'] = 'AUTH_tk3d7438ae35934666affdefbf26429ae3'

##    _default_global_options['os_auth_url'] = 'https://tin.fhcrc.org/auth/v2.0'
##    _default_global_options['os_username'] = 'petersen'
##    _default_global_options['os_password'] = ''
##    _default_global_options['os_tenant_name'] = 'AUTH_Swift__ADM_SciComp'
    
    stats=SwiftService(options=_default_global_options).stat()    
    while not stats["success"] == True:
        if not setup_write():
            return False        
        authlist=setup_read()
        stats=SwiftService(options=_default_global_options).stat()

    swifttenant=stats["items"][0][1]

    #args.uploadfolder='c:/temp/test'
    #args.downloadtofolder='c:/temp/test'

    if not args.downloadtofolder and not args.uploadfolder:
        choices = ["Upload to Swift","Download from Swift","Change Credentials","Cancel"]
        choice=easygui.buttonbox("To copy data from and to Swift please right click on a folder in Explorer and select 'Swift:...' ..... or select one of the following options", choices=choices)
        if choice == 'Upload to Swift':
            args.uploadfolder=easygui.diropenbox("Please select a folder for upload","Uploading Folder")
        elif choice == 'Download from Swift':
            args.downloadtofolder=easygui.diropenbox("Please select a folder to download to.","Downloading to Folder")
        elif choice == 'Change Credentials':
            if not setup_write():
                return False 
        elif choice == 'Cancel':
            sys.exit()
            
    if args.downloadtofolder:
        if OS == "win32":
            args.downloadtofolder=args.downloadtofolder.replace('\\','/')
        args.downloadtofolder=args.downloadtofolder.rstrip('/')
        basename=os.path.basename(args.downloadtofolder)
        #easygui.msgbox("Will now download from Swift to folder %s" % args.downloadtofolder, "%s launched from %s" % (__app__, args.downloadtofolder))
        container,prefix=selSwiftFolderDownload(_default_global_options,swifttenant)
        subdir=container+'/'+prefix
        subdir=os.path.basename(subdir.rstrip('/'))
        ret=download_folder_from_swift(args.downloadtofolder+'/'+subdir,prefix,container)       
    elif args.uploadfolder:
        if OS == "win32":
            args.uploadfolder=args.uploadfolder.replace('\\','/')
        args.uploadfolder=args.uploadfolder.rstrip('/')
        basename=os.path.basename(args.uploadfolder)
        container=selSwiftFolderUpload(_default_global_options,swifttenant,basename)
        if container:
            pseudodir=os.path.basename(args.uploadfolder)
            if container.startswith("------------ Upload to root of (new) container"):
                container=basename
                pseudodir=''
            ret=upload_folder_to_swift(args.uploadfolder,pseudodir,container,meta)

    #print("End")

def selSwiftFolderUpload(options,swifttenant,basename):
    visible_containers = []
    #visible_containers.append("----------- Switch Account (current: %s) --------------------" % swifttenant)
    visible_containers.append("------------ Upload to root of (new) container '%s'-----------" % basename)
    with SwiftService(options=options) as swift:
        # Do work here
        #x=swift.stat(container=None, objects=None, options=None)
        #logger.info('swift stat: %s' % x)
        listing=swift.list(container=None, options=None)
        for o in listing:
            for i in o['listing']:
                if not i['name'].startswith('.'):
                    visible_containers.append(i['name'])
    msg="Please pick a root folder (container) to upload to"
    choice = easygui.choicebox(msg,"Select Folder/Container for data transfer",visible_containers)
    return choice

def selSwiftFolderDownload(options,swifttenant):
    choice=''
    oldchoice=''
    container=''
    prefix=''
    myoptions={'prefix': None}
    with SwiftService(options=options) as swift:
        
        while not choice.startswith('------------ DOWNLOAD FOLDER'):            
            visible_folders = []         
            if choice.startswith("------------ GO UP ONE LEVEL"):
                if not '/' in oldchoice:
                    choice = ''
                    container = ''
                    myoptions={'prefix': None}
                else:
                    choice=os.path.dirname(oldchoice.rstrip("/"))+'/'
                    if choice == '/':
                        choice=container
                        container=''
                                 
            #print('choice1:',choice)
            #visible_containers.append("----------- Switch Account (current: %s) --------------------" % swifttenant)
                        
            if choice != '':                
                if container == '':
                    container=choice
                    myoptions={'prefix': None, 'delimiter': '/'}
                else:
                    prefix=choice
                    myoptions={'prefix': prefix, 'delimiter': '/'}
                            
                visible_folders.append("------------ DOWNLOAD FOLDER '%s/%s' NOW-----------" % (container, prefix))
                visible_folders.append("------------ GO UP ONE LEVEL -----------")

            listing=swift.list(container=container, options=myoptions)
            
            for o in listing:
                for i in o['listing']:
                    cnt=0
                    if 'subdir' in i:
                        visible_folders.append(i['subdir'])
                        cnt+=1
                    elif not i['name'].startswith('.') and container=='':
                        visible_folders.append(i['name'])
                        cnt+=1
            if cnt == 0:
                if easygui.boolbox('Do you want to download /%s/%s now?' % (container,prefix), "Downloading stuff", ["    Yes    ","   No   "]):
                    return container, prefix
                else:
                    oldchoice=choice
                    choice="------------ GO UP ONE LEVEL"
                    continue
            msg="Please select a sub folder for download or download the current folder '%s/%s'" % (container,prefix)
            oldchoice=choice
            choice = easygui.choicebox(msg,"Select Folder/Container for data transfer",visible_folders)
            if not choice:
                return None, None
    return container, oldchoice
                
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

def gettailcmd(outpath):
    if OS == "win32":
        wintail = os.path.join(get_script_dir(),'wintail.exe')
        return [wintail,outpath]
    else:
        pytail = os.path.join(get_script_dir(),'tail.py')
        return [sys.executable,pytail,outpath]
    
def upload_folder_to_swift(fname,swiftname,container,meta):
    oldout = sys.stdout
    olderr = sys.stderr
    outfile = 'Swift_upload_'+container+'_'+swiftname.rstrip('/').replace('/','_')+".log"
    outpath = os.path.join(tempfile.gettempdir(),outfile)
    fh = open(outpath, 'w')
    sys.stdout = fh
    sys.stderr = fh
    print("upload logging to %s" % outpath)
    print("uploading to %s/%s, please wait ....." % (container,swiftname))
    sys.stdout.flush()
    tailpid=subprocess.Popen(gettailcmd(outpath))
    final=[container,fname]
    if meta:
        final=meta+final
    sw_upload("--object-name="+swiftname,
        "--segment-size=1073741824",   # should be _default_global_options['segment_size'] but is not working
        "--use-slo",
        "--changed",
        "--segment-container=.segments_"+container,
        "--header=X-Object-Meta-Uploaded-by:"+USERNAME,*final)
    print("upload logged to %s" % outpath)
    print("SUCCESS: %s uploaded to %s/%s" % (fname,container,swiftname))
    sys.stdout = oldout
    sys.stderr = olderr
    fh.close()

def download_folder_from_swift(fname,swiftname,container):
    oldout = sys.stdout
    olderr = sys.stderr
    outfile = 'Swift_download_'+container+'_'+swiftname.replace('/','_')+".log"
    outpath = os.path.join(tempfile.gettempdir(),outfile)
    fh = open(outpath, 'w')
    sys.stdout = fh
    sys.stderr = fh
    print("download logging to %s" % outpath)
    print("downloading to %s/%s, please wait ....." % (container,swiftname))
    sys.stdout.flush()
    tailpid=subprocess.Popen(gettailcmd(outpath))
    sw_download('--prefix='+swiftname,
        '--output-dir='+fname,
        '--remove-prefix',
        container)
    print("download logged to %s" % outpath)
    print("SUCCESS: %s/%s downloaded to %s" % (container,swiftname,fname))
    sys.stdout = oldout
    sys.stderr = olderr
    fh.close()

# define minimum parser object to allow swiftstack shell to run (taken from swbundler)
def shell_minimal_options():

   parser = optparse.OptionParser()

   parser.add_option('-A', '--auth', dest='auth',
      default=_default_global_options['auth'])
   parser.add_option('-V', '--auth-version',
      default=os.environ.get('ST_AUTH_VERSION',
         (os.environ.get('OS_AUTH_VERSION','2.0'))))
   parser.add_option('-U', '--user', dest='user',
      default=_default_global_options['user'])
   parser.add_option('-K', '--key', dest='key',
      default=_default_global_options['key'])

   parser.add_option('--os_auth_token',default=_default_global_options['os_auth_token'])
   parser.add_option('--os_storage_url',default=_default_global_options['os_storage_url'])

   parser.add_option('--os_username', default=_default_global_options['os_username'])
   parser.add_option('--os_password', default=_default_global_options['os_password'])
   parser.add_option('--os_auth_url', default=_default_global_options['os_auth_url'])

   parser.add_option('--os_user_id')
   parser.add_option('--os_user_domain_id')
   parser.add_option('--os_user_domain_name')
   parser.add_option('--os_tenant_id')
   parser.add_option('--os_tenant_name',default=_default_global_options['os_tenant_name'] )
   parser.add_option('--os_project_id')
   parser.add_option('--os_project_domain_id')
   parser.add_option('--os_project_name')
   parser.add_option('--os_project_domain_name')
   parser.add_option('--os_service_type')
   parser.add_option('--os_endpoint_type')
   parser.add_option('--os_region_name', default=_default_global_options['os_region_name'])
   
   parser.add_option('-v', '--verbose', action='count', dest='verbose',
       default=1, help='Print more info.')

   return parser

# wrapper function for swiftstack shell functions
def sw_shell(sw_fun,*args):

   if _default_global_options['os_auth_token'] and _default_global_options['os_storage_url']:
      args=args+("--os_auth_token",_default_global_options['os_auth_token'],
         "--os_storage_url",_default_global_options['os_storage_url'])

   args = ('',) + args
   with OutputManager() as output:
      parser = shell_minimal_options()
      try:
         sw_fun(parser, list(args), output)
         #easygui.codebox("Contents of file", "Show File Contents", output)
      except (ClientException, RequestException, socket.error) as err:
         output.error(str(err))
 
def sw_download(*args):
    sw_shell(shell.st_download,*args)
 
def sw_upload(*args):
    sw_shell(shell.st_upload,*args)

def sw_post(*args):
    sw_shell(shell.st_post,*args)

def getDriveAuth():
    # get config settings from openstack drive.
    mykey = winreg.OpenKey(HKEY_CURRENT_USER,'Software\Vehera\OpenStack.Drive', 0, winreg.KEY_ALL_ACCESS)
    swiftauthurl=winreg.QueryValueEx(mykey,"Endpoint")
    print(swiftauthurl)
    print(decryptsme.decrypt(swiftauthurl))
    print(decryptsme.decrypt("##?&256UKCnrrvu<))roh(`nete(ita)gsrn)p4(6"))
    print(winreg.QueryValueEx(mykey,"Tenant"))
    print(decryptsme.decrypt("('##7$256WIAEQPL[Wsmbp[[E@I[WgmGkit', 1)"))
    
    swifttenant=decryptsme.decrypt(winreg.QueryValueEx(mykey,"Tenant"))
    swiftaccount=decryptsme.decrypt(winreg.QueryValueEx(mykey,"Username"))
    swiftpassword=decryptsme.decrypt(winreg.QueryValueEx(mykey,"Password"))
    print(swiftauthurl, swifttenant, swiftaccount, swiftpassword)

def encode(KEY, clear):
    enc = []
    b64=None
    for i in range(len(clear)):
        key_c = KEY[i % len(KEY)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
        b64 = base64.urlsafe_b64encode("".join(enc).encode('utf-8'))
    if b64:
        return b64.decode('utf-8')
    return ""

def decode(KEY, enc):
    dec = []
    b64 = base64.urlsafe_b64decode(enc.encode('utf-8'))
    enc = b64.decode('utf-8')
    for i in range(len(enc)):
        key_c = KEY[i % len(KEY)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

def setup_read():    
    if OS == "linux2" or OS == "linux":
        authlist = setup_read_linux()
    elif OS == "win32":
        authlist = setup_read_win()
    elif OS == "darwin":
        authlist = setup_read_mac()
    else:
        print("Could not detect your platform: '%s'" % OS)
        authlist = setup_read_linux()

    auth, user, key = None, None, None
    authversion = '2.0'
    if authlist[0].endswith('/v1.0'):
        authversion = '1.0'
        auth = authlist[0]
        user = authlist[2]
        key = authlist[3]

    global _default_global_options
    _default_global_options = {
        "segment_size": 1073741824,
##        "segment_size": 2147483648,  #2GB
        "use_slo": True,
        "changed": True,
        "auth_version": os.environ.get('ST_AUTH_VERSION', authversion),
        "auth": os.environ.get('ST_AUTH', auth),
        "user": os.environ.get('ST_USER', user),
        "key": os.environ.get('ST_KEY', key),
        "retries": 5,
        "os_username": os.environ.get('OS_USERNAME', authlist[2]),
        "os_password": os.environ.get('OS_PASSWORD', authlist[3]),
        "os_tenant_id": os.environ.get('OS_TENANT_ID'),
        "os_tenant_name": os.environ.get('OS_TENANT_NAME', authlist[1]),
        "os_auth_url": os.environ.get('OS_AUTH_URL', authlist[0]),
        "os_auth_token": os.environ.get('OS_AUTH_TOKEN'),       
        "os_storage_url": os.environ.get('OS_STORAGE_URL'),  
        "os_region_name": os.environ.get('OS_REGION_NAME', 'default'),
        "os_service_type": os.environ.get('OS_SERVICE_TYPE'),
        "os_endpoint_type": os.environ.get('OS_ENDPOINT_TYPE'),        
        }
    return authlist

def setup_write():

    auth = DEFAULT_AUTH_URL
    tenant = DEFAULT_TENANT
    user = USERNAME
    if _default_global_options['os_auth_url']:
        auth = _default_global_options['os_auth_url']
    if _default_global_options['os_tenant_name']:
        tenant = _default_global_options['os_tenant_name']
    if _default_global_options['os_username']:
        user = _default_global_options['os_username']

    msg = "Enter the Swift connection settings"
    title = "OpenStack Swift Authentication"
    fieldNames = ["Swift Auth URL", "Swift Tenant Name", "User Name", "Password"]
    fieldValues = [auth, tenant, user, ""]
    fieldValues = easygui.multpasswordbox(msg,title, fieldNames, fieldValues)

    OS = sys.platform
    if OS == "linux2" or OS == "linux":
        return setup_write_linux(fieldValues)
    elif OS == "win32":
        return setup_write_win(fieldValues)
    elif OS == "darwin":
        return setup_write_mac(fieldValues)
    else:
        print("Could not detect your platform: '%s'" % OS)
        return setup_write_linux(fieldValues)

def setup_read_linux():
    if sys.hexversion > 0x03000000:
        from configparser import ConfigParser 
    else:
        from ConfigParser import ConfigParser

    authlist = [""]*4

    homedir = os.path.expanduser('~')
    if not os.path.exists(homedir+'/.swift'):
        return authlist
        
    # instantiate
    config = ConfigParser()

    try:
        # parse existing file
        config.read(homedir+'/.swift/swiftclient.ini')

        # add a new section and some values
        authlist[0] = config.get('default', 'auth_url')
        authlist[1] = config.get('default', 'tenant')
        authlist[2] = config.get('default', 'user')
        authlist[3] = decode(KEY,config.get('default', 'pass'))
    except:
        print('error reading config swiftclient.ini')
    
    return authlist

def setup_read_win():
    if sys.hexversion > 0x03000000:
        import winreg as winreg
    else:
        import _winreg as winreg

    authlist = [""]*4

    MyHKEY = HKEY_CURRENT_USER
    try:
        mykey = winreg.OpenKey(MyHKEY,'SOFTWARE\OpenStack\SwiftClient', 0, winreg.KEY_ALL_ACCESS)
        authlist[0] = winreg.QueryValueEx(mykey,"auth_url")[0]
        authlist[1] = winreg.QueryValueEx(mykey,"tenant")[0]
        authlist[2] = winreg.QueryValueEx(mykey,"user")[0]
        authlist[3] = decode(KEY,winreg.QueryValueEx(mykey,"pass")[0])
    except:
        print ("Error reading data from registry")
    return authlist
    
def setup_read_mac(authlist):
    # don't have anything for mac, use linux settings for now
    return setup_read_linux(authlist)

def setup_write_linux(authlist):
    if sys.hexversion > 0x03000000:
        from configparser import ConfigParser 
    else:
        from ConfigParser import ConfigParser

    # instantiate
    config = ConfigParser()

    # parse existing file
    #config.read('test.ini')

    # add a new section and some values

    if authlist:
        config.add_section('default')
        config.set('default', 'auth_url', authlist[0])
        config.set('default', 'tenant', authlist[1])
        config.set('default', 'user', authlist[2])
        config.set('default', 'pass', encode(KEY,authlist[3]))

        # save to a file
        homedir = os.path.expanduser('~')
        if not os.path.exists(homedir+'/.swift'):
            os.makedirs(homedir+'/.swift')
        with open(homedir+'/.swift/swiftclient.ini', 'w') as configfile:
            config.write(configfile)
        return authlist
    else:
        return None
    
def setup_write_win(authlist):
    """ setup is executed if this program is started without any command line args. """
    if sys.hexversion > 0x03000000:
        import winreg as winreg
    else:
        import _winreg as winreg
    
    myPath = getMyFile()
    MyHKEY = HKEY_CURRENT_USER

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

    #set wintail position:
    ret = winreg.SetValue(MyHKEY,'SOFTWARE\WinTail\WindowPosition',REG_SZ,"")
    mykey = winreg.OpenKey(MyHKEY,'SOFTWARE\WinTail\WindowPosition', 0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(mykey, "AlwaysOnTop", None, REG_DWORD, 1)
    mykey.Close()
        
    #setting authentication
    if authlist:
        ret = winreg.SetValue(MyHKEY,'SOFTWARE\OpenStack\SwiftClient',REG_SZ,'Openstack authentication settings')
        mykey = winreg.OpenKey(MyHKEY,'SOFTWARE\OpenStack\SwiftClient', 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(mykey, "auth_url", None, REG_SZ, authlist[0])
        winreg.SetValueEx(mykey, "tenant", None, REG_SZ, authlist[1])
        winreg.SetValueEx(mykey, "user", None, REG_SZ, authlist[2])
        winreg.SetValueEx(mykey, "pass", None, REG_SZ, encode(KEY,authlist[3]))
        mykey.Close()
        return authlist
    else:
        return None
        
def setup_write_mac():
    # don't have anything for mac, use linux settings for now
    return setup_write_linux(authlist)
 
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
                            
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()
    sys.exit(main(args))
