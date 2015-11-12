#!/usr/bin/env python3

import sys, os
import time

if sys.hexversion > 0x03000000:
    from tkinter import *
    from tkinter.scrolledtext import ScrolledText
else:
    from Tkinter import *
    from ScrolledText import ScrolledText


class LogViewer(Frame):
    def __init__(self, parent, filename):
        Frame.__init__(self,parent)
        self.filename = filename 
        self.file = open(filename, 'r')
        self.text = ScrolledText(parent)
        self.text.pack(fill=BOTH)
        data = self.file.read()
        self.size = len(data)
        self.text.insert(END, data)
        self.after(100, self.poll)

    def poll(self):
        if os.path.getsize(self.filename) > self.size:
            data = self.file.read()
            self.size = self.size + len(data)
            self.text.insert(END, data)
        self.after(100,self.poll)

if __name__ == "__main__":
    root = Tk()
    logfile=''
    if len(sys.argv) > 1:
        logfile = sys.argv[1]
    if os.path.exists(logfile):
        viewer = LogViewer(root, sys.argv[1])
        viewer.mainloop()
    elif logfile == '':
        print('usage: tail.py <filename>')
    else:
        print('file %s not found' % logfile)
