from OpenOrange import *

class ReportWindow(Window):
    
    def replaceAccountsShortCut(self):
        from Account import Account
        record = self.getRecord()
        rngs = filter(lambda x: bool(x), record.Account.split(","))
        x_rngs = []
        for rng in rngs:
            accs = filter(lambda x: bool(x), rng.split(":"))
            x_accs = []
            for acc in accs:
                account = Account.bring(acc)
                if account and account.Code != acc: acc = account.Code
                x_accs.append(acc)
            x_rngs.append(":".join(x_accs))
        record.Account = ",".join(x_rngs)

    def afterEdit(self, fieldname):
        Window.afterEdit(self, fieldname)
        if fieldname == "Account":
            record = self.getRecord()
            if record.Account and not (record.Account.strip().endswith(":") or record.Account.strip().endswith(",")):
                self.replaceAccountsShortCut()
