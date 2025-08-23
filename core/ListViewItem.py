from OpenOrange import *

__author__ = 'PDB'
    
class ListViewItem(Embedded_ListViewItem):
    
    def setText(self, texts):
        i = 0
        for text in texts:
            self.setColumnText(text, i)
            i += 1

    def getText(self):
        res = []
        for col in range(self.getListView().getColumnCount()):
            res.append(self.getColumnText(col))
        return res
        
    def clicked(self):
        pass
        