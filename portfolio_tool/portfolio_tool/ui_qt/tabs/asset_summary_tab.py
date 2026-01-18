from __future__ import annotations

from typing import Dict

from PySide6.QtWidgets import QTableView, QVBoxLayout, QWidget

from ..widgets.table_model import SimpleTableModel


class AssetSummaryTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.table = QTableView()
        self.model = SimpleTableModel(
            headers=["Ticker", "Return", "Volatility"],
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

    def update_summary(self, result: Dict) -> None:
        tickers = result.get("tickers", [])
        mean_returns = result.get("mean_returns", {})
        cov = result.get("cov", None)
        rows = []
        if hasattr(mean_returns, "items") and cov is not None:
            import numpy as np

            vol = np.sqrt(np.diag(cov.values))
            for idx, ticker in enumerate(tickers):
                rows.append([ticker, float(mean_returns.get(ticker, 0.0)), float(vol[idx])])
        self.model.update_rows(rows)
