import sys
from PyQt5.QtWidgets import QApplication
from gui.test_gui import Gui
from data.test_data import DcmData
from controller.test_control import Controller

app = QApplication(sys.argv)
myWindow = Gui()
myWindow.show()
app.exec_()
