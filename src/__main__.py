
from .config import parse_config


def main() -> None:
    """Разобрать параметры до загрузки графического интерфейса."""
    config = parse_config()
    print(config.describe(), flush=True)
    from .gui import main as open_window

    open_window(config)

if __name__ == "__main__":
    main()
