from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QFormLayout, QGroupBox, QLineEdit


class BenchmarkBox(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("Benchmark", parent)
        self._enabled = QCheckBox("Enable benchmark")
        self._enabled.setChecked(True)
        self._ticker = QLineEdit("VWCE.DE")

        layout = QFormLayout(self)
        layout.addRow(self._enabled)
        layout.addRow("Ticker (Yahoo)", self._ticker)

    def is_enabled(self) -> bool:
        return self._enabled.isChecked()

    def ticker(self) -> str:
        text = self._ticker.text().strip()
        return text or "VWCE.DE"

    def set_enabled(self, value: bool) -> None:
        self._enabled.setChecked(value)

    def set_ticker(self, value: str) -> None:
        self._ticker.setText(value)
