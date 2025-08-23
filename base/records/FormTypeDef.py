#encoding: utf-8
from OpenOrange import *

ParentFormTypeDef = SuperClass('FormTypeDef', "Master", __file__)
class FormTypeDef(ParentFormTypeDef):
    buffer = RecordBuffer("FormTypeDef",RecordBuffer.defaulttimeout, True)
    
    @classmethod
    def getFormType(objclass, numerable, additional_varspace={}):
        ftd = FormTypeDef.bring(numerable.name())
        if (ftd):
            varspace = additional_varspace
            varspace["Record"] = numerable
            for frow in ftd.FormTypeDefRows:
                try:
                    cond = eval(frow.Condition,varspace)
                except Exception, e:
                    #return ErrorResponse("Form Type Definition Error: " + str(e))
                    cond = False
                if (cond):
                  return frow.FormType
        return None

