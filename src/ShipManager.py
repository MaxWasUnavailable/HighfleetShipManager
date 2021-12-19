from github import Github
from io import BytesIO, StringIO
from ruamel.yaml import YAML
import requests

from ShipEntry import ShipEntry

yaml = YAML(typ='safe')


class ShipManager:
    """
    Manages and fetches the list of ships from the Github repo.
    """
    def __init__(self, repo_ids: list = None):
        if repo_ids is None:
            repo_ids = ["MaxWasUnavailable/HighfleetShipRepository"]
        self.ships = []
        self.repo_ids = repo_ids
        self.git = Github()

    def fetch_ship_list(self):
        """
        Fetches information on all ships in the github repo.
        """
        self.ships = []
        rate_limited = False
        for repo_id in self.repo_ids:
            try:
                repo = self.git.get_repo(repo_id)
                for ship_folder in repo.get_contents("ships"):
                    try:
                        ship_url = ship_folder.url
                        ship_image = None
                        data = None
                        for file in repo.get_contents(f"ships/{ship_folder.name}"):
                            if file.name.endswith(".png") or file.name.endswith(".jpg"):
                                ship_image = BytesIO(requests.get(file.download_url).content)
                            if file.name == "ship.yaml":
                                data = yaml.load(StringIO(str(requests.get(file.download_url).content.decode("utf-8"))).read())

                        ship = ShipEntry(data, ship_url, ship_image)
                        self.ships.append(ship)
                    except Exception as e:
                        print(e)
            except Exception as e:
                print(e)
                if "403" in str(e):
                    rate_limited = True

        return not rate_limited

    def refresh(self):
        self.ships.clear()
        self.fetch_ship_list()


# if __name__ == '__main__':
#     manager = ShipManager()
#     manager.fetch_ship_list()
#     print(manager.ships)
#     manager.ships[0].download("../ships/")
