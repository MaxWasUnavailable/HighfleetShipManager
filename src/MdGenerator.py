from ruamel.yaml import YAML
from os import listdir

yaml = YAML(typ='safe')


class MdGenerator:
    """
    Crude readme.md generator based on ship.yaml files.
    """
    def __init__(self):
        return

    @staticmethod
    def generate_md(yaml_file_path: str):
        """
        Generates the readme.me for the provided yaml file's ship.
        :param yaml_file_path: Yaml file to base the information on.
        """
        data = yaml.load(open(yaml_file_path))
        dir_name = '/'.join(yaml_file_path.split("/")[:-1]) + "/"
        md_file = open(dir_name + "readme.md", 'w')

        img_name = ""
        for file in listdir(dir_name):
            if file.endswith(".png") or file.endswith(".jpg"):
                img_name = file

        md_file.write(
            f"""
![]({img_name})
# {data.get("name", "")}
{data.get("description", "")}

{"".join([f"- {tag}{chr(10)}" for tag in data.get("tags", [])])}

```
author: {data.get("author", "unknown")}
version: {data.get("version", "unknown")}
game_version: {data.get("game_version", "unknown")}
```
            """
        )


if __name__ == '__main__':
    md = MdGenerator()
    for ship_dir in listdir("../ships/"):
        md.generate_md(f"../ships/{ship_dir}/ship.yaml")
