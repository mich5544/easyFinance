from __future__ import annotations

from typing import Dict

from PySide6.QtWidgets import QTableView, QVBoxLayout, QWidget

from ..widgets.table_model import SimpleTableModel


class WeightsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.table = QTableView()
        self.model = SimpleTableModel(
            headers=["Ticker", "Min Var Weight", "Max Sharpe Weight"],
            rows=[],
            numeric_columns=[1, 2],
        )
        self.table.setModel(self.model)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self.table)

    def clear(self) -> None:
        self.model.update_rows([])

    def update_weights(self, result: Dict) -> None:
        tickers = result.get("tickers", [])
        min_weights = result["min_variance"].weights
        max_weights = result["max_sharpe"].weights
        rows = []
        for idx, ticker in enumerate(tickers):
            rows.append([ticker, float(min_weights[idx]), float(max_weights[idx])])
        self.model.update_rows(rows)
