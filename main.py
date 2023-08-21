import sys
from PyQt5.QtWidgets import QApplication
from gui.gui_manager import GuiManager
from data.data_manager import DataManager
from controller.controller import Controller


class Main(QApplication):
    def __init__(self) -> None:
        super().__init__(sys.argv)
        self.instances = {
            'data': DataManager(self.get),
            'gui': GuiManager(self.get),
            'control': Controller(self.get)
        }

        for instance in self.instances.values():
            instance.init_instance_member()

        myWindow = self.instances['gui']
        myWindow.show()
        self.exec_()

    def get(self, arg):
        if arg in self.instances:
            return self.instances[arg]
        else:
            print("### Not formatted arg ###")


if __name__ == "__main__":
    main = Main()
