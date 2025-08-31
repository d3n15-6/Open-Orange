#encoding: utf-8
from OpenOrange import *
from Report import Report

class TraceRecorderFileViewerReport(Report):

    def run(self):
        self.startTable()
        for k in self.trace[self.item][5]:
            self.row(k, str(self.trace[self.item][5][k]))
        self.endTable()
        self.startTable()
        try:    
            ln = 0
            for line in self.trace_files[self.trace[self.item][2]]:
                self.startRow()
                c = "white"
                s = ""
                if ln == self.trace[self.item][4] - 10:
                    s = '<a name="currentline"></a>'
                
                if ln == self.trace[self.item][4]: 
                    c = "yellow"
                self.addValue(s + "<pre>" + str(ln+1).rjust(4,'0') + "  " + line.replace("\n", "") + "</pre>", BGColor=c)
                self.endRow()
                ln += 1
        except KeyError, e:
            pass
        self.endTable()