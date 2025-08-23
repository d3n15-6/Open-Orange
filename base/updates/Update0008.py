# Agosto 2009 - Martin Salcedo
from OpenOrange import *

class Update0008(Routine):  
    Description = "Ajuste de Fila de Registro Transformación de Stock. Campo UnitCode por Unit "
    UpdateResult = "No Ejecutado\n"
    Persistent = True

    def performUpdate(self):
        self.UpdateResult = "Verificando CRM Settings\n"

        try:
            
            if (currentUserCanDo("CanSynchronizeRecords",False)):
                synchronizeRecord("StockTransformationItemInRow")
                synchronizeRecord("StockTransformationItemOutRow")

            uquery = Query()
            uquery.sql  = "UPDATE StockTransformationItemInRow STIr "
            uquery.sql += "SET STIr.Unit = STIr.UnitCode "

            res = uquery.execute()
            if (res):
                self.UpdateResult += "Fila In Actualizada \n"

            uquery = Query()
            uquery.sql  = "UPDATE StockTransformationItemOutRow STOr "
            uquery.sql += "SET STOr.Unit = STOr.UnitCode "

            res = uquery.execute()
            if (res):
                self.UpdateResult += "Fila Out Actualizada \n"
            commit()

        except Exception, err:
            self.UpdateResult += "Error %s \n" %(err)
            return False
        return True