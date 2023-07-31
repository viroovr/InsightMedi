import sys
from PyQt5.QtWidgets import QApplication
from gui.test_gui import MyWindow

app = QApplication(sys.argv)
myWindow = MyWindow()
myWindow.show()
app.exec_()