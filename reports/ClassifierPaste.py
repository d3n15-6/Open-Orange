#encoding: utf-8
from OpenOrange import *
from Report import Report
import string
from LabelControl import LabelControl

class ClassifierPaste(Report):

    def getClassifiers(self):
        lc = LabelControl.bring(self.tableName)
        if (lc):
            dims = lc.LabelTypes.split(",")
            labs = {}
            query = Query()
            query.sql = "SELECT {Code}, {Name}, {Type} FROM [Label] "
            if query.open():
               for rec in query:
                  if (rec.Type in dims):
                      if not labs.has_key(rec.Type):
                          labs[rec.Type] = []
                      labs[rec.Type].append( (rec.Code,rec.Name) )
            return labs
        return {}

    def select(self,param,value):
        dim,lab = param.split(",")
        self.values[dim] = lab
        self.clear()
        self.run()
        self.render()

    def setinitialValues(self):
        self.values = {}
        for lab in self.record.Classification.split(","):
            for dim in self.classifiers.keys():
                labels = [ lb for (lb,labname) in self.classifiers[dim] ]
                if (lab in labels):
                    self.values[dim] = lab
                    continue
        #alert(self.values)

    def run(self):
        icons = ["<IMG SRC=images/orange.png>","<IMG SRC=images/nopriority.png>"]
        self.getView().resize(400,400)
        if (not self.__dict__.has_key("values")):
            from LabelType import LabelType
            self.labelTypes = LabelType.getNames()
            self.classifiers = self.getClassifiers()
            self.setinitialValues()
            initialvalues = self.record.Classification.split(",")
        self.printReportTitle(tr("Paste Classifier"))

        c = "White"
        self.startTable()
        for dim in self.classifiers.keys():
            self.startRow()
            self.addValue(self.labelTypes[dim],Color="White",BGColor="Gray")
            for (lab,labname) in self.classifiers[dim]:
                bcol = "#CC6600"
                if self.values.get(dim,"") == lab:
                   bcol = "orange"
                self.addValue(labname,CallMethod="select",Color=c,BGColor=bcol,Parameter="%s,%s" % (dim,lab) )
            self.endRow()
        self.row("")
        self.endTable()

        self.startTable()        
        self.startRow()
        self.addValue(tr("Paste"),Bold=True,CallMethod="paste")
        self.endRow()
        self.endTable()
        return

    def paste(self,value):
        self.record.Classification = ",".join(self.values.values())
        self.close()
