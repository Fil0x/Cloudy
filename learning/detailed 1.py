import os
import operator
from PyQt4 import QtCore, QtGui, Qt

class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, header, data=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)

        #Hax
        self.data = [['']*(len(header)+1)] if not data else data
        self.header = header
        self.hidden_col = len(header)

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.data[0]) if len(self.data) else 0

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != Qt.Qt.DisplayRole:
            return QtCore.QVariant()
        return QtCore.QVariant(self.data[index.row()][index.column()])

    def headerData(self, col, orientation, role):
        if col != self.hidden_col and orientation == Qt.Qt.Horizontal and role == Qt.Qt.DisplayRole:
            return QtCore.QVariant(self.header[col])
        return QtCore.QVariant()

    def sort(self, Ncol, order):
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.data = sorted(self.data, key=operator.itemgetter(Ncol))
        if order == Qt.Qt.DescendingOrder:
            self.data.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))
        
    def add_item(self, item):
        self.beginInsertRows(QtCore.QModelIndex(), len(self.data), len(self.data))
        self.data.append(item)
        self.endInsertRows()
        
    def remove(self, id, index=None):
        i = 0
        if index:
            i = index
        else:
            i = zip(*self.data)[-1].index(id)
        self.beginRemoveRows(QtCore.QModelIndex(), i, i)
        self.data = self.data[0:i] + self.data[i+1:]
        self.endRemoveRows()
        
    def remove_all(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self.data) - 1)
        del self.data[:]
        self.endRemoveRows()
        
class BaseDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, device, font, color, images=None):
        QtGui.QStyledItemDelegate.__init__(self, device)

        self.font = font
        self.images = images
        self.brush = QtGui.QBrush(color)
        
    def createEditor(self, parent, option, index):
        return None
        
class UploadTableDelegate(BaseDelegate):
        
    def paint(self, painter, option, index):
        painter.save()
        model = index.model()
        d = model.data[index.row()][index.column()]
        
        if index.row() % 2:
            painter.fillRect(option.rect, self.brush)
        
        painter.translate(option.rect.topLeft())
        painter.setFont(self.font)
        #painter.drawImage(QtCore.QPoint(5, 5), self.images[0])
        painter.drawText(QtCore.QPoint(40, 20), d)
        '''
        painter.setPen(self.date_color)
        painter.drawText(QtCore.QPoint(40, 30), str(d[3]))
        if option.state & QtGui.QStyle.State_MouseOver:
            painter.drawImage(self.sharelink_pos, self.sharelink_img)
        '''
        painter.restore()

    def editorEvent(self, event, model, option, index):
        '''sharelink_rect = self.sharelink_img.rect().translated(self.sharelink_pos.x(),
                                                option.rect.top() + self.sharelink_pos.y())
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if sharelink_rect.contains(event.pos()):
                model = index.model()
                link = model.data[index.row()][2]
                import webbrowser
                webbrowser.open(link)'''

        return False

    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[index.row()]
        return QtCore.QSize(100, 40)

