#encoding: utf-8
# Nov/09 - MSP
from OpenOrange import *
from Report import Report
import os

class VersionNoveltiesReport(Report):

    def run(self):
        self.printReportName("Version Novelties")
        self.getView().resize(350,500)
        if (not hasattr(self,"noveltiesfilename")):
            from VersionSettings import VersionSettings
            vset = VersionSettings.bring()
            self.noveltiesfilename = ".".join(vset.getNoveltiesFile())
        if (hasattr(self,"noveltiesfilename") and self.noveltiesfilename):
            fname = "./tmp/%s" %(self.noveltiesfilename)
            version = self.noveltiesfilename.split(".")[1]
            import codecs
            if (not os.path.exists(fname)):
                return 
            fobj = open(fname,"r")
            self.startTable()
            self.startRow()
            self.addValue(version)
            self.endRow()
            self.startRow()
            self.addValue("<HR>")
            self.endRow()
            for fline in fobj.readlines():
                self.startRow()
                self.addValue(utf8(fline))
                self.endRow()
            self.endTable()
            self.startTable()
            
            self.startRow()
            self.addValue("<HR>")
            self.endRow()
            
            self.startRow()
            self.addValue(tr("Don't Show This Novelty Again"),Color="blue",CallMethod="dontShow",Parameter="%s,%s" %(currentUser(),version))
            self.endRow()
            self.endTable()

    def dontShow(self, param, value):
        usercode,version = param.split(",")
        from VersionSettings import VersionSettings
        vs = VersionSettings.bring()
        vs.setLastNovelties(usercode,version)
        res = vs.save()
        if (res):
            commit()
            self.close()
        else:
            postMessage("Error Updating Version Settings")