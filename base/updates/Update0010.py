# Agosto 2009 - Martin Salcedo
from OpenOrange import *
from Routine import Routine

class Update0010(Routine):

    Description = "Corrección de Seteos de Códigos de Telefonos en Opciones de CRM y Paises"
    UpdateResult = ""
    Persistent = True

    def routinelog(self, text):
        if (not self.UpdateResult):
            self.UpdateResult = text
        else:
            self.UpdateResult += "%s\n" %(text)

    def performUpdate(self):
        self.Description = "Corrección de configuración de Cod. de Acceso Internacional de Telefonos de Paises"

        self.routinelog("Ajustando Settings")
        try:
            from CRMSettings import CRMSettings
            crmset = CRMSettings.bring()
            crmset.CountryPhoneCode = crmset.IntAccessCode
            res = crmset.save()
            if (res):
                self.routinelog("CRM Settings Fixed")
                commit()
            else:
                self.routinelog("Error Saving CRM Settings")
                self.routinelog(res)
                rollback()

            cquery = Query()
            cquery.sql  = "UPDATE Country "
            cquery.sql += "SET CountryPhoneCode = IntAccessCode "
            cquery.sql += "WHERE (IntAccessCode IS NOT NULL OR IntAccessCode <> '') "
            
            res =  cquery.execute()
            if (res):
                self.routinelog("Countries Fixed")
                commit()
            else:
                self.routinelog("Error Fixing Countries")
                self.routinelog(res)
                rollback()
            self.routinelog("Updating End")

        except Exception, err:
            self.routinelog("Error %s \n" %(err))
            return False
        return True