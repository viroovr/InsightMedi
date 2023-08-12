import sys
from PyQt5.QtWidgets import QApplication
from gui.test_gui import Gui
from data.test_data import DcmData
from controller.test_control import Controller


class Main(QApplication):
    def __init__(self) -> None:
        super().__init__(sys.argv)
        self.data = DcmData(self.get)
        self.gui = Gui(self.get)
        self.controller = Controller(self.get)
        
        self.gui.init_instance_member()
        self.controller.init_instance_member()

        myWindow = self.gui
        myWindow.show()
        self.exec_()

    def get(self, arg):
        if arg == 'data':
            return self.data
        elif arg == 'control':
            return self.controller
        elif arg == 'gui':
            return self.gui
        else:
            print("### Not formatted arg ###")


if __name__ == "__main__":
    main = Main()
