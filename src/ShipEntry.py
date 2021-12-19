from PySide2 import QtCore, QtWidgets, QtGui
from io import BytesIO
from ast import literal_eval
import requests
import os


class ShipEntry:
    """
    Represents a ship's information.
    """
    def __init__(self, data: dict, url: str = "", image: BytesIO = None):
        """
        Initialises the ShipEntry.
        :param data: YAML dict object.
        :param url: Url to the ship's folder in the repo.
        :param image: File object that stores the ship's image in-memory.
        """
        self.data = data
        self.url = url or ""
        self.image = image or None

    def __str__(self):
        return self.data["name"]

    @staticmethod
    def create_required_directories():
        """
        Create required directories in case they don't exist.
        """
        if not os.path.exists("./data"):
            os.mkdir("./data")
        if not os.path.exists("./data/downloads"):
            os.mkdir("./data/downloads")

    def download(self, path="./data/downloads/"):
        """
        Downloads ship to provided path directory.
        :param path: Directory to download to.
        """
        if path == "./data/downloads/":
            self.create_required_directories()
        parsed_url = literal_eval(requests.get(self.url).content.decode("utf-8"))
        if len(parsed_url) == 0:
            return

        remote_folder_name = parsed_url[0]['path'].split("/")[1]

        full_path = path + remote_folder_name
        full_path_temp = full_path
        i = 1

        while os.path.exists(full_path_temp):
            full_path_temp = full_path + f"({i})"
            i += 1

        full_path = full_path_temp + "/"

        os.mkdir(full_path)

        for file in parsed_url:
            file_to_save = open(full_path + file['name'], 'wb')
            file_to_save.write(requests.get(file['download_url']).content)
            file_to_save.close()


class ShipEntryWidget(QtWidgets.QFrame):
    """
    Framed widget that holds and displays a Ship's info for use in the list.
    """
    def __init__(self, ship_entry: ShipEntry, parent=None, downloads_dir: str = "./data/downloads/"):
        """
        Initialises the ShipEntry.
        :param data: YAML dict object.
        :param url: Url to the ship's folder in the repo.
        :param image: File object that stores the ship's image in-memory.
        :param parent: Parent widget.
        """
        super().__init__(parent)
        self.setFrameStyle(QtCore.Qt.SolidLine)

        self.downloads_dir = downloads_dir
        self.ship_entry = ship_entry

        self.setToolTip(str(self.ship_entry))

        self.setup_widget()

    def setup_widget(self):
        """
        Sets up the widget representation; adding the labels and download button.
        """
        layout = QtWidgets.QGridLayout()

        download_button = QtWidgets.QPushButton(self)
        download_button.setText("Download")
        name_label = QtWidgets.QLabel(self)
        name_label.setText(self.ship_entry.data.get("name", ""))
        tags_label = QtWidgets.QLabel(self)
        tags_label.setStyleSheet("QLabel {color: #e9a576}")
        tags_label.setText(str(", ".join(self.ship_entry.data.get("tags", ""))))

        download_button.clicked.connect(lambda: self.ship_entry.download(self.downloads_dir))

        layout.addWidget(name_label, 0, 0)
        layout.addWidget(tags_label, 1, 0)
        layout.addWidget(download_button, 2, 0)

        self.setLayout(layout)

    def get_ship_display_text(self):
        """
        Generates the text to display in the ship info widget when selected.
        :return: The text to display.
        """
        ship_data = self.ship_entry.data
        text = \
            f"""
{ship_data['name']}

{", ".join(ship_data['tags'])}

{ship_data['description']}


Author: {ship_data['author']}
Version: {ship_data['version']}
Made for game version: {ship_data['game_version']}
            """

        return text


# if __name__ == '__main__':
#     from ruamel.yaml import YAML
#
#     yaml = YAML(typ='safe')
#
#     data = yaml.load(
#         """
# author: "Max"
# name: "Zephyr-Class Light Strategic Command Carrier"
# description: "The Zephyr-class is a lightweight but nimble flagship carrier intended to support its fleet from the backlines using its complement of 3 interceptors and 5 fighter-bombers. Additionally, it features a light armament of 2 strategic missiles."
# tags:
#   - "flagship"
#   - "carrier"
#   - "strategic"
# version: 1.0
# game_version: 1.12
#         """
#     )
#     ship = ShipEntry(data, "https://api.github.com/repos/MaxWasUnavailable/HighfleetShipRepository/contents/ships/zephyr?ref=master")
#
#     print(ship)
#
#     ship.download("../ships/")
