# encoding: utf-8
from OpenOrange import *
from Routine import Routine

class Update0011(Routine):
    Description = "Actualizacion de Cuenta de NC en Articulos, Grupos de Articulo y Manejo de Cuentas"
    UpdateResult = ""
    Persistent = True

    def routinelog(self, text):
        if (not self.UpdateResult):
            self.UpdateResult = text
        else:
            self.UpdateResult += "%s\n" %(text)

    def performUpdate(self):
        try:
            from ItemGroup import ItemGroup
            from Item import Item
            self.routinelog( "Actualizando Grupos de Articulos")

            query = Query()
            query.sql = "UPDATE [ItemGroup] [i] "
            query.sql += "SET  [i].{CredSalesAcc} =  [i].{SalesAcc} "
            query.sql += "WHERE  ( [i].{CredSalesAcc} = '' OR [i].{CredSalesAcc} IS NULL ) "
            query.sql += "AND  ( [i].{SalesAcc} <> '' OR [i].{SalesAcc} IS NOT NULL ) "

            res = query.execute()
            if res:
                self.routinelog( "Grupos de Articulos Actualizados")
                commit()
            else:
                self.routinelog( "Error al actualizar Grupos de Articulos %s"%res)
                rollback()
                
            self.routinelog( "Actualizando Grupos de Articulos")
            query = Query()
            query.sql = "UPDATE [Item] [i] "
            query.sql += "SET  [i].{CredSalesAcc} =  [i].{SalesAcc} "
            query.sql += "WHERE  ( [i].{CredSalesAcc} = '' OR [i].{CredSalesAcc} IS NULL ) "
            query.sql += "AND  ( [i].{SalesAcc} <> '' OR [i].{SalesAcc} IS NOT NULL ) "
            res = query.execute()
            if res:
                self.routinelog( "Articulos Actualizados")
                commit()
            else:
                self.routinelog( "Error al actualizar Articulos %s"%res)
                rollback()

            self.routinelog( "Actualizando Manejo de Cuentas")
            query = Query()
            query.sql = "UPDATE [AccountSettings] [i] "
            query.sql += "SET  [i].{CredSalesAcc} =  [i].{Sales1Acc} "
            query.sql += "WHERE  ( [i].{CredSalesAcc} = '' OR [i].{CredSalesAcc} IS NULL ) "
            query.sql += "AND  ( [i].{Sales1Acc} <> '' OR [i].{Sales1Acc} IS NOT NULL ) "
            res = query.execute()
            if res:
                self.routinelog( "Manejo de Cuentas Actualizados")
                commit()
            else:
                self.routinelog( "Error al actualizar Manejo de Cuentas %s"%res)
                rollback()

        except Exception, err:
            self.routinelog("Error %s" %(err))
            return False
        return True