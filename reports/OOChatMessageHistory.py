#encoding: utf-8
from OpenOrange import *
from Report import Report
import os
import time
import cPickle
           
class OOChatMessageHistory(Report):
    
    def __init__(self):
        Report.__init__(self)
        self.events = []
        
    def run(self):
        pass
        
    def openLink(self, param, value):
        event = self.events[int(param)]
        w = NewWindow(event.linkwindowname)
        r = cPickle.loads(event.linkrecord)
        if w and r:
            w.setRecord(r)
            w.open()
