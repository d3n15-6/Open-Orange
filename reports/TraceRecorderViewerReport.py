#encoding: utf-8
from OpenOrange import *
from Report import Report
import os.path

class TraceRecorderViewerReport(Report):

    def run(self):
        self.startTable()
        try:    
            ln = 0
            for trace in self.trace:
                if not self.filenamefilter or self.filenamefilter == trace[2]:
                    line = "%s:\t\t%s" % (os.path.basename(trace[2]), trace[3])
                    self.startRow()
                    c = "white"
                    s = ""
                    if ln == self.item - 10:
                        s = '<a name="currentline"></a>'
                    if ln == self.item: 
                        c = "yellow"
                    self.addValue(s + line.replace("\n", "") , BGColor=c, CallMethod="goTrace", Parameter=ln)
                    self.endRow()
                ln += 1
        except KeyError, e:
            pass
        self.endTable()
        
    
    def goTrace(self, param, value):
        self.window.item = int(param)
        self.window.refreshViewers()