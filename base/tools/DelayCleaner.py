#encoding: utf-8
from OpenOrange import *
import time

class DelayCleanerThread(CThread):
    def __init__(self, objects):
        CThread.__init__(self)
        self.objects = objects
    
    def run(self):
        t = len(self.objects)
        for k in range(t):
            self.setName("Object Delay Cleaner (%i/%i)" % (k+1, t))
            self.objects[k] = None
            time.sleep(0.01)
        self.objects = []
            

class DelayCleaner:

    def __init__(self, *args):
        self.objects = []
        self.appendObjects(*args)

    def appendObjects(self, *args):
        for arg in args:
            if isinstance(arg, list) or isinstance(arg, tuple):
                self.objects.extend(arg)
            elif isinstance(arg, dict):
                self.appendObjects(*(arg.keys()))
                self.appendObjects(*(arg.values()))
            self.objects.append(arg)
    
    def __del__(self):
        self.clean()
        
    def clean(self):
        if len(self.objects):
            t = DelayCleanerThread(self.objects)
            self.objects = []
            t.start()
