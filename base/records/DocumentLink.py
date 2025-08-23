#encoding: utf-8
from OpenOrange import *

ParentDocumentLink = SuperClass("DocumentLink", "Master", __file__)
class DocumentLink(ParentDocumentLink):
    buffer = RecordBuffer("DocumentLink", RecordBuffer.defaulttimeout, True)

    def pasteRecordName(self):
        from DocumentSpecFieldsRow import DocumentSpecFieldsRow
        last = 10
        recordobj = NewRecord(self.RecordName)
        for field in recordobj.fieldNames():
           FieldRow = DocumentSpecFieldsRow
           FieldRow.Name = field
           FieldRow.X = 100
           FieldRow.Y = last
           last += 20
           self.Fields.append(FieldRow)

    def getDocument(self,record, additional_varspace={}):
        if self.conditionsUsed():
            varspace = additional_varspace
            varspace["Record"] = record
            glf = record.getLinkedFields()
            rlinked = None
            for lf in glf:
                tmp = "rlinked = record.get%sRecord()" %(lf)
                #print tmp
                exec(tmp)
                try:
                    for fname in rlinked.fieldNames():
                        varspace["%s.%s" %(glf[lf],fname)] = rlinked.fields(fname).getValue()
                except Exception, err:
                    pass
                    #print str(err)
            for field in record.fieldNames():
                varspace[field] = record.fields(field).getValue()
            for srow in self.Specs:
               if srow.Conditions:
                   try:
                       cond = eval(srow.Conditions,varspace)
                   except Exception, e:
                       cond = False
                   if (cond):
                       return (srow.DocumentSpecCode, srow.ClassName)
        elif self.Specs.count()==1:
            return (self.Specs[0].DocumentSpecCode, self.Specs[0].ClassName)
        else:
            for row in self.Specs:
                if not row.Office or row.Office == record.Office:
                    return (row.DocumentSpecCode, row.ClassName)
        return (None, None)

    def conditionsUsed(self):
        for srow in self.Specs:
           if (srow.Conditions):
              return True
        return False

