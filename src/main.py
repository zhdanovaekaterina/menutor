import sys

from PySide6.QtWidgets import QApplication

from src.composition_root import ApplicationContainer
from src.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    container = ApplicationContainer()
    window = MainWindow(container)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
