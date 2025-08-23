#encoding: utf-8
from OpenOrange import *

class globals:

  DayLetters = ("L", "M", "M", "J", "V", "S", "D")
  DayNames = (tr("Mon"), tr("Tue"), tr("Wed"), tr("Thu"), tr("Fri"), tr("Sat"), tr("Sun"))
  LongDayNames = (tr("Monday"), tr("Tuesday"), tr("Wednesday"), tr("Thursday"), tr("Friday"), tr("Saturday"), tr("Sunday"))
  LongMonthNames = (tr("Nothing")  ,tr("January") , tr("February") ,tr("March") ,tr("April") ,tr("May"),tr("June"),tr("July"),tr("August"),tr("September"),tr("October"),tr("November") ,tr("December"))
  MonthNames = (tr("Nothing")  ,tr("Jan") , tr("Feb") ,tr("Mar") ,tr("Apr") ,tr("May"),tr("Jun"),tr("Jul"),tr("Aug"),tr("Sep"),tr("Oct"),tr("Nov") ,tr("Dec"))

  OriginTypes = ["Asiento","Factura","Recibo","Caso","Recibo de Salario","Factura de compra","Pago","Salida de Caja","Liquidacion de Tarjetas","Entrada de Caja","Entrada de Mercaderia","Entrega de Mercaderia","Baja de Stock","Deposito de Cheque"]
  OriginRecords = ["NLT","Invoice","Receipt","Case","SalaryReceipt","PurchaseInvoice","Payment","CashOut","CouponCons","CashIn","GoodsReceipt","Delivery","StockDepreciation","Deposit"]