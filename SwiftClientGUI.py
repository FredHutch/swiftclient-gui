#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SwiftClientGUI is a simple wrapper for the Python Swift client that
allows users to upload and download files to/from a swift object store
"""

import sys, os, inspect, argparse, logging, json, subprocess, tempfile
import getpass, optparse
import easygui
import swiftclient, keystoneclient
import decryptsme

from swiftclient import shell
from swiftclient import RequestException
from swiftclient.exceptions import ClientException
from swiftclient.multithreading import OutputManager

# the new way of using swift 
from swiftclient.service import SwiftService

class KeyboardInterruptError(Exception): pass

#constants
__app__ = "Swift Client GUI"
__ver__ = "0.12"
__ver_date__ = "2015-11-01" 
__copy_date__ = "2015"
__author__ = "Dirk Petersen <dirk14@fredhutch.org>"
__company__ = "Fred Hutch, Seattle"


HKEY_CURRENT_USER = -2147483647
HKEY_LOCAL_MACHINE = -2147483646
REG_SZ = 1
swifttenant="AUTH_Swift_xxxxxx"

#variables
USERNAME = os.environ["USERNAME"]
swift_auth=os.environ.get("ST_AUTH")
swift_auth_token=os.environ.get("OS_AUTH_TOKEN")
storage_url=os.environ.get("OS_STORAGE_URL")

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

def main(args):
    """ main entry point """
    _default_global_options = {
        #"os_auth_token": args.os_auth_token,
        #"os_storage_url": args.os_storage_url,
        "segment_size": 1073741824,
        "use_slo": True,
        "changed": True,                
        #"os_auth_token": 'AUTH_tk4d25ddf78b414d9597a296e4f90aacf6',
        "os_auth_token": 'AUTH_tk3d7438ae35934666affdefbf26429ae3',
        "os_storage_url": 'https://tin.fhcrc.org/v1/AUTH_Swift__ADM_SciComp',
        "os_tenant_name": os.environ.get('OS_TENANT_NAME')
        }

    #getDriveAuth()
    #sys.exit()
        
    # set environment var for valid CA SSL cert
    os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(get_script_dir(), "cacert.pem")

    global swift_auth
    global swift_auth_token
    global storage_url
    global batchmode 

    batchmode=False
    swift_auth_token=_default_global_options["os_auth_token"]
    storage_url=_default_global_options["os_storage_url"]
    
    meta=[]

    stats=SwiftService(options=_default_global_options).stat()
    if not stats["success"]:
        easygui.msgbox("Not Authenticated",__app__)
        ##stats=SwiftService(options=_default_global_options).stat()
        return False
    
    swifttenant=stats["items"][0][1]

    #args.uploadfolder='c:/temp/'
    #args.downloadtofolder='d:/tmp/dl'
    #args.uploadfolder=easygui.diropenbox("Please select a folder for upload","Uploading Folder")
    #args.downloadtofolder=easygui.diropenbox("Please select a folder to download to.","Downloading to Folder")
                       
    if args.downloadtofolder:
        args.downloadtofolder=args.downloadtofolder.replace('\\','/')
        basename=os.path.basename(args.downloadtofolder)
        #easygui.msgbox("Will now download from Swift to folder %s" % args.downloadtofolder, "%s launched from %s" % (__app__, args.downloadtofolder))
        container,prefix=selSwiftFolderDownload(_default_global_options,swifttenant)
        ret=download_folder_from_swift(args.downloadtofolder,prefix,container)
        print('selSwiftFolderDownload',container,prefix)
        
    elif args.uploadfolder:
        args.uploadfolder=args.uploadfolder.replace('\\','/')
        #args.uploadfolder,os.path.basename(args.uploadfolder)
        basename=os.path.basename(args.uploadfolder)
        container=selSwiftFolderUpload(_default_global_options,swifttenant,basename)
        if container=="------------ Upload to new container '%s'-----------" % basename:
            container=basename
            args.uploadfolder=os.path.dirname(args.uploadfolder)
        ret=upload_folder_to_swift(args.uploadfolder,os.path.basename(args.uploadfolder),container,meta)
        #print(something)
    else:
        authdata=setup()
        swiftauthurl=authdata[0]
        swifttenant=authdata[1]
        swiftaccount=authdata[2]
        swiftpassword=authdata[3]
        
        easygui.msgbox("To copy Data from and to Swift please right click on a folder in Explorer and select 'Swift:...'", "%s (%s)" % (__app__, myPath))

def selSwiftFolderUpload(options,swifttenant,basename):
    visible_containers = []
    #visible_containers.append("----------- Switch Account (current: %s) --------------------" % swifttenant)
    visible_containers.append("------------ Upload to new container '%s'-----------" % basename)
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
                    choice=os.path.dirname(oldchoice.strip("/"))+'/'
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

def upload_folder_to_swift(fname,swiftname,container,meta):
    oldout = sys.stdout
    olderr = sys.stderr
    outfile = 'Swift_upload_'+container+'_'+swiftname.replace('/','_')+".log"
    outpath = os.path.join(tempfile.gettempdir(),outfile)
    wintail = os.path.join(get_script_dir(),'wintail.exe')
    fh = open(outpath, 'w')
    sys.stdout = fh
    sys.stderr = fh
    print("upload logging to %s" % outpath)
    print("uploading to %s/%s, please wait ....." % (container,swiftname))
    sys.stdout.flush()
    tailpid=subprocess.Popen([wintail, outpath])
    final=[container,fname]
    if meta:
        final=meta+final
    sw_upload("--object-name="+swiftname,
        #"--segment-size=2147483648",  (This is 2GB)
        "--segment-size=1073741824",
        "--use-slo",
        "--changed",
        "--segment-container=.segments_"+container,
        "--header=X-Object-Meta-Uploaded-by:"+getpass.getuser(),*final)
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
    wintail = os.path.join(get_script_dir(),'wintail.exe')
    fh = open(outpath, 'w')
    sys.stdout = fh
    sys.stderr = fh
    print("download logging to %s" % outpath)
    print("downloading to %s/%s, please wait ....." % (container,swiftname))
    sys.stdout.flush()
    tailpid=subprocess.Popen([wintail, outpath])
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
   global swift_auth,swift_auth_token,storage_url

   parser = optparse.OptionParser()

   parser.add_option('-A', '--auth', dest='auth',
      default=swift_auth)
   parser.add_option('-V', '--auth-version',
      default=os.environ.get('ST_AUTH_VERSION',
         (os.environ.get('OS_AUTH_VERSION','1.0'))))
   parser.add_option('-U', '--user', dest='user',
      default=os.environ.get('ST_USER'))
   parser.add_option('-K', '--key', dest='key',
      default=os.environ.get('ST_KEY'))

   parser.add_option('--os_auth_token',default=swift_auth_token)
   parser.add_option('--os_storage_url',default=storage_url)

   parser.add_option('--os_username')
   parser.add_option('--os_password')
   parser.add_option('--os_auth_url')

   parser.add_option('--os_user_id')
   parser.add_option('--os_user_domain_id')
   parser.add_option('--os_user_domain_name')
   parser.add_option('--os_tenant_id')
   parser.add_option('--os_tenant_name')
   parser.add_option('--os_project_id')
   parser.add_option('--os_project_domain_id')
   parser.add_option('--os_project_name')
   parser.add_option('--os_project_domain_name')
   parser.add_option('--os_service_type')
   parser.add_option('--os_endpoint_type')
   parser.add_option('--os_region_name')
   
   parser.add_option('-v', '--verbose', action='count', dest='verbose',
       default=1, help='Print more info.')

   return parser

# wrapper function for swiftstack shell functions
def sw_shell(sw_fun,*args):
   global swift_auth_token,storage_url

   if swift_auth_token and storage_url:
      args=args+("--os_auth_token",swift_auth_token,
         "--os_storage_url",storage_url)

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
