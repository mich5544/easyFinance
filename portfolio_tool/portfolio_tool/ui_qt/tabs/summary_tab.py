from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ..widgets.table_model import SimpleTableModel


class ResultsTab(QWidget):
    def __init__(
        self,
        open_excel_callback,
        open_folder_callback,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._open_excel = open_excel_callback
        self._open_folder = open_folder_callback
        self._excel_path = ""

        self.min_return = QLabel("-")
        self.min_vol = QLabel("-")
        self.min_sharpe = QLabel("-")
        self.max_return = QLabel("-")
        self.max_vol = QLabel("-")
        self.max_sharpe = QLabel("-")
        self.benchmark_status = QLabel("-")

        perf_box = QGroupBox("Performance")
        perf_layout = QFormLayout(perf_box)
        perf_layout.addRow("Min Var return", self.min_return)
        perf_layout.addRow("Min Var volatility", self.min_vol)
        perf_layout.addRow("Min Var Sharpe", self.min_sharpe)
        perf_layout.addRow("Max Sharpe return", self.max_return)
        perf_layout.addRow("Max Sharpe volatility", self.max_vol)
        perf_layout.addRow("Max Sharpe Sharpe", self.max_sharpe)
        perf_layout.addRow("Benchmark status", self.benchmark_status)

        self.allocation_table = QTableView()
        self.allocation_model = SimpleTableModel(
            headers=["Ticker", "Min Var", "Max Sharpe"],
            rows=[],
            numeric_columns=[1, 2],
        )
        self.allocation_table.setModel(self.allocation_model)
        self.allocation_table.setSortingEnabled(False)
        self.allocation_table.setSelectionBehavior(QTableView.SelectRows)
        self.allocation_table.setSelectionMode(QTableView.SingleSelection)
        self.allocation_table.horizontalHeader().setStretchLastSection(True)
        self.allocation_table.verticalHeader().setVisible(False)
        self.allocation_table.setMinimumHeight(180)

        allocation_box = QGroupBox("Allocations (compact)")
        allocation_layout = QVBoxLayout(allocation_box)
        allocation_layout.addWidget(self.allocation_table)

        self.benchmark_table = QTableView()
        self.benchmark_model = SimpleTableModel(
            headers=["Metric", "Benchmark", "Min Var", "Max Sharpe"],
            rows=[],
            numeric_columns=[1, 2, 3],
        )
        self.benchmark_table.setModel(self.benchmark_model)
        self.benchmark_table.setSortingEnabled(False)
        self.benchmark_table.setSelectionBehavior(QTableView.SelectRows)
        self.benchmark_table.setSelectionMode(QTableView.SingleSelection)
        self.benchmark_table.horizontalHeader().setStretchLastSection(True)
        self.benchmark_table.verticalHeader().setVisible(False)
        self.benchmark_table.setMinimumHeight(150)

        benchmark_box = QGroupBox("Benchmark Comparison")
        bench_layout = QVBoxLayout(benchmark_box)
        bench_layout.addWidget(self.benchmark_table)

        self.excel_path_label = QLabel("-")
        self.output_folder_label = QLabel("-")
        open_excel = QPushButton("Open Excel")
        open_folder = QPushButton("Open folder")
        open_excel.setObjectName("secondary")
        open_folder.setObjectName("secondary")
        open_excel.clicked.connect(self._open_excel)
        open_folder.clicked.connect(self._open_folder)

        output_box = QGroupBox("Outputs")
        out_layout = QFormLayout(output_box)
        out_layout.addRow("Excel path", self.excel_path_label)
        out_layout.addRow("Study folder", self.output_folder_label)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(open_excel)
        buttons.addWidget(open_folder)
        out_layout.addRow("", buttons)

        layout = QGridLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(12)
        layout.addWidget(perf_box, 0, 0)
        layout.addWidget(benchmark_box, 1, 0)
        layout.addWidget(allocation_box, 0, 1)
        layout.addWidget(output_box, 2, 0, 1, 2)
        layout.setRowStretch(3, 1)

    def clear(self) -> None:
        for label in (
            self.min_return,
            self.min_vol,
            self.min_sharpe,
            self.max_return,
            self.max_vol,
            self.max_sharpe,
            self.benchmark_status,
        ):
            label.setText("-")
        self.excel_path_label.setText("-")
        self.output_folder_label.setText("-")
        self._excel_path = ""
        self.allocation_model.update_rows([])
        self.benchmark_model.update_rows([])

    def update_summary(self, result: Dict) -> None:
        min_perf = result["min_variance"].performance
        max_perf = result["max_sharpe"].performance

        self.min_return.setText(f"{min_perf.get('return', 0):.4f}")
        self.min_vol.setText(f"{min_perf.get('volatility', 0):.4f}")
        self.min_sharpe.setText(f"{min_perf.get('sharpe', 0):.4f}")
        self.max_return.setText(f"{max_perf.get('return', 0):.4f}")
        self.max_vol.setText(f"{max_perf.get('volatility', 0):.4f}")
        self.max_sharpe.setText(f"{max_perf.get('sharpe', 0):.4f}")

        benchmark = result.get("benchmark") or {}
        self.benchmark_status.setText(str(benchmark.get("status", "-")))

        benchmark_rows = [
            [
                "Return",
                benchmark.get("return"),
                min_perf.get("return"),
                max_perf.get("return"),
            ],
            [
                "Volatility",
                benchmark.get("volatility"),
                min_perf.get("volatility"),
                max_perf.get("volatility"),
            ],
            [
                "Sharpe",
                benchmark.get("sharpe"),
                min_perf.get("sharpe"),
                max_perf.get("sharpe"),
            ],
        ]
        self.benchmark_model.update_rows(benchmark_rows)

        report_paths = result.get("report_paths", {})
        excel_path = report_paths.get("excel", "")
        self._excel_path = excel_path
        self.excel_path_label.setText(excel_path or "-")
        folder = str(Path(excel_path).parent) if excel_path else ""
        self.output_folder_label.setText(folder or "-")

        tickers = result.get("tickers", [])
        min_weights = result["min_variance"].weights
        max_weights = result["max_sharpe"].weights
        rows = []
        for idx, ticker in enumerate(tickers):
            rows.append([ticker, float(min_weights[idx]), float(max_weights[idx])])
        self.allocation_model.update_rows(rows)
