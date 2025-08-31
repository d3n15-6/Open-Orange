#encoding: utf-8
from OpenOrange import *
from Report import Report

TranslateEditor = {"text":"s","value":"v", "date":"d", "integer":"i", "time":"t", "combobox":"i"}
class ListWindowReport(Report):

    def run(self):
        if not hasattr(self, "first_run_done"):
            self.declareRecordFields(self.lwinfo["RecordName"],[fn["FieldName"] for fn in self.lwinfo["Columns"]])
            self.first_run_done = True
        self.startTable()
        self.header(self.lwinfo["Title"])
        self.endTable()
        if not self.__dict__.has_key("firstrec"):
            self.can_delete = False
            self.firstrec = 0
            self.getView().resize(600,480)
        if not self.__dict__.has_key("lastwhere"): self.lastwhere = ""
        if not self.__dict__.has_key("combos"): self.combos = {}
        self.recsPerPage = 20
        spec = self.getRecord()
        self.startTable()
        self.startRow()
        query = Query()
        columns = self.lwinfo["Columns"]
        fieldnames = "{internalId}"
        for col in columns:
            fieldnames += ",{%s}" % (col["FieldName"])

        self.startRow()
        self.addValue("[Crear]", CallMethod="createRecord")
        if not self. can_delete: self.addValue("[Habilitar Borrado]", CallMethod="enableDeleting", Wrap=False)
        self.addValue("[Limpiar Filtros]", CallMethod="clearFilters")
        self.endRow()

        self.startHeaderRow()
        if self. can_delete: self.addValue("Quitar", CallMethod="disableDeleting")
        where = ""
        for col in columns:
            #self.addValue(col["Label"])
            fn = col["FieldName"]
            val = spec.fields(fn).getValue()
            if not spec.fields(fn).isNone():
                editor = col["Editor"]
                if editor in ("text","memo"):
                    where += " WHERE?AND {%s} LIKE %s|%s| " % (col["FieldName"], TranslateEditor[editor], "%"+str(val)+"%")
                else:
                    where += " WHERE?AND {%s} = %s|%s| " % (col["FieldName"], TranslateEditor[editor], val)

        if self.recinfo["Fields"].has_key("Office"):
            from AccessGroup import AccessGroup
            from User import User
            if User.getCurrentRecordVisibility(self.recinfo["TableName"]) == AccessGroup.ONLY_OFFICE:
                office = User.getOffice(currentUser())
                if office:
                    where += " WHERE?AND {Office} = s|%s| " % (office)
        elif self.recinfo["Fields"].has_key("User"):
            from AccessGroup import AccessGroup
            from User import User
            if User.getCurrentRecordVisibility(self.recinfo["TableName"]) == AccessGroup.ONLY_USER:
                where += " WHERE?AND {User} = s|%s| " % (user)
        self.publishTitles()
        self.endHeaderRow()

        if where != self.lastwhere:
            self.firstrec = 0
            self.lastwhere = where

        query.sql = "SELECT %s FROM [%s] %s " % (fieldnames, self.recinfo["TableName"], where)
        query.setLimit(int(self.recsPerPage), int(self.firstrec) )
        self.recsInPage = 0
        query.setResultClass(NewRecord(self.lwinfo["RecordName"]).__class__)
        if query.open():
            lineColors = ("#BCCABC","#FBEEED","#33BBAA")
            delcolor=2
            idcolor = 0
            v = None
            for rec in query:
                self.startRow()
                if self. can_delete: self.addValue("eliminar", CallMethod="deleteRecord", Parameter=str(rec.internalId), BGColor=lineColors[delcolor], Wrap=False)
                """
                for col in columns:
                    if self.combos.has_key(col["FieldName"]):
                        v = self.combos[col["FieldName"]].get(str(rec.fields(col["FieldName"]).getValue()),"")
                    else:
                        v = rec.fields(col["FieldName"]).getValue()
                    self.addValue(v, CallMethod="openRecord", Parameter=str(rec.internalId), BGColor=lineColors[idcolor], Wrap=False)
                """
                self.publishFields(rec)
                #self.addValue("[Copiar]", CallMethod="copyRecord", Parameter=str(rec.internalId))
                #self.addValue("[Borrar]", CallMethod="deleteRecord", Parameter=str(rec.internalId))
                idcolor = not idcolor
                self.recsInPage += 1

                self.endRow()
        self.endTable()

        self.showCursors()

    def showCursors(self):
        self.startTable()
        self.startRow()
        if self.firstrec > 0:
            self.addValue("[Primera]", CallMethod="firstPage")
            self.addValue("[Anterior]", CallMethod="prevPage")
        else:
            self.addValue("[Primera]", FGColor="gray")
            self.addValue("[Anterior]", FGColor="gray")
        if self.recsInPage == self.recsPerPage:
            self.addValue("[Siguiente]", CallMethod="nextPage")
            self.addValue("[Ultima]", CallMethod="lastPage")
        else:
            self.addValue("[Siguiente]", FGColor="gray")
            self.addValue("[Ultima]", FGColor="gray")
        self.endRow()
        self.endTable()

    def firstPage(self, value):
        self.firstrec = 0
        self.clear()
        self.run()
        self.render()

    def lastPage(self, value):
        qry = Query()
        qry.sql = "SELECT COUNT(*) as NumRecs FROM %s" % self.recinfo["TableName"]
        if qry.open():
            if qry.count() > 0:
                self.firstrec = qry[0].NumRecs - self.recsPerPage + 1
                if self.firstrec < 0: self.firstrec = 0
        self.clear()
        self.run()
        self.render()

    def prevPage(self, value):
        self.firstrec -= self.recsPerPage
        if self.firstrec < 0: self.firstrec = 0
        self.clear()
        self.run()
        self.render()

    def nextPage(self, value):
        self.firstrec += self.recsInPage
        self.clear()
        self.run()
        self.render()

    def disableDeleting(self, value):
        self.can_delete = False
        self.clear()
        self.run()
        self.render()

    def enableDeleting(self, value):
        self.can_delete = True
        self.clear()
        self.run()
        self.render()

    def openRecord(self, internalid, value):
        record = NewRecord(self.recinfo["Name"])
        record.internalId = int(internalid)
        if record.load():
            window = NewWindow(self.lwinfo["WindowName"])
            window.setRecord(record)
            window.open()

    def deleteRecord(self, internalid, value):
        record = NewRecord(self.recinfo["Name"])
        record.internalId = int(internalid)
        if record.load():
            record.delete()
            commit()
            self.clear()
            self.run()
            self.render()

    def copyRecord(self, internalid, value):
        pass

    def createRecord(self, value):
        record = NewRecord(self.recinfo["Name"])
        record.defaults()
        window = NewWindow(self.lwinfo["WindowName"])
        window.setRecord(record)
        window.open()

    def clearFilters(self, value):
        record = self.getRecord()
        for fn in record.fieldNames():
            record.fields(fn).setValue(None)

    def getUserInputDef(self, param):
        self.combos = {}
        self.lwinfo = getListWindowsInfo()[param]
        self.recinfo = getRecordsInfo()[self.lwinfo["RecordName"]]
        fieldsStr=""
        fields = self.recinfo["Fields"]
        columns = self.lwinfo["Columns"];
        for col in columns:
            fn = col["FieldName"]
            fieldsStr += "<field name=\"%s\" type=\"%s\" length=\"%i\"/>\n" % (fn, fields[fn]["Type"], fields[fn]["Length"])
            #fieldsStr += "<field name=\"_check_%s\" type=\"boolean\"/>\n" % fn

        columnsStr=""
        for col in columns:
            columnsStr += "<line>\n"
            if col["Editor"] != "combobox":
                columnsStr += "<%s fieldname=\"%s\" label=\"%s\"/>\n" % (col["Editor"], col["FieldName"], col["Label"])
            else:
                columnsStr += "<combobox fieldname=\"%s\" label=\"%s\">\n" % (col["FieldName"], col["Label"])
                combo = {}
                for opt in col["Options"]:
                    columnsStr += "  <combooption value=\"%s\" label=\"%s\"/>\n" % (opt["Value"], opt["Label"])
                    combo[opt["Value"]] = opt["Label"]
                columnsStr += "</combobox>\n"
                self.combos[col["FieldName"]] = combo
            #columnsStr += "<checkbox fieldname=\"_check_%s\" label=\"\"/>\n" % (col["FieldName"])
            columnsStr += "</line>\n"

        res = """
        <reportuserinput>
            <reportrecord>%s</reportrecord>
            <reportwindow name="%s" title="%s">%s</reportwindow>
        </reportuserinput>
        """ % (fieldsStr, param, self.lwinfo["Title"], columnsStr)
        return res