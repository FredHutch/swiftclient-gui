#!/usr/bin/env python

import sys,os
import time
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
    viewer = LogViewer(root, sys.argv[1])
    viewer.mainloop()
