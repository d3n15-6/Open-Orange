#encoding: utf-8
# Mayo 2009 - Martin Salcedo
from OpenOrange import *

ParentAttachNoteWindow = SuperClass("AttachNoteWindow","AttachWindow",__file__)
class AttachNoteWindow(ParentAttachNoteWindow):

    def buttonClicked(self, buttonname):
        if (buttonname == "cancelNote"):
            self.close()
        elif (buttonname == "okNote"):
            record = self.getRecord()
            res = record.save()
            if (res):
                commit()
                record.refresh()
                orecord = record.getOriginRecord()
                if (orecord):
                    orecord.updateAttachFlag()
                    res = orecord.store()
                    if (not res):
                        message(res)
                    else:
                        commit()
                    self.close()
            if (hasattr(self,"ParentViewAttachReport")):
                self.ParentViewAttachReport.refresh()
                self.ParentViewAttachReport.source_record.refresh()