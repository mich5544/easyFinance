from __future__ import annotations

from typing import List

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QSortFilterProxyModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ...utils import normalize_tickers


class AssetTableModel(QAbstractTableModel):
    def __init__(self, items: List[dict] | None = None) -> None:
        super().__init__()
        self._items = items if items is not None else []

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        return len(self._items)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return 2

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        return ["Enabled", "Ticker"][section]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._items[index.row()]
        if index.column() == 0:
            if role == Qt.CheckStateRole:
                return Qt.Checked if item.get("enabled", True) else Qt.Unchecked
            if role == Qt.DisplayRole:
                return ""
        if index.column() == 1:
            if role in (Qt.DisplayRole, Qt.EditRole):
                return item.get("ticker", "")
        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole):
        if not index.isValid():
            return False
        item = self._items[index.row()]
        if index.column() == 0 and role == Qt.CheckStateRole:
            item["enabled"] = value == Qt.Checked
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            return True
        if index.column() == 1 and role == Qt.EditRole:
            item["ticker"] = str(value).strip().upper()
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemIsEnabled
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def add_tickers(self, tickers: List[str]) -> None:
        if not tickers:
            return
        existing = {item["ticker"] for item in self._items}
        new_items = []
        for ticker in tickers:
            if ticker in existing:
                continue
            new_items.append({"ticker": ticker, "enabled": True})
            existing.add(ticker)
        if not new_items:
            return
        start = len(self._items)
        self.beginInsertRows(QModelIndex(), start, start + len(new_items) - 1)
        self._items.extend(new_items)
        self.endInsertRows()

    def remove_rows(self, rows: List[int]) -> None:
        if not rows:
            return
        for row in sorted(rows, reverse=True):
            if 0 <= row < len(self._items):
                self.beginRemoveRows(QModelIndex(), row, row)
                self._items.pop(row)
                self.endRemoveRows()

    def enabled_tickers(self) -> List[str]:
        return [item["ticker"] for item in self._items if item.get("enabled", True)]


class AssetTable(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._model = AssetTableModel()
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setSortCaseSensitivity(Qt.CaseInsensitive)

        self._input = QLineEdit()
        self._input.setPlaceholderText("AAPL, MSFT, VWCE.DE")
        self._add_btn = QPushButton("Add")
        self._remove_btn = QPushButton("Remove selected")
        self._remove_btn.setObjectName("secondary")

        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Tickers"))
        input_row.addWidget(self._input)
        input_row.addWidget(self._add_btn)
        input_row.addWidget(self._remove_btn)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.SelectedClicked
            | QAbstractItemView.EditKeyPressed
        )
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addLayout(input_row)
        layout.addWidget(self._table)

        self._add_btn.clicked.connect(self._add_from_input)
        self._remove_btn.clicked.connect(self._remove_selected)

    def _add_from_input(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        tickers = normalize_tickers(text)
        self._model.add_tickers(tickers)
        self._input.clear()

    def _remove_selected(self) -> None:
        selection = self._table.selectionModel().selectedRows()
        rows = [self._proxy.mapToSource(idx).row() for idx in selection]
        self._model.remove_rows(rows)

    def enabled_tickers(self) -> List[str]:
        return self._model.enabled_tickers()

    def set_tickers(self, tickers: List[str]) -> None:
        self._model = AssetTableModel()
        self._proxy.setSourceModel(self._model)
        self._model.add_tickers(tickers)
