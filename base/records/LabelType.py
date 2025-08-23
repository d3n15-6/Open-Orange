#encoding: utf-8
from OpenOrange import *

ParentLabelType = SuperClass("LabelType", "Master", __file__)
class LabelType(ParentLabelType):    
    buffer = RecordBuffer("LabelType")

    def getLabels(self):
        labs = []
        query = Query()
        query.sql = "SELECT {Code} FROM [Label] WHERE {Type} = s|%s| " % self.Code
        if query.open():
           for x in query:
              labs.append(x.Code)
        return labs