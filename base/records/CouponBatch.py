#encoding: utf-8
from OpenOrange import *

ParentCouponBatch = SuperClass("CouponBatch", "Record", __file__)
class CouponBatch(ParentCouponBatch):

    @classmethod
    def findOpenBatch(objclass, credcardtype, posnet=None):
        if not posnet:
            from LocalSettings import LocalSettings
            ls = LocalSettings.bring()
            posnet = ls.POSNet
        cb = CouponBatch()
        cb.CredCardType = credcardtype
        cb.POSNet = posnet
        cb.OpenFlag = True
        if cb.load():
            return cb.BatchNr
        return ErrorResponse("No hay Lote abierto para tarjetas %s y posnet %s" % (credcardtype, posnet))
    
    @classmethod
    def getNextCouponNr(objclass, credcardtype, batchnr):
        query = Query()
        query.sql = "SELECT MAX({CouponNr}) as {CouponNr} FROM [Coupon] WHERE {BatchNr} = i|%i| AND {CardType} = s|%s|" % (batchnr, credcardtype)
        if query.open() and query.count():
            return query[0].CouponNr + 1
        return 1

    
