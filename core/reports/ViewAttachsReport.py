#encoding: utf-8
from OpenOrange import *
from Report import Report
import sys

class ViewAttachsReport(Report):

    def run(self):
        if not hasattr(self, "editing_files"):
            self.editing_files = {}
        if (not hasattr(self,"ImageFileList")):
            self.ImageFileList = []
        from Attach import Attach
        query = Query()
        query.sql = "SELECT {Comment}, {internalId}, {Type}, LENGTH({Value}) as Length, Value FROM [Attach]  "
        query.sql += "WHERE {OriginRecordName} = '%s' AND {OriginId} = '%s'" % (self.source_record.name(), self.source_record.getPortableId())
        self.printReportName("View Attachments")
        if query.open():
            self.startTable()
            if self.source_record.lock_nontoken_records():
                self.startRow()
                self.addValue("Synchronization Version: %s" %self.source_record.syncVersion)
                self.endRow()
            self.startHeaderRow()
            self.addValue(tr("Attach File"), CallMethod="attachFile")
            self.addValue(tr("Attach Note"), CallMethod="attachNote")
            self.endHeaderRow()
            self.endTable()

            for rline in query:
                if (rline.Type == Record.ATTACH_NOTE):
                    self.startTable()
                    self.startRow()
                    self.startCell()
                    self.addHTML("<TABLE>")
                    
                    self.startRow()
                    self.addValue(tr("Save"),Size=2,CallMethod="downloadAttachFile", Parameter=rline.internalId)
                    self.endRow()
                    self.startRow()
                    self.addValue(tr("Modify"),Size=2,CallMethod="editNote", Parameter=rline.internalId)
                    self.endRow()
                    self.startRow()
                    self.addValue(tr("Erase"),Size=2,CallMethod="deleteAttach", Parameter=rline.internalId)
                    self.endRow()

                    self.addHTML("</TABLE>")
                    self.endCell()

                    self.addValue("<BR><B>%s</B><BR>%s" %(rline.Comment,self.getAttachNote(rline.internalId)))
                    self.endRow()
                    self.endTable()
                else:
                    if (rline.Comment[-3:].lower() in ("png", "gif", "jpg", "bmp")):
                        import os
                        self.startTable()
                        self.startRow()

                        self.startCell()
                        self.addHTML("<TABLE>")

                        self.startRow()
                        self.addValue(tr("Save"),Size=2,CallMethod="downloadAttachFile", Parameter=rline.internalId)
                        self.endRow()
                        self.startRow()
                        self.addValue(tr("Erase"),Size=2,CallMethod="deleteAttach", Parameter=rline.internalId)
                        self.endRow()

                        self.addHTML("</TABLE>")
                        self.endCell()
                        iname = rline.Comment.replace(" ","_").encode("ascii","ignore")
                        imgname = "./images/attachtmp_%s" %(iname)
                        open(imgname,"wb").write(rline.Value)
                        self.addValue(rline.Comment)
                        self.addImage("attachtmp_%s" %(iname))
                        self.endRow()
                        self.endTable()
                        self.ImageFileList.append(imgname)
                    else:
                        self.startTable()
                        self.startRow()

                        self.startCell()
                        self.addHTML("<TABLE>")

                        self.startRow()
                        self.addValue(tr("Open File"),Size=2,CallMethod="openAttach", Parameter=rline.internalId)
                        self.endRow()
                        self.startRow()
                        self.addValue(tr("Save"),Size=2,CallMethod="downloadAttachFile", Parameter=rline.internalId)
                        self.endRow()
                        self.startRow()
                        self.addValue(tr("Erase"),Size=2,CallMethod="deleteAttach", Parameter=rline.internalId)
                        self.endRow()

                        self.addHTML("</TABLE>")
                        self.endCell()
                        self.addValue(rline.Comment)

                        self.endRow()
                        self.endTable()
        self.check_editing_files()

    def openAttach(self, param, value):
        query = Query()
        query.sql = "SELECT {Comment}, {Value}, {Type} FROM [Attach] WHERE {internalId} = i|%s|" % param
        if query.open() and query.count():
            if query[0].Type != Record.ATTACH_NOTE:
                import tempfile
                import os
                tmp_fd, tmp_name = tempfile.mkstemp(suffix="_"+ query[0].Comment)
                f = os.fdopen(tmp_fd, 'w+b')
                f.write(query[0].Value)
                f.close()
                import os
                if not sys.platform.startswith("win"):
                    openFile(tmp_name)
                    if (sys.platform.startswith("darwin")):
                        message("Funcion no disponible en MAC o Linux. Pruebe con save as.")
                else:
                    os.startfile(tmp_name)
                    self.setAutoRefresh(1500)
                    self.editing_files[int(param)] = {"InternalId": int(param), "Comment": query[0].Comment, "FileName": tmp_name, "Modified": os.path.getmtime(tmp_name)}

    def downloadAttachFile(self, param, value):
        query = Query()
        query.sql = "SELECT {Comment}, {Value} FROM [Attach] WHERE {internalId} = i|%s|" % param
        if query.open() and query.count():
            if query[0].Comment:
                filename = getSaveFileName(tr("Save As"), DefaultFileName = query[0].Comment)
            else:
                filename = getSaveFileName(tr("Save As"))
            if filename:
                open(filename,"wb").write(query[0].Value)

    def deleteAttach(self, param, value):   #OK
        if askYesNo(tr("Are You sure?")):
            res = self.source_record.deleteAttach(param)
            if (res):
                commit()
                self.refresh()
            else:
                message(tr("Attachment was not deleted"))

    def getImage(self, internalid):
        query = Query()
        query.sql = "SELECT {Value} FROM [Attach] WHERE {internalId} = i|%i|" % internalid
        if query.open() and query.count():
            from ReportTools import Image
            from StringIO import StringIO
            strio = StringIO(query[0].Value)
            img = Image.open(strio)
            return img

    def genImage(self):
        query = Query()
        query.sql = "SELECT {Value} FROM [Attach] WHERE {internalId} = i|%i|" % internalid
        if query.open() and query.count():
            import tempfile
            import os
            tmp_fd, tmp_name = tempfile.mkstemp(suffix="_"+ query[0].Comment)
            f = os.fdopen(tmp_fd, 'w+b')
            f.write(query[0].Value)
            f.close()

    def getAttachNote(self, internalid):
        query = Query()
        query.sql = "SELECT {Value} FROM [Attach] WHERE {internalId} = i|%i|" % internalid
        if query.open() and query.count():
            return query[0].Value.decode("latin1")

    def attachFile(self, value):        #OK
        filename = getOpenFileName(tr("Select File"))
        if filename:
            res = self.source_record.attachFile(filename)
            if not res: message(tr("Attach failed"))
            commit()
            self.source_record.refresh()
            self.refresh()

    def editNote(self, param, value):   #OK
        from Attach import Attach
        atch = Attach()
        atch.internalId = param
        if (atch.load()):
            from AttachNoteWindow import AttachNoteWindow
            awin = AttachNoteWindow()
            awin.ParentViewAttachReport = self
            awin.setRecord(atch)
            awin.open()

    def attachNote(self, value):        #OK
        from AttachNoteWindow import AttachNoteWindow
        from Attach import Attach
        atch = Attach()
        atch.defaults()
        atch.OriginRecordName = self.source_record.name()
        atch.OriginId = self.source_record.getPortableId()
        anw = AttachNoteWindow()
        anw.setRecord(atch)
        anw.ParentViewAttachReport = self
        anw.open()

    def beforeClose(self):
        if (hasattr(self,"ImageFileList")):
            import os
            for fline in self.ImageFileList:
                try:
                    os.remove(fline)
                except:
                    pass
        return True

    def check_editing_files(self):
        import os
        for internalid in self.editing_files:
            ef = self.editing_files[internalid]
            modif_time = os.path.getmtime(ef["FileName"])
            if  modif_time != ef["Modified"]:
                ef["Modified"] = os.path.getmtime(ef["FileName"])
                if askYesNo("El archivo %s ha sido modificado localmente, desea actualizar el adjunto con las nuevas modificaciones?" % ef["Comment"]):
                    from Attach import Attach
                    attach = Attach()
                    attach.internalId = ef["InternalId"]
                    if attach.load():
                        f = open(ef["FileName"], "rb")
                        attach.Value = f.read()
                        if not attach.store():
                            message("The attachment could not be modified!")

