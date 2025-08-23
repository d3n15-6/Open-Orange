#encoding: utf-8
from OpenOrange import *

ParentCustomer = SuperClass("Customer", "Addressable", __file__)
class Customer(ParentCustomer):
    IIBBLOCAL = 0
    IIBBCONVENIO = 1
    IIBBEXENTO = 2

    TAXREGTYPE_RESP = 0
    TAXREGTYPE_CONSFINAL = 1
    TAXREGTYPE_IVANORESP = 2
    TAXREGTYPE_EXENTO = 3
    TAXREGTYPE_MONO = 5
    TAXREGTYPE_EXENTOEXT = 6

    DOCTYPEA = 0
    DOCTYPEB = 1
    DOCTYPEC = 2
    DOCTYPEE = 3
    
    IDTYPE_NONE = 0
    IDTYPE_CUIT = 1
    IDTYPE_DNI = 2
    IDTYPE_POLICEID = 3
    IDTYPE_CUIL = 4
    IDTYPE_LC = 5
    IDTYPE_LE = 6
    IDTYPE_PASSPORT = 7


    def check(self):
        result = ParentCustomer.check(self)
        if not result: return result
        result = self.checkTaxRegType()
        if not result: return result
        from OurSettings import OurSettings
        os = OurSettings.bring()
        if (os.Country=="ar" and self.Country=="ar"):
            if (self.fields("TaxReg2Type").isNone()):
                return self.FieldErrorResponse("Especifique una condicion de ingresos brutos", "TaxReg2Type")                # can stay in spanish
            if ((self.TaxReg2Type == 0) and (not self.fields("TaxReg2Type").isNone()) and (not self.TaxReg2Province)):
                return self.FieldErrorResponse("Falta provincia inscripcion Ingresos Brutos", "TaxReg2Province")
        return result

    def checkTaxRegType(self):

        ##FAC A: el sistema debe chequear que el tipo de documento sea CUIT y el tipo de inscripcion responsable inscripto.
        #cond1 = (self.DocType == self.DOCTYPEA and self.IDType == self.IDTYPE_CUIT and self.TaxRegType == self.TAXREGTYPE_RESP)
        ##En caso de Monotributista, el tipo de factura debe ser B y el tipo de documento un CUIT.
        #cond2 = (self.DocType == self.DOCTYPEB and self.IDType == self.IDTYPE_CUIT and self.TaxRegType == self.TAXREGTYPE_MONO)
        #if (tset.TaxRegType == self.TAXREGTYPE_EXENTO):
        #    #En caso de un Consumidor final, se puede tener cualquier tipo de documento, pero solo facturas de Tipo C.
        #    cond3 = (self.DocType == self.DOCTYPEC and self.TaxRegType == self.TAXREGTYPE_CONSFINAL)
        #else:
        #    #En caso de un Consumidor final, se puede tener cualquier tipo de documento, pero solo facturas de Tipo B.
        #    cond3 = (self.DocType == self.DOCTYPEB and self.TaxRegType == self.TAXREGTYPE_CONSFINAL)
        ##Para clientes exentos, el tipo de factura debe ser B, teniendo en cuenta que deben tener un Nro de CUIT y dicho tipo de documento.
        #cond4 = (self.DocType == self.DOCTYPEB and self.IDType == self.IDTYPE_CUIT and self.TaxRegType == self.TAXREGTYPE_EXENTO)
        ##Para Exento Exterior, tipo de documento Pasaporte o CUIT, tipo de fact B o E
        #cond5 = ((self.DocType == self.DOCTYPEB or self.DocType == self.DOCTYPEE) 
        #         (self.IDType == self.IDTYPE_CUIT or self.IDType == self.IDTYPE_PASSPORT) and self.TaxRegType == self.TAXREGTYPE_EXENTOEXT)

        # -1 (indica cualquiera)
        #La clave es para los tipos de inscripción y la lista son tuplas para la combinación posible.
        #Consumidor Final tiene dos combinaciones posibles

        import Validator
        from TaxSettings import TaxSettings
        tset = TaxSettings.bring()
        CheckRules = {}
        CheckRules[self.TAXREGTYPE_RESP]        = [[self.DOCTYPEB],[self.IDTYPE_CUIT]]
        CheckRules[self.TAXREGTYPE_MONO]        = [[self.DOCTYPEB],[self.IDTYPE_CUIT]]
        CheckRules[self.TAXREGTYPE_EXENTO]      = [[self.DOCTYPEB],[self.IDTYPE_CUIT]]
        CheckRules[self.TAXREGTYPE_CONSFINAL]   = [[self.DOCTYPEB],[-1]]
        if (tset.TaxRegType in (self.TAXREGTYPE_MONO,self.TAXREGTYPE_EXENTO)):
            CheckRules[self.TAXREGTYPE_RESP]        = [[self.DOCTYPEC],[self.IDTYPE_CUIT]]
            CheckRules[self.TAXREGTYPE_MONO]        = [[self.DOCTYPEC],[self.IDTYPE_CUIT]]
            CheckRules[self.TAXREGTYPE_EXENTO]      = [[self.DOCTYPEC],[self.IDTYPE_CUIT]]
            CheckRules[self.TAXREGTYPE_CONSFINAL]   = [[self.DOCTYPEC],[-1]]
        elif (tset.TaxRegType == self.TAXREGTYPE_RESP):
            CheckRules[self.TAXREGTYPE_RESP]        = [[self.DOCTYPEA],[self.IDTYPE_CUIT]]
        CheckRules[self.TAXREGTYPE_EXENTOEXT]   = [[self.DOCTYPEB,self.DOCTYPEE],[self.IDTYPE_PASSPORT,self.IDTYPE_CUIT]]

        doctypes = CheckRules[self.TaxRegType][0]
        idtypes = CheckRules[self.TaxRegType][1]
        error = False
        if (not ((-1 in doctypes) or self.DocType in doctypes )):
            error = True
        if (not error):
            if (not ((-1 in idtypes) or self.IDType in idtypes )):
                error = True
        if (error):
            return ErrorResponse("Tipo de Documento, Tipo de Factura e Inscripcion incompatibles")
        if (self.IDType == self.IDTYPE_CUIT and not Validator.VATRegNrOK(self.TaxRegNr,"ar")):
            return ErrorResponse(tr("WRONGTAXREGNR"))
        return True