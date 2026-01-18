from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class DataHorizonDialog(QDialog):
    def __init__(self, assets_info: List[dict], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Data Horizon Options")
        self.setMinimumWidth(600)
        self._assets = sorted(assets_info, key=lambda a: a["start"])
        self._drop = []

        info = QLabel(
            "Some assets have shorter history. Select assets to drop to extend the common window."
        )

        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Drop", "Ticker", "Start", "End"])
        self.table.setRowCount(len(assets_info))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)

        for row, asset in enumerate(assets_info):
            item = QTableWidgetItem()
            item.setCheckState(Qt.Unchecked)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            self.table.setItem(row, 0, item)
            for col, value in enumerate(
                [asset["yahoo_symbol"], asset["start"], asset["end"]], start=1
            ):
                cell = QTableWidgetItem(value)
                cell.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(row, col, cell)

        self.common_label = QLabel("")
        self._update_common_label()
        self.table.itemChanged.connect(lambda _item: self._update_common_label())

        keep_btn = QPushButton("Keep all (common window)")
        apply_btn = QPushButton("Apply selection")
        keep_btn.clicked.connect(self._keep_all)
        apply_btn.clicked.connect(self._apply)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        buttons.rejected.connect(self.reject)

        actions = QHBoxLayout()
        actions.addWidget(keep_btn)
        actions.addStretch(1)
        actions.addWidget(apply_btn)
        actions.addWidget(buttons)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(self.table)
        layout.addWidget(self.common_label)
        layout.addLayout(actions)

    def _selected_drop(self) -> List[str]:
        drop = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                drop.append(self._assets[row]["yahoo_symbol"])
        return drop

    def _update_common_label(self) -> None:
        drop = set(self._selected_drop())
        remaining = [a for a in self._assets if a["yahoo_symbol"] not in drop]
        if len(remaining) < 2:
            self.common_label.setText("Need at least two assets after selection.")
            return
        common_start = max(a["start"] for a in remaining)
        self.common_label.setText(f"Common start if applied: {common_start}")

    def _keep_all(self) -> None:
        self._drop = []
        self.accept()

    def _apply(self) -> None:
        self._drop = self._selected_drop()
        self.accept()

    def selected_drop(self) -> List[str]:
        return self._drop
