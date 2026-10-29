from .config import parse_config


def main(arguments=None):
    config = parse_config(arguments)
    print(config.describe())
    return 0
