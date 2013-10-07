from PyQt4 import QtCore

class Signals(QtCore.QObject):
    history_compact = QtCore.pyqtSignal(list)
    history_detailed = QtCore.pyqtSignal(list)
    upload_detailed_start = QtCore.pyqtSignal(list)
    upload_detailed_update = QtCore.pyqtSignal(list)
    
class Globals(object):
    def __init__(self):
        self.signals = Signals()
        
def get_globals(_singleton=Globals()):
    return _singleton