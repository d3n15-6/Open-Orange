from OpenOrange import *

class RoutineWindow(Window):
    
    
    def start(self):
        if hasattr(self, "routine"):
            self.routine.start()