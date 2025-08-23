#encoding: utf-8
from OpenOrange import *
# encoding: utf-8
from OpenOrange import *
from Routine import Routine

class Update0012(Routine):
    Description = "Encriptacion de Password de Actualizacion Web en Opciones de Impuestos"
    UpdateResult = ""
    Persistent = True

    def routinelog(self, text):
        if (not self.UpdateResult):
            self.UpdateResult = text
        else:
            self.UpdateResult += "%s\n" %(text)

    def performUpdate(self):
        try:
            from TaxSettings import TaxSettings

            self.routinelog( "Encriptando Password de Actualizacion Web")
            ts = TaxSettings.bring()
            if ts and ts.IIBBTaxPass and not ts.IIBBTaxPassEncripted:
                ts.IIBBTaxPass = genPassword(ts.IIBBTaxPass)
                ts.IIBBTaxPassEncripted = True
                res = ts.store()
                if res:
                    self.routinelog( "Password de Actualizacion Web Encriptado en Opciones de Impuestos")
                    commit()
                else:
                    self.routinelog( "Error al encriptar Password de Actualizacion Web %s"%res)
                    rollback()

        except Exception, err:
            self.routinelog("Error %s" %(err))
            return False
        return True