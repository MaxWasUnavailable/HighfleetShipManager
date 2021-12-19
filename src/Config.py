from ruamel.yaml import YAML

yaml = YAML(typ='safe')


class Config:
    def __init__(self, config_path: str = "./data/config.yaml"):
        self.config = None
        self.downloads_dir = None
        self.repository_ids = None

        self.load_config(config_path)
        self.__update_from_config()

    def load_config(self, config_path):
        config_file = open(config_path, 'r')
        self.config = yaml.load(config_file)
        config_file.close()

    def __update_from_config(self):
        self.downloads_dir = self.config.get("downloads_directory", "./data/downloads")
        self.repository_ids = self.config.get("repository_ids", [])
        if self.repository_ids is None:
            self.repository_ids = []
