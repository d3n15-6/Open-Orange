#encoding: utf-8
from OpenOrange import *
from OOChatMessageHistory import OOChatMessageHistory
from core.Event import ChatMessageEvent
import cPickle

ParentOOChatClientWindow = SuperClass("OOChatClientWindow","Window",__file__)
class OOChatClientWindow(ParentOOChatClientWindow):

    def afterShowRecord(self):
        ParentOOChatClientWindow.afterShowRecord(self)
        self.history = OOChatMessageHistory()
        rv = self.getReportView("MessageHistory")
        self.history.setView(rv)
        
    def getTitle(self):
        if self.getRecord():
            return "Chat con " + self.getRecord().ToUsers
        else:
            return "Chat"
    def buttonClicked(self, buttonname):
        ParentOOChatClientWindow.buttonClicked(self, buttonname)
        if buttonname=="send":
            self.send()
            
    def send(self):
        r = self.getRecord()
        ev = ChatMessageEvent([u.strip() for u in r.ToUsers.split(",") if u.strip()], r.Message)
        ev.post()
        self.addMessage(ev, False)
        r.Message=""
        self.getRecord().setFocusOnField("Message")
        
        
    def addMessage(self, ev, notifyUser=True):
        self.history.addHTML("<hr>" + ev.user +  " says: <br>")
        if ev.linkwindowname and ev.linkrecord:
            self.history.events.append(ev)
            self.history.startTable()
            self.history.startRow()
            self.history.addValue(ev.msg, CallMethod="openLink", Parameter=str(len(self.history.events)-1))
            self.history.endRow()
            self.history.endTable()
        else:
            self.history.addHTML(ev.msg)        
        self.history.render()
        self.history.getView().scrollToBottom()
        if notifyUser: beep()        
        
    def afterEdit(self, fieldname):
        if fieldname == "Message":
            if self.getRecord().Message:
                self.send()
                
    def sendWindowLink(self):
        r = self.getRecord()
        wl = getOpenWindowsList()
        opts = dict([(w.getTitle(), w) for w in wl])
        o = getSelection("Select Window", tuple(opts.keys()))
        if o:
            w = opts[o]
            msg = w.getTitle()
            ev = ChatMessageEvent([u.strip() for u in r.ToUsers.split(",") if u.strip()], msg)
            ev.linkwindowname = w.name()
            ev.linkrecord = cPickle.dumps(w.getRecord())
            ev.post()
            self.addMessage(ev, False)
            
                