#encoding: utf-8
from OpenOrange import *


def resolve(a,b,f1,f2,direction):
    if f2:
      factor = (float(f1) / float(f2))
    else:
      factor = 0.0
    if (direction==1):
      if b:
        return (a / b) * factor
      else:
        return 0
    else:
      return (a * b) * factor

ParentCurrency = SuperClass("Currency","Master",__file__)
class Currency(ParentCurrency):
    buffer = RecordBuffer("Currency")

    def defaults(self):
        self.RoundOff =  2
        self.FrFactor = 1
        self.ToFactor = 1
        self.ConvertionBase = 0
        self.ConvertionDirection = 0

    def check(self):
        #return True
        return ParentCurrency.check(self)

    def convert(self,amount,curRate,baseRate):
        base1, base2 = Currency.getBases()
        b1 = Currency.bring(base1)
        b2 = Currency.bring(base2)
        invertDir = lambda a: abs(a-1)
        if (self.Code==base1):
            r1 = amount
            res = resolve(amount,baseRate,b2.ToFactor,b2.FrFactor,invertDir(b2.ConvertionDirection)) #invierto direccion
            r2 = res
        elif (self.Code==base2):
            r2 = amount
            res = resolve(amount,baseRate,b2.ToFactor,b2.FrFactor,b2.ConvertionDirection)
            r1 = res
        else:
            if (self.ConvertionBase==0):
              res = resolve(amount,curRate,self.ToFactor,self.FrFactor,self.ConvertionDirection)
              r1 = res  # i guess we should not round here!
              res = resolve(r1,baseRate,b1.ToFactor,b1.FrFactor,b1.ConvertionDirection)
              r2 = res
            else:
              res = resolve(amount,curRate,self.ToFactor,self.FrFactor,self.ConvertionDirection)
              r2 = res
              res = resolve(r2,baseRate,b2.ToFactor,b2.FrFactor,b2.ConvertionDirection)
              r1 = res
        return (r1,r2)

    def convertToBase(self,amount,curRate,baseRate,baseCurNr):
        (m1,m2) = self.convert(amount,curRate,baseRate)
        if (baseCurNr==0):
            return m1
        else:
            return m2

    @classmethod
    def convertTo(objclass,amount,curRate,baseRate,FromCurrency,ToCurrency,TransDate=None, TransTime=None, **kwargs):
        context = kwargs.get("context", "sales")
        if TransDate is None: TransDate = today()
        if TransTime  is None: TransTime = now()
        #curRate corresponde a la cotizacion de la moneda de origen (FromCurrency)
        invertDir = lambda a: abs(a-1)
        if (FromCurrency==ToCurrency):
            return amount
        else:
            fr = Currency.bring(FromCurrency)
            if (not fr):
                log( tr("Record not found!") + " " + FromCurrency )
            base1, base2 = Currency.getBases()
            (b1,b2) = fr.convert(amount,curRate,baseRate)
            if (ToCurrency==base1):
                return b1
            elif (ToCurrency==base2):
                return b2
            elif (FromCurrency==base1):
                tocur = Currency.bring(ToCurrency)
                from ExchangeRate import ExchangeRate
                exRate = ExchangeRate.getRate(ToCurrency, TransDate, TransTime)
                if context == "sales" or not exRate.SalesRate:
                    curRate = exRate.Value
                else: #purchase context"
                    curRate = exRate.SalesRate
                (t1,t2) = tocur.convert(1.0,curRate,baseRate)
                return (1.0/t1) * amount
            elif (FromCurrency==base2):
                tocur = Currency.bring(ToCurrency)
                (t1,t2) = tocur.convert(1.0,curRate,baseRate)
                return (1.0/t2) * amount
            else:
                # should be an error here!
                tc = Currency.bring(ToCurrency)
                if (tc):
                    from ExchangeRate import ExchangeRate
                    exRate = ExchangeRate.getRate(ToCurrency, TransDate, TransTime)
                    if context == "sales" or not exRate.SalesRate:
                        curRate2 = exRate.Value
                    else: #purchase context
                        curRate2 = exRate.SalesRate
                    if (tc.ConvertionBase==0):
                        res = resolve(b1,curRate2,tc.ToFactor,tc.FrFactor,abs(tc.ConvertionDirection-1))
                    else:
                        res = resolve(b2,curRate2,tc.ToFactor,tc.FrFactor,abs(tc.ConvertionDirection-1))
                    return res
                return amount

    @classmethod
    def convertUsingToRate(objclass,amount,curRate,baseRate,FromCurrency,ToCurrency,TransDate=None, TransTime=None, **kwargs):
        context = kwargs.get("context", "sales")
        if TransDate is None: TransDate = today()
        if TransTime  is None: TransTime = now()
        #like convertTo, but curRate corresponds to destination currency (ToCurrency)
        fr = Currency.bring(FromCurrency)
        if (FromCurrency==ToCurrency):
          return amount
        else:
            base1, base2 = Currency.getBases()
            if FromCurrency not in Currency.getBases():
                from ExchangeRate import ExchangeRate
                exRate = ExchangeRate.getRate(FromCurrency, TransDate, TransTime)
                if context == "sales" or not exRate.SalesRate:
                    curRate = exRate.Value
                else: #purchase context"
                    curRate = exRate.SalesRate
            return Currency.convertTo(amount,curRate,baseRate,FromCurrency,ToCurrency,TransDate, TransTime, **kwargs)

    @classmethod
    def ContextFreeConvertTo(objclass,amount,FromCurrency,ToCurrency,TransDate=None,TransTime=None):
        if not TransDate: TransDate = today()
        if not TransTime: TransTime = now()
        from ExchangeRate import ExchangeRate
        exRate = ExchangeRate.getRate(FromCurrency, TransDate,TransTime)
        curRate = exRate.Value
        bRate = ExchangeRate.getRate(Currency.getBase2(), TransDate,TransTime)
        baseRate = bRate.Value
        return Currency.convertTo(amount,curRate,baseRate,FromCurrency,ToCurrency,TransDate)

    @classmethod
    def default(objclass):
        return Currency.getBase1()

    @classmethod
    def getBase1(objclass):
        from OurSettings import OurSettings
        sets = OurSettings.bring()
        return sets.BaseCur1

    @classmethod
    def getBase2(objclass):
        from OurSettings import OurSettings
        sets = OurSettings.bring()
        return sets.BaseCur2

    @classmethod
    def getBases(objclass):
        from OurSettings import OurSettings
        sets = OurSettings.bring()
        return (sets.BaseCur1, sets.BaseCur2)

    @classmethod
    def getRoundOff(objclass,currencycode):
        currency = Currency.bring(currencycode)
        if currency:
            return currency.RoundOff
        return 0

    @classmethod
    def fillInDecimals(objclass,currency,num):
        # Converts 159.9 to 159.90, 159.92 to 159.92 and 159 to 159
        roundoff = Currency.getRoundOff(currency)
        if (roundoff==2):
            if isinstance(num,float):
                num = str(num)
                temp=num[(len(num)-2): len(num)]
                if (temp[0]==".") or (temp[0]==","):
                    num=num + "0"
            else:
                num = str(num) + ".00"
        return num

    @classmethod
    def processQueryResult(classobj, tocurrency, query, keyfields, sumfieldnames, currencyfn, currencyratefn, baseratefn, transdatefn, transtimefn):
        res = []
        lastkey = None
        lastrec = None
        r = None
        sumfields = []
        k = None
        rec = None
        #Los campos que comienzan con ! se suman sin convertir
        sumfieldtypes = {}
        sumfieldtypes.update([(fn.replace("!",""), bool(fn[0] == "!")) for fn in sumfieldnames])
        sumfieldnames = [fn.replace("!","") for fn in sumfieldnames]
        for rec in query:
            k = []
            for fn in keyfields: k.append(getattr(rec, fn))
            if k != lastkey:
                if lastrec is not None:
                    newrec = lastrec
                    for i in range(len(sumfieldnames)): setattr(newrec, sumfieldnames[i], sumfields[i])
                    res.append(newrec)
                sumfields = [0] * len(sumfieldnames)
                lastkey = k
            for i in range(len(sumfieldnames)):
                #def convertTo(objclass,amount,curRate,baseRate,FromCurrency,ToCurrency,TransDate=today(), TransTime=now()):
                if (sumfieldtypes[sumfieldnames[i]]):
                    sumfields[i] += getattr(rec, sumfieldnames[i])
                else:
                    sumfields[i] += Currency.convertTo(getattr(rec, sumfieldnames[i]), getattr(rec, currencyratefn), getattr(rec, baseratefn), getattr(rec, currencyfn), tocurrency, getattr(rec, transdatefn), getattr(rec, transtimefn))
            lastrec = rec
        if lastrec is not None:
            newrec = lastrec
            for i in range(len(sumfieldnames)): setattr(newrec, sumfieldnames[i], sumfields[i])
            res.append(newrec)
        return res
