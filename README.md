# swiftclient-gui
SwiftClientGUI is a simple wrapper for the Python Swift client that allows users to upload and download files to/from a swift object store by right clicking folders in Windows Explorer.

This blog post explains how it works:
https://swiftstack.com/blog/2015/12/10/using-swift-for-the-rest-of-us/

If you use this make sure that your python-swidftclient 2.6.0 is patched:
https://github.com/FredHutch/python-swiftclient/commit/57ecf5034b1f58566fe06b6ddfde3d932dbf207b


before bulding an msi make sure you hardcode the __version__ string 
and disable the line that tries to use pbr.version in all modules under site-packages, eg
\Lib\site-packages\keystoneclient\__init__.py
\Lib\site-packages\swiftclient\version.py

