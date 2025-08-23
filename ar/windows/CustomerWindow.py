#encoding: utf-8
from OpenOrange import *
import Validator

ParentCustomerWindow = SuperClass("CustomerWindow", "AddressableWindow", __file__)
class CustomerWindow(ParentCustomerWindow):


    def afterEdit(self, fieldname):
        ParentCustomerWindow.afterEdit(self, fieldname)
        customer = self.getRecord()
        if (fieldname == "TaxRegNr"):
            import re
            isString = re.search('[a-zA-Z]', customer.TaxRegNr)
            if (isString):
                #passport
                customer.IDType = 7
            else:
                if (customer.TaxRegNr != "" and  Validator.VATRegNrOK(customer.TaxRegNr,customer.Country)):
                    #CUIT
                    customer.IDType = 1
