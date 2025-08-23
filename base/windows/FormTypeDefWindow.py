#encoding: utf-8
from OpenOrange import *

ParentFormTypeDefWindow = SuperClass('FormTypeDefWindow', "MasterWindow", __file__)
class FormTypeDefWindow(ParentFormTypeDefWindow): 

    def fillPasteWindow(self, pastewindowname, fieldname):
        if pastewindowname == "XPasteWindow":
           query = []
           wininfo = getWindowsInfo()
           from Numerable import Numerable
           classes = Numerable.getChildrenClasses()
           for cls in classes:
                z = NewRecord("X")
                z.Code = cls.__name__
                try:
                    z.Name = wininfo[cls.__name__ + "Window"]["Title"]
                except:
                    z.Name = tr(cls.__name__)
                query.append(z)
           query.sort(key = lambda x: x.Name)
           return query
        return None
