# Agosto 2009 - Martin Salcedo
from OpenOrange import *
from BankAccount import BankAccount

class Update0008(Routine):
    Description = "Creación de Cuentas Bancarias desde los datos de Clientes y Proveedores"
    UpdateResult = "No Ejecutado\n"
    Persistent = True

    def performUpdate(self):
        self.UpdateResult = "Actualizando Tablas\n"

        try:
            if (currentUserCanDo("CanSynchronizeRecords",False)):
                synchronizeRecord("BankAccount")

            fields = ["BankAccount", "BankBranch", "BnkAccRouteNr", "IBAN", "SWIFT", "Bank", "BankName"]
            cquery = Query()
            cquery.sql  = "SELECT Code, Name, TaxRegNr, %s " %(",".join(fields))
            cquery.sql += "FROM Customer "
            condlist = []
            for fname in fields:
                condlist.append("%s <> '' OR %s IS NOT NULL" %(fname,fname))
            cquery.sql += "WHERE?AND (%s) " %(" OR ".join(condlist))

            if (cquery.open()):
                for crow in cquery:
                    bacc = BankAccount()
                    bacc.defaults()
                    bacc.EntityType = bacc.CUSTOMER
                    bacc.BankAccNr = crow.BankAccount
                    bacc.BankBranch = crow.BankBranch
                    bacc.BnkAccRouteNr = crow.BnkAccRouteNr
                    bacc.IBAN = crow.IBAN
                    bacc.SWIFT = crow.SWIFT
                    bacc.Bank = crow.Bank
                    bacc.Entity = crow.Code
                    bacc.AccountHolder = crow.Name
                    bacc.DocNr = crow.TaxRegNr
                    dummy = crow.BankName
                    res = bacc.save()
                    if (not res): 
                        self.UpdateResult += "%s. %s\n" %("Error Creating Bank Account for Customer %s" %(crow.Code),res)
                        rollback()
                        return False
                    else:
                        self.UpdateResult += "Actualización a Clientes OK \n" 
                        commit()

            fields = ["Bank", "BankName", "BankAccNr", "BnkAccRouteNr", "BankAccType", "BankBranch","IBAN", "SWIFT"]
            cquery = Query()
            cquery.sql  = "SELECT Code, Name, TaxRegNr, %s " %(",".join(fields))
            cquery.sql += "FROM Supplier "
            condlist = []
            for fname in fields:
                condlist.append("%s <> '' OR %s IS NOT NULL" %(fname,fname))
            cquery.sql += "WHERE?AND (%s) " %(" OR ".join(condlist))
            
            if (cquery.open()):
                for crow in cquery:
                    bacc = BankAccount()
                    bacc.defaults()
                    bacc.EntityType = bacc.SUPPLIER
                    bacc.BankAccNr = crow.BankAccNr
                    bacc.Comment = crow.BankAccType
                    bacc.BankBranch = crow.BankBranch
                    bacc.BnkAccRouteNr = crow.BnkAccRouteNr
                    bacc.IBAN = crow.IBAN
                    bacc.SWIFT = crow.SWIFT
                    bacc.Bank = crow.Bank
                    bacc.Entity = crow.Code
                    bacc.AccountHolder = crow.Name
                    bacc.DocNr = crow.TaxRegNr
                    dummy = crow.BankName
                    res = bacc.save()
                    if (not res): 
                        self.UpdateResult += "%s %s\n" %("Error Creating Bank Account for Supplier %s" %(crow.Code),res)
                        rollback()
                        return False
                    else:
                        self.UpdateResult += "Actualización a Proveedores OK \n" 
                        commit()

        except Exception, err:
            self.UpdateResult += "Error %s \n" %(err)
            return False
        return True