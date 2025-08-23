#coding:utf-8
from OpenOrange import *

ParentWindowState = SuperClass("WindowState","Record",__file__)
class WindowState(ParentWindowState):
    buffer = RecordBuffer("WindowState")
    
    def uniqueKey(self):
        return ('User', 'WindowName')
    
    def getPortableId(self, useOldFields=False):
        user = self.User
        windowname = self.WindowName
        if useOldFields: 
            user = self.oldFields('User').getValue()
            windowname = self.oldFields('WindowName').getValue()
        return str("%s|%s" % (user,windowname))
    
    def setPortableId(self, id):
        self.User, self.WindowName  = id.split('|')
    
    @classmethod
    def bring(classobj, user, windowname):
        uniquekey = "%s|%s" % (user, windowname)
        try:
            return classobj.buffer[uniquekey]
        except:
            p = classobj()
            p.User = user
            p.WindowName = windowname
            if p.load():
                classobj.buffer[uniquekey] = p
                return p
            classobj.buffer[uniquekey] = None
