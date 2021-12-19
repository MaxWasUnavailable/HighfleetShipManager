from github.GithubException import RateLimitExceededException
from PySide2 import QtCore, QtWidgets, QtGui
from ShipEntry import ShipEntryWidget
from ShipManager import ShipManager
from Config import Config
from copy import copy


class Popup(QtWidgets.QWidget):
    """
    Simple text popup.
    """
    def __init__(self, message):
        super().__init__()
        label = QtWidgets.QLabel(message)
        label.setTextFormat(QtCore.Qt.RichText)
        label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        label.setOpenExternalLinks(True)
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedSize(400, 120)
        self.show()


class DownloaderThread(QtCore.QThread):
    def __init__(self, parent=None):
        super(DownloaderThread, self).__init__(parent)
        self.refreshing = False
        self.ship_list = self.parent()

    def run(self):
        if not self.refreshing:
            self.refreshing = True
            self.ship_list.refresh_ship_list()
            self.refreshing = False


class ManagerWindow(QtWidgets.QMainWindow):
    """
    Main GUI window.
    Holds all widgets.
    """
    def __init__(self, config: Config = Config()):
        super().__init__()
        self.setWindowTitle("Highfleet Ship Manager")
        self.central_widget = None
        self.config = config
        self.popups = []

        self.ship_display = None
        self.ship_list = None
        self.controls = None

        self.setup_window()

    def closeEvent(self, QCloseEvent):
        """
        Close all remaining popups when the window is closed.
        """
        for popup in self.popups:
            popup.close()

    def popup(self, message):
        """
        Create and show a popup dialogue.
        :param message: The message to display.
        """
        self.popups.append(Popup(message))

    def setup_window(self):
        """
        Sets up the window.
        Initialises the necessary widgets.
        """
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QtWidgets.QGridLayout(self.central_widget)

        self.ship_display = ShipDisplay(self)
        self.ship_list = ShipList(self, config=self.config)
        self.controls = Controls(self)

        self.ship_display.setMinimumSize(self.ship_display.sizeHint())
        self.ship_list.setMinimumSize(self.ship_list.sizeHint())
        self.controls.setMinimumSize(self.controls.sizeHint())

        layout.addWidget(self.ship_list, 0, 0, 5, 1)
        layout.addWidget(self.controls, 5, 0, 1, 1)
        layout.addWidget(self.ship_display, 0, 1, 6, 1)

        self.setLayout(layout)


class ShipImage(QtWidgets.QLabel):
    """
    Represents a ship's image.

    TODO: Still needs some work to properly scale images / keep aspect ratio correct.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setToolTip("This is the ship display image.")
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setScaledContents(True)
        self.setMinimumSize(1, 1)
        self.set_placeholder()

    def resizeEvent(self, QResizeEvent):
        self.__resize()

    def __resize(self):
        self.setPixmap(self.pixmap().scaled(self.width(), self.height(), QtCore.Qt.KeepAspectRatio, QtGui.Qt.SmoothTransformation))

    def set_placeholder(self):
        """
        Sets image using placeholder.
        """
        self.setPixmap(QtGui.QPixmap("data/placeholder-image.png"))

    def set_image(self, image):
        """
        Sets the image based on the raw bytes given.
        Copy is made since the image was otherwise lost after being read.
        TODO: Can probably be done cleaner.
        :param image: The raw bytes IO to use.
        """
        self.setPixmap(QtGui.QPixmap(QtGui.QImage.fromData(QtCore.QByteArray(copy(image).read()))))


class ShipInfo(QtWidgets.QTextEdit):
    """
    A text panel that displays a ship's information.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setToolTip("This is the ship display info panel.")
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding))
        self.setReadOnly(True)

    def set_text(self, text: str):
        """
        Sets the text displayed in the panel.
        :param text: Text to display.
        """
        self.setText(text)


