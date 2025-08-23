#encoding: utf-8
from OpenOrange import *

ParentLogSettings = SuperClass("LogSettings", "Setting", __file__)
class LogSettings(ParentLogSettings):
    buffer = SettingBuffer()
    
    __records__ = {}
    __reports__ = {}
    
    @classmethod
    def loadBuffer(self):
        ls = LogSettings.bring()
        if ls.Enabled:
            for record in ls.Records:
                LogSettings.__records__[record.RecordName] = record.Mode
            for report in ls.Reports:
                LogSettings.__reports__[report.ReportName] = report.VersionsQty
                
    def shouldLogEvents(self, recordname):
        res = LogSettings.__records__.get(recordname, None)
        if res is None:
            rec = NewRecord(recordname)
            res = rec.__class__.defaultLoggingMode()
            LogSettings.__records__[recordname] = res
        return (res >= 1)

    def shouldLogReportEvents(self, reportname):
        res = LogSettings.__reports__.get(reportname, None)
        if res is None:
            exec("from %s import %s as cls" % (reportname,reportname))
            res = cls.defaultLoggingVersionsQty()
            LogSettings.__reports__[reportname] = res
        return (res >= 1)
    
    def shouldStoreVersions(self, recordname):
        res = LogSettings.__records__.get(recordname, None)
        if res is None:
            rec = NewRecord(recordname)
            res = rec.__class__.defaultLoggingMode()
            LogSettings.__records__[recordname] = res
        return (res >= 2)


LogSettings.loadBuffer()