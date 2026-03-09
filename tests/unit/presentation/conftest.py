"""Shared fixtures for presentation-layer tests requiring a QApplication."""

import sys

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Create a single QApplication for the entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
