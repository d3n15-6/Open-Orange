#encoding: utf-8
from OpenOrange import *

ParentAccessGroup = SuperClass("AccessGroup", "Master", __file__)
class AccessGroup(ParentAccessGroup):
    #visibility constants
    ALL_RECORDS = 0
    ONLY_OFFICE = 1
    ONLY_USER = 2
    ONLY_DEPARTMENT = 3
    
    buffer = RecordBuffer("AccessGroup")
    
    
    def defaults(self):
        ParentAccessGroup.defaults(self)
        self.ModulesAccessType = 1
        self.RecordsAccessType = 1
        self.ReportsAccessType = 1
        self.RoutinesAccessType = 1
        self.SettingsAccessType = 1
        self.CustomsAccessType = 1

    def canDo(self, actionname,default=True):
        for row in self.Customs:
            if row.Name == actionname:
                if row.Access == 0:
                    return True
                else:
                    return ErrorResponse("User is not authorized")
        return default

    def check_records(self):
        if not hasattr(self, "__records__"):
            if self.RecordsAccessType == 0:
                self.__records_access_type__ = 3 #denied
            else:
                self.__records_access_type__ = 0 #allowed
            self.__records__ = {}
            self.__records_visibility__ = {}
            for row in self.Records:
                if row.Name:
                    self.__records__[row.Name] = row.Access
                    self.__records_visibility__[row.Name] = row.Visibility

    def canOpenRecord(self, recordname):
        self.check_records()
        return (self.__records__.get(recordname, self.__records_access_type__) != 3)

    def getRecordVisibility(self, recordname):
        self.check_records()
        return self.__records_visibility__.get(recordname, AccessGroup.ALL_RECORDS)

    def check_modules(self):
        if not hasattr(self, "__modules__"):
            if self.RecordsAccessType == 0:
                self.__modules_access_type__ = 1 #denied
            else:
                self.__modules_access_type__ = 0 #allowed
            self.__modules__ = {}
            for row in self.Modules:
                if row.Name:
                    self.__modules__[row.Name] = row.Access
            
    def canViewModule(self, modulename):
        self.check_modules()
        return (self.__modules__.get(modulename, self.__modules_access_type__) != 1)

    @classmethod
    def getFunctionalities(objclass):
        #res = ParentAccessGroup.getFunctionalities(objclass)
        res = {}
        
        res["CanUnOKReceipt"] = None
        res["CanUnOKInvoice"] = None
        res["CanUnOKSalesOrder"] = None
        res["CanUnOKQuote"] = None
        res["CanUnOKDelivery"] = None
        res["CanUnOKGoodsReceipt"] = None
        res["CanUnOKStockDepreciation"] = None
        res["CanUnOKStockMovement"] = None
        res["CanUnOKPayment"] = None
        res["CanUnOKPurchaseInvoice"] = None
        res["CanUnOKPurchaseOrder"] = None
        res["CanUnOKSubscription"] = None
        
        res["CanChangeInvoiceUpdStockFlag"] = None

        res["CanSaveCustomerProspects"] = None
        res["CanSaveCustomers"] = None
        
        res["CanModifyCustomerPayTerm"] = None
        res["CanModifyCustomerDiscountDeal"] = None
        res["CanModifyGoodsReceipt"] = None
        res["CanModifyGoodsReceiptArtCode"] = None
        res["CanModifyGoodsReceiptQty"] = None
        res["CanModifyGoodsReceiptPos"] = None
        res["CanModifyGoodsReceiptStockDepo"] = None
        res["CanModifyAuthorizedPurchaseOrder"] = None
        res["CanModifyAuthorizedPurchaseOrderQty"] = None
        res["CanModifyGoodsReceiptComment"] = None
        res["CanModifyInvoicePrices"] = None
        res["CanModifyInvoiceVATCode"] = None
        res["CanModifyPurchaseOrderDiscount"] = None
        res["CanModifyPurchaseOrderPrice"] = None
        res["CanModifyQuoteArtNames"] = None
        res["CanModifyQuoteDueDate"] = None
        res["CanModifyQuotePayTerm"] = None
        res["CanModifyQuotePrices"] = None
        res["CanModifyQuotePrices"] = None
        res["CanModifyQuoteSalesMan"] = None
        res["CanModifyQuoteTransDate"] = None
        res["CanModifySalesOrderArtNames"] = None
        res["CanModifySalesOrderPayTerm"] = None
        res["CanModifySalesOrderPrices"] = None
        res["CanModifySalesOrderSalesMan"] = None
        res["CanModifySalesOrderTransDate"] = None
        res["CanModifySalesOrderVATCode"] = None
        
        res["CanAuthorizeInvoices"] = None
        res["CanAuthorizeAnyPurchaseOrder"] = None
        res["CanAuthorizePurchaseOrder"] = None
        res["CanAuthorizeSalesOrders"] = None
        
        res["CanPrintUnapprovedReceipt"] = None
        res["CanPrintUnapprovedInvoice"] = None
        res["CanPrintUnapprovedSalesOrder"] = None
        res["CanPrintUnapprovedQuote"] = None
        res["CanPrintUnapprovedDelivery"] = None
        res["CanPrintUnapprovedGoodsReceipt"] = None
        res["CanPrintUnapprovedGoodsDepreciation"] = None
        res["CanPrintUnapprovedStockMovement"] = None
        res["CanPrintUnapprovedPayment"] = None
        res["CanPrintUnapprovedPurchaseInvoice"] = None
        res["CanPrintUnapprovedPurchaseOrder"] = None
        res["CanTouchFolio"] = None
        # Des Invalidar Voucher de Restaurant.
        res["CanUnInvalidateOpperationBooking"] = None

        res["CanSynchronizeRecords"] = None

        
        return res
    
  
    
    