class ShipDisplay(QtWidgets.QFrame):
    """
    Widget that holds the ship image and info widgets.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setToolTip("This is the ship display.")
        self.setFrameStyle(QtCore.Qt.SolidLine)

        self.ship_image = None
        self.ship_info = None

        self.setup_widget()

    def setup_widget(self):
        """
        Sets up the widget.
        Initialises the ship image and info widgets.
        """
        layout = QtWidgets.QGridLayout()

        self.ship_image = ShipImage(self)
        self.ship_info = ShipInfo(self)

        self.ship_image.setMinimumSize(self.ship_image.sizeHint())
        self.ship_info.setMinimumSize(self.ship_info.sizeHint())

        layout.addWidget(self.ship_image, 0, 0, 2, 1)
        layout.addWidget(self.ship_info, 2, 0, 1, 1)

        self.setLayout(layout)

    def update_display(self, ship):
        """
        Update the Ship Display image & info widgets with information from the provided ship.
        :param ship: The ship to display.
        """
        self.ship_info.set_text(ship.get_ship_display_text())
        self.ship_image.set_image(ship.ship_entry.image)


class ShipList(QtWidgets.QListWidget):
    """
    Widget which displays a list of ships available in the repository.
    """
    def __init__(self,  parent, config: Config = Config()):
        super().__init__(parent)
        # self.setToolTip("This is the ship list.")
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding))
        self.config = config

        self.downloader_thread = DownloaderThread(self)
        self.main_window = self.parent()
        self.ship_manager = None
        self.rate_limited = False

        self.downloader_thread.finished.connect(self.thread_finished)
        self.currentItemChanged.connect(self.current_item_changed)

        self.initialise_manager()
        self.threaded_refresh_ship_list()

    def current_item_changed(self):
        """
        Execute when the selected item has changed in the Ship List widget.
        """
        self.main_window.ship_display.update_display(self.itemWidget(self.currentItem()))

    def clear_list(self):
        """
        Clears the list.
        """
        self.clear()

    def add_item(self, ship_entry):
        """
        Adds an item to the list, and then sets that item to display the given ShipEntry widget.
        :param ship_entry: The ship entry to list.
        """
        item = QtWidgets.QListWidgetItem()
        ship_entry_widget = ShipEntryWidget(ship_entry, downloads_dir=self.config.downloads_dir)
        item.setSizeHint(ship_entry_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, ship_entry_widget)

    def fill_list(self, ships):
        """
        Fills the ship list with ship entries.
        :param ships: List of ship entries to use.
        """
        self.clear_list()
        for ship in ships:
            self.add_item(ship)

    def __fill_list(self):
        self.fill_list(self.ship_manager.ships)

    def initialise_manager(self):
        """
        Initialise the ShipManager.
        """
        self.ship_manager = ShipManager(self.config.repository_ids)

    def threaded_refresh_ship_list(self):
        """
        Refresh the ship list using the thread.
        """
        if not self.downloader_thread.isRunning():
            self.downloader_thread.start()

    def refresh_ship_list(self):
        """
        Refresh the ship list.
        """
        self.rate_limited = not self.ship_manager.fetch_ship_list()

    def thread_finished(self):
        self.__fill_list()
        if self.rate_limited:
            self.main_window.popup("Error 403.<br>Github has rate limited you for refreshing too often.<br>Please wait a couple of minutes before trying again.<br>My apologies for this!")
            self.rate_limited = False


class Controls(QtWidgets.QFrame):
    """
    Misc controls for the application.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setToolTip("This is the control panel.")
        self.setFrameStyle(QtCore.Qt.SolidLine)
        self.main_window = self.parent()
        self.setup_widget()

    def setup_widget(self):
        """
        Sets up the widget.
        Initialises misc buttons and the like.
        """
        layout = QtWidgets.QGridLayout()

        # refresh_button = QtWidgets.QPushButton(self)
        # refresh_button.setText("Refresh")
        discord_button = QtWidgets.QPushButton(self)
        discord_button.setText("Discord")
        about_button = QtWidgets.QPushButton(self)
        about_button.setText("About")
        label = QtWidgets.QLabel(self)
        label.setText("See the config.yaml file in the data folder for settings.")
        label.setAlignment(QtCore.Qt.AlignCenter)

        # refresh_button.clicked.connect(lambda: self.main_window.ship_list.refresh_ship_list())
        discord_button.clicked.connect(lambda: self.main_window.popup("""<a href=\"https://discord.gg/HR5EGQz\">https://discord.gg/HR5EGQz</a>"""))
        about_button.clicked.connect(lambda: self.main_window.popup("Created by Max."))

        # layout.addWidget(refresh_button, 0, 0)
        layout.addWidget(discord_button, 0, 0)
        layout.addWidget(about_button, 0, 1)
        layout.addWidget(label, 1, 0, 1, 2)

        self.setLayout(layout)

