"""About panel — displays app version and a link to the user guide."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.app_info import APP_VERSION, GUIDE_URL


class AboutPanel(QWidget):
    """Панель «О программе»."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        version_label = QLabel(f"Версия: {APP_VERSION}")
        layout.addWidget(version_label)

        guide_label = QLabel(
            f'<a href="{GUIDE_URL}">Руководство пользователя</a>'
        )
        guide_label.setOpenExternalLinks(True)
        layout.addWidget(guide_label)
