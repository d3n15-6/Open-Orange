#encoding: utf-8
from OpenOrange import *

def formatValue(value,precision=2, thousep='.', decimalsep=','):
    from SystemSettings import SystemSettings
    ss = SystemSettings.bring()
    if (ss):
        if (ss.ThousandSep):
            thousep = ss.ThousandSep
        if (ss.DecimalSep):
            decimalsep = ss.DecimalSep
    value = ('%.*f' % (max(0, precision), value)).split('.')
    integer_part = value[0]
    if integer_part[0] == '-':
        sign = integer_part[0]
        integer_part = integer_part[1:]
    else:
        sign = ''
    if len(value) == 2:
        decimal_part = decimalsep + value[1]
    else:
        decimal_part = ''   
    integer_part = list(integer_part)
    c = len(integer_part)   
    while c > 3:
        c -= 3
        integer_part.insert(c, thousep)
    return sign + ''.join(integer_part) + decimal_part
    
def processString(s, objects):
    """ usage:
    
        c = NewRecord("Customer")
        c.load()
        i = NewRecord("Item")
        i.load()
        s = NewRecord("Supplier")
        s.load()
        s.prefix = "Provider"   

        t = 'Today is |today().strftime("%d/%m/%Y")|\nFirst Customer in the database is |Customer.Name|\nFirst Item in the database is |Item.Name|\nFirst Supplier in the database is |Provider.Name|'
        print processString(t, (c,i,s))
    """
    d = {}
    for obj in objects:
        if hasattr(obj, "prefix"):
            k = obj.prefix
        else:
            k = obj.__class__.__name__
            #print "class",k
        d[k] = obj
    
    def processExpression(expr):
        return str(eval(expr[1:-1], globals(), d))
    
    import re
    p = re.compile("\|([^\|]*)\|")
    it = p.finditer(s)
    delta = 0
    for mo in it:
        expr =  s[mo.start()-delta:mo.end()-delta]
        try:
            expr_replaced = str(eval(expr[1:-1], globals(), d))
        except:
            expr_replaced = "#Error!"
        s = s[:mo.start()-delta] + expr_replaced + s[mo.end()-delta:]
        delta += mo.end() - mo.start() - len(expr_replaced)
    res = s
    return res    

def wrapText(text, wraplimit):
    wraptext = text.split(" ")
    accum = ""
    lista = []
    for i in range(len(wraptext)):
        if len(accum + " ") < wraplimit:
            accum = accum + wraptext[i] + " "
            if (i+1) == len(wraptext):
                lista.append(accum)
        else:
            lista.append(accum)
            accum = wraptext[i] + " "
    return lista
