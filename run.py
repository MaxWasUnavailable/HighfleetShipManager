from src.ManagerGUI import ManagerWindow
from PySide2.QtWidgets import QApplication
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = ManagerWindow()

    main_window.show()

    sys.exit(app.exec_())
