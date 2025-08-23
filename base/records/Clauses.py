#encoding: utf-8
from OpenOrange import *

ParentClauses = SuperClass("Clauses","Master",__file__)
class Clauses(ParentClauses):

    def getfilledText(self, RecordObject, FieldDict=None):
        if (not FieldDict):
            FieldDict = {}
        for rfields in RecordObject.fieldNames():
            if isinstance(RecordObject.fields(rfields).getValue(), (float)): # Para que los numeros salgan con "," y dos decimales. 
                rec = str("%.2f" % RecordObject.fields(rfields).getValue()).replace(".",",")
            else:
                rec = RecordObject.fields(rfields).getValue()
            FieldDict[rfields] =  rec
        text = self.Text
        for rkey in FieldDict.keys():
            toreplace = "[%s]" %rkey
            replacing = str(FieldDict.get(rkey,toreplace))
            text = str(text).replace(toreplace,replacing)
        return text