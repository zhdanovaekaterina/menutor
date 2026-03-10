import logging
import sys

from PySide6.QtWidgets import QApplication

from backend.composition_root import ApplicationContainer
from backend.main_window import MainWindow


def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app = QApplication(sys.argv)
    container = ApplicationContainer()
    window = MainWindow(container)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
