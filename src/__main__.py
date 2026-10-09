
import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import parse_config


def main() -> None:
    """Разобрать параметры до загрузки графического интерфейса."""
    config = parse_config()
    print(config.describe(), flush=True)
    from src.gui import main as open_window

    open_window(config)

if __name__ == "__main__":
    main()