class DetailedWindow(QtGui.QMainWindow):
    #http://www.jankoatwarpspeed.com/ultimate-guide-to-table-ui-patterns/
    
    font = QtGui.QFont('Tahoma', 10)
    addBtnPath = r'images/detailed-add.png'
    playBtnPath = r'images/detailed-play.png'
    stopBtnPath = r'images/detailed-stop.png'
    file_icon_path = r'images/detailed-doc.png'
    removeBtnPath = r'images/detailed-remove.png'
    settingsBtnPath = r'images/detailed-configure.png'
    tableBackgroundPath = r'images/detailed-background.jpg'
    windowStyle = r'QMainWindow {background-color: rgba(108, 149, 218, 100%)}'

    def __init__(self, title):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle(title)
        #self.setVisible(False)
        self.setStyleSheet(self.windowStyle)
        
        file_image = QtGui.QImage(self.file_icon_path)
        c = QtGui.QColor('#E5FFFF')
        
        self.history_header = ['Name', 'Destination', 'Service', 'Date']
        self.uploads_header = ['Name', 'Progress', 'Status', 'Destination', 
                               'Service', 'Conflict']
        self.data = [map(str, range(1, 8)), map(str, range(2, 9))]*2
        self.data2 = [map(str, range(2, 7)), map(str, range(1, 6))]*2
        
        self.upload_table = self._create_table(self.uploads_header)
        self.upload_table.setItemDelegate(UploadTableDelegate(self, self.font, c))
        
        self.history_table = self._create_table(self.history_header)
        self.history_table.setItemDelegate(UploadTableDelegate(self, self.font, c))

        self._createRibbon()
        self._createSideSpaces()

        tab = QtGui.QTabWidget()
        tab.setTabShape(QtGui.QTabWidget.Triangular)
        tab.insertTab(0, self.upload_table, 'Active')
        tab.insertTab(1, self.history_table, 'History')
        tab.insertTab(2, QtGui.QLabel('SETTINGS'), 'Settings')

        self.setCentralWidget(tab)

    def add_history_item(self, item):
        #[name, dest, service, date, id]
        self.history_table.model().add_item(item)
        
    def update_all_history(self, items):
        self.history_table.model().remove_all()
        for i in items:
            self.add_history_item(i)
            
    def delete_history_item(self, id, row=None):
        self.history_table.model().remove(id, row)
        
    def closeEvent(self, event):
        self.setVisible(False)
        event.ignore()

    def selection_changed(self, new, old):
        for i in new.indexes():
            self.upload_table.selectRow(i.row())

    def _createSideSpaces(self):
        '''
        Add some space on the left and right of the table.
        '''
        leftDockWidget = QtGui.QDockWidget()
        leftDockWidget.setTitleBarWidget(QtGui.QWidget())
        leftDockWidget.setWidget(QtGui.QLabel(' '))
        self.addDockWidget(Qt.Qt.LeftDockWidgetArea, leftDockWidget)

        rightDockWidget = QtGui.QDockWidget()
        rightDockWidget.setTitleBarWidget(QtGui.QWidget())
        rightDockWidget.setWidget(QtGui.QLabel(' '))
        self.addDockWidget(Qt.Qt.RightDockWidgetArea, rightDockWidget)

    def _createRibbon(self):
        def _createDockWidget(elem):
            dockWidget = QtGui.QDockWidget()
            #Hide the dock title bar
            dockWidget.setTitleBarWidget(QtGui.QWidget())

            setattr(self, elem, QtGui.QPushButton())
            getattr(self, elem).setIcon(QtGui.QIcon(getattr(self, elem + 'Path')))
            getattr(self, elem).setFlat(True)
            dockWidget.setWidget(getattr(self, elem))
            self.addDockWidget(Qt.Qt.TopDockWidgetArea, dockWidget)

        #@Mediator
        _createDockWidget('addBtn')
        _createDockWidget('removeBtn')
        _createDockWidget('playBtn')
        _createDockWidget('stopBtn')

    def _create_table(self, header):
        tbl = QtGui.QTableView()

        tm = MyTableModel(header, parent=self)
        tbl.setModel(tm)
        QtCore.QObject.connect(tbl.selectionModel(),
                               QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
                               self.selection_changed)

        tbl.setMinimumSize(704, 300)
        tbl.setShowGrid(False)
        tbl.setFont(self.font)
        tbl.hideColumn(len(header))

        vh = tbl.verticalHeader()
        vh.setVisible(False)

        hh = tbl.horizontalHeader()
        for i in range(len(header)):
            hh.setResizeMode(i, QtGui.QHeaderView.Stretch)

        # set column width to fit contents
        tbl.resizeColumnsToContents()
        tbl.setSortingEnabled(True)

        return tbl
        
if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    window = DetailedWindow('Cloudy')
    window.show()

    sys.exit(app.exec_())
