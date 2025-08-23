#encoding: utf-8
from OpenOrange import *

ParentPasswordChangeWindow = SuperClass("PasswordChangeWindow","SettingWindow",__file__)
class PasswordChangeWindow(ParentPasswordChangeWindow):

    def buttonClicked(self, buttonname):
        if buttonname == "Accept":
            self.accept()

    def accept(self):
        record = self.getRecord()
        op = record.OldPassword
        np = record.NewPassword
        np2 = record.NewPassword2
        
        if np != np2:
            message(tr("New Passwords do not match"))
            return
        from User import User
        user = User.bring(currentUser())
        if user:
            if op == user.Password or not user.Password:
                user.Password = np
                if user.save():
                    commit()
                    message(tr("Password successfully changed"))
                    self.close()
                else:
                    message(tr("Password has not been changed"))
            else:
                message(tr("Old password doesn't match"))