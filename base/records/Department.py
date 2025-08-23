#encoding: utf-8
from OpenOrange import *

ParentDepartment = SuperClass("Department","Master",__file__)
class Department(ParentDepartment):
    buffer = RecordBuffer("Department")
    
    @classmethod
    def default(objclass):
        from OurSettings import OurSettings
        from User import User
        of = User.getDepartment(currentUser())
        if of: return of
        os = OurSettings.bring()
        return os.DefDepartment
