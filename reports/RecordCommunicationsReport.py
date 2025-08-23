#encoding: utf-8
from OpenOrange import *
from Report import Report
import sys
import tempfile
import os

class RecordCommunicationsReport(Report):

    def run(self):
        if not hasattr(self, "notfirsttime"):
            self.getView().resize(500,400)
            self.notfirsttime = True
        specs = self.getRecord()
        q = Query()
        q.sql = "SELECT c.SerNr, c.Name, c.TransDate, c.TransTime, c.Person as Person, c.Message, p.Name as PersonName, p.LastName as PersonLastName, a.Value as Photo, a.Comment as PhotoFile "
        q.sql += "FROM RecordCommunication c "
        q.sql += "LEFT JOIN Person p ON p.Code = c.Person "
        q.sql += "LEFT JOIN Attach a ON a.OriginRecordName = s|Person| AND a.OriginId=p.Code AND a.Type=i|%s| " % Record.ATTACH_PHOTO
        q.sql += "WHERE?AND c.OriginRecord = %s AND c.OriginId = %s "
        q.sql += "ORDER BY c.TransDate desc, c.TransTime desc "
        q.setLimit(50)
        q.params = (specs.OriginRecord, specs.OriginId)
        q.open()
        self.startTable()
        self.startRow()
        self.addValue(tr("Communications for") +  " " + tr(specs.OriginRecord) + " " + specs.OriginId)
        self.endRow()
        self.endTable()        
        self.addHTML("<HR/>")
        self.startTable()
        self.startRow()
        self.addValue(tr("Post a new message"), CallMethod="add")
        self.endRow()
        self.endTable()
        self.addHTML("<HR/>")
        self.startTable()
        if not q.count():
            self.startRow()
            self.addValue(tr("No messages."))
            self.endRow()
        else:
            for r in q:
                self.startRow()
                self.addValue(r.TransDate)
                self.addValue(r.TransTime)
                if r.Photo:
                    imgname = "./images/attachtmp_%s" %(r.PhotoFile)
                    open(imgname,"wb").write(r.Photo)
                    self.addImage("attachtmp_%s" %r.PhotoFile)
                else:                
                    self.addValue("")
                if (r.PersonName or r.PersonLastName):
                    self.addValue(r.PersonName + " " + r.PersonLastName)
                else:
                    self.addValue(r.Name)
                self.addValue(r.Message)
                self.endRow()
        self.endTable()
        

    def add(self, value):
        s = getString("Message")
        if s:
            from RecordCommunication import RecordCommunication
            rc = RecordCommunication()
            rc.defaults()
            rc.Message = s
            rc.OriginRecord = self.getRecord().OriginRecord
            rc.OriginId = self.getRecord().OriginId
            res = rc.save()
            if not res: 
                message(res)
            else:
                commit()
                self.refresh()
            