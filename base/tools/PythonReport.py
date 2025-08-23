#encoding: utf-8
from OpenOrange import * 
from PythonRecord import PythonRecord

class PythonReport:
    
    def __init__(self, report=None):
        self.__classname__ = None
        self.__specs__ = None
        if report: self.fromReport(report)
    
    def fromReport(self, report):
        self.__classname__ = report.name()
        self.__html__ = report.getHTML()
        self.__specs__ = PythonRecord(report.getRecord())
       

    def toReport(self, report=None):
        if not report: 
            report = NewReport(self.__classname__)
        report.clear()
        report.addHTML(self.__html__)
        self.__specs__.toRecord(report.getRecord())
        return report
        
    def __str__(self):
        return "report %s" % self.__classname__