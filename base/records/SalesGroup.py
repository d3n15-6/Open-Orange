#encoding: utf-8
from OpenOrange import *

ParentSalesGroup = SuperClass("SalesGroup", "Master", __file__)
class SalesGroup(ParentSalesGroup):
    buffer = RecordBuffer("SalesGroup")
    
    def maxDiscountAllowed(self, itemcode, pricedeal):
        if self.Discounts.count() == 0: return 100
        itemgroup = None
        from Item import Item
        item = Item.bring(itemcode)
        if item: itemgroup = item.ItemGroup
        for disc in self.Discounts:
            if (not disc.ArtCode or disc.ArtCode == itemcode) and (not disc.ItemGroup or disc.ItemGroup == itemgroup) and (not disc.PriceDeal or disc.PriceDeal == pricedeal):
               return disc.MaxPercent
        return 100

ParentSalesGroupDiscount = SuperClass("SalesGroupDiscount","Record",__file__)
class SalesGroupDiscount(ParentSalesGroupDiscount):
    pass