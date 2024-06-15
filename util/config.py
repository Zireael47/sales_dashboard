import yaml


def build_config(path: str):
    with open(path) as f:
        return yaml.load(f, Loader=yaml.FullLoader)
