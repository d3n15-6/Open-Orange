#encoding: utf-8
from OpenOrange import *
from Report import Report
from HistoryManager import HistoryManager

class HistoryManagerReport(Report):
    instances = {}

    def run(self):
        HistoryManagerReport.instances[self] = True
        self.getView().resize(370,600)
        self.printReportTitle("Recent Documents")
        self.startTable()
        self.startHeaderRow()
        self.addValue("Date")
        self.addValue("Time")
        self.addValue("Record")
        self.endHeaderRow()
        hm = HistoryManager()
        k = len(hm)-1
        for item in reversed(hm):
            self.startRow()
            self.addValue(item[0].strftime("%d/%m/%Y"))
            self.addValue(item[1].strftime("%H:%M:%S"))
            if (":" in item[2]):
                rname,rnr = item[2].split(":")
                rname = tr(rname)
                self.addValue("%s:%s" %(rname,rnr), CallMethod="openRecord", Parameter=k)
            else:
                self.addValue(item[2], CallMethod="openRecord", Parameter=k)
            k -= 1
            self.endRow()
        self.endTable()

    def beforeClose(self):
        try:
            del HistoryManagerReport.instances[self]
        except:
            pass
        return True
        
    def openRecord(self, param, value):
        HistoryManager.openItem(int(param))
