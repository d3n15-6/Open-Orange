#encoding: utf-8
from OpenOrange import *

ParentLoginDialogWindow = SuperClass("LoginDialogWindow","Window",__file__)
class LoginDialogWindow(ParentLoginDialogWindow):

    def __init__(self):
        ParentLoginDialogWindow.__init__(self)
        self.OKClicked = False
        self.accepted = None
        self.rejected = None

    def afterShowRecord_fromC(self):
        pass
    
    def call_beforeEdit(self, fieldname):
        return True

    def call_afterEdit(self, fieldname):
        pass

    def call_keyPressed(self, key, state):
        pass

    def call_beforeClose(self):        
        return True

    def call_windowResized(self):
        pass
        
    def call_buttonClicked(self, buttonname):
        if buttonname == "login":
            self.close()
            if self.accepted: self.accepted(self.getRecord())
        else:
            self.close()
            if self.rejected: self.rejected(self.getRecord())
            
        
