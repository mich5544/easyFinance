from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Sequence

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class PandasTableModel(QAbstractTableModel):
    def __init__(
        self,
        df: pd.DataFrame | None = None,
        formatters: Dict[str, Callable[[object], str]] | None = None,
    ) -> None:
        super().__init__()
        self._df = df if df is not None else pd.DataFrame()
        self._formatters = formatters or {}

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        return 0 if self._df is None else len(self._df.index)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return 0 if self._df is None else len(self._df.columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole or self._df is None:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return str(self._df.index[section])

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or self._df is None:
            return None
        value = self._df.iat[index.row(), index.column()]
        column = self._df.columns[index.column()]

        if role == Qt.DisplayRole:
            if pd.isna(value):
                return ""
            formatter = self._formatters.get(str(column))
            if formatter:
                return formatter(value)
            if isinstance(value, (float, int)):
                return f"{value:.4f}" if isinstance(value, float) else str(value)
            return str(value)

        if role == Qt.TextAlignmentRole:
            if isinstance(value, (int, float)):
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        return None


class SimpleTableModel(QAbstractTableModel):
    def __init__(
        self,
        headers: Sequence[str],
        rows: Iterable[Sequence],
        numeric_columns: Iterable[int] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._headers = list(headers)
        self._rows = [list(r) for r in rows]
        self._numeric = set(numeric_columns or [])

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        value = self._rows[index.row()][index.column()]
        if role == Qt.DisplayRole:
            if index.column() in self._numeric and value is not None:
                if isinstance(value, float):
                    return f"{value:.4f}"
                return str(value)
            return "" if value is None else str(value)
        if role == Qt.TextAlignmentRole and index.column() in self._numeric:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._headers[section]
        return str(section + 1)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        reverse = order == Qt.DescendingOrder

        def key(row: List):
            value = row[column]
            if value is None:
                return float("-inf") if reverse else float("inf")
            return value

        self.layoutAboutToBeChanged.emit()
        self._rows.sort(key=key, reverse=reverse)
        self.layoutChanged.emit()

    def update_rows(self, rows: Iterable[Sequence]) -> None:
        self.beginResetModel()
        self._rows = [list(r) for r in rows]
        self.endResetModel()
