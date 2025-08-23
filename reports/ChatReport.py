#encoding: utf-8
# Nov/09 - MSP
from OpenOrange import *
from Report import Report
import os
import time
from Company import Company


class ChartReportThread(CThread):
    
    def run(self):
        sysprint("ACA")
        self.setName("Chat Report Thread")
        self.finish = False
        while not self.finish and not self.shouldFinish():
            cc = Company.getCurrent()
            try:
                self.report.users = cc.getServerConnection().getLoguedUsers()
            except AppException, e:
                for i in range(10):
                    if self.shouldFinish(): return
                    time.sleep(1)
            time.sleep(3)
            
            
class ChatReport(Report):

    def run(self):
        sysprint("111!")
        if not hasattr(self, "chatthread"):
            sysprint("222")
            self.chatthread = ChartReportThread()
            self.chatthread.report = self
            self.chatthread.start()
            self.users = []
        sysprint("3333")
        self.setAutoRefresh(3000)
        cc = Company.getCurrent()
        if not cc.isApplicationServerCompany():
            message("Invalid Company type")
            return
                    
        self.startTable()
        self.startRow()
        self.addValue(now().strftime("%H:%M:%S"))
        self.endRow()
        for u in dict(zip(self.users,self.users)):
            self.startRow()
            self.addValue(u, CallMethod="openChatWindow", Parameter=u)
            self.endRow()
        self.endTable()
        
    def openChatWindow(self, param, value):
        from OOChatClientWindow import OOChatClientWindow
        from OOChatClient import OOChatClient    
        wl = getOpenWindowsList()
        wnd = None
        for w in wl:
            if isinstance(w, OOChatClientWindow):
                if w.getRecord().ToUsers == param:
                    wnd = w
                    r = wnd.getRecord()
                    break
        if not wnd:
            wnd = OOChatClientWindow()
            r = OOChatClient()
            r.ToUsers = param
            wnd.setRecord(r)  
            wnd.open()     
        r.setFocusOnField("Message")
        
    def beforeClose(self):
        if hasattr(self, "chatthread"):
            self.chatthread.finish = True
        return True
        