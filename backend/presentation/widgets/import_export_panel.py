"""Import/export panel for shopping list."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ImportExportPanel(QWidget):
    """Панель импорта/экспорта."""

    export_text_requested = Signal()
    export_csv_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Экспорт последнего сформированного списка покупок:"))

        export_text_btn = QPushButton("Экспорт в текст (для мессенджера)")
        export_csv_btn = QPushButton("Экспорт в CSV")
        export_text_btn.clicked.connect(self.export_text_requested)
        export_csv_btn.clicked.connect(self._on_export_csv)
        layout.addWidget(export_text_btn)
        layout.addWidget(export_csv_btn)
        layout.addStretch()

    def _on_export_csv(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить список покупок", "", "CSV файлы (*.csv)"
        )
        if filepath:
            self.export_csv_requested.emit(filepath)
