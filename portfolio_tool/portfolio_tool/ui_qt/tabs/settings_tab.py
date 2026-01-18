from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..widgets.benchmark_box import BenchmarkBox
from ...utils import normalize_tickers


class SettingsTab(QWidget):
    def __init__(self, open_excel_callback, open_folder_callback, parent=None) -> None:
        super().__init__(parent)
        self._open_excel = open_excel_callback
        self._open_folder = open_folder_callback

        self.tickers_input = QLineEdit()
        self.tickers_input.setPlaceholderText("SPY, QQQ, VWCE.DE")

        self.period = QComboBox()
        self.period.addItems(["1y", "3y", "5y", "max"])
        self.period.setCurrentText("5y")

        self.log_returns = QCheckBox("Log returns")
        self.allow_short = QCheckBox("Allow short")
        self.weight_bounds = QCheckBox("Enable weight bounds")
        self.weight_bounds.setChecked(True)

        self.risk_free = QLineEdit("0.00")
        self.currency = QLineEdit("USD")
        self.min_weight = QLineEdit("0.03")
        self.max_weight = QLineEdit("0.25")
        self.max_drawdown = QLineEdit("")

        self.mc_sims = QSpinBox()
        self.mc_sims.setRange(100, 200000)
        self.mc_sims.setSingleStep(500)
        self.mc_sims.setValue(20000)

        self.study_name = QLineEdit("study")
        self.capital = QLineEdit("0")
        self.base_dir = QLineEdit(str(Path.cwd()))
        self.base_dir.setReadOnly(True)

        self.benchmark = BenchmarkBox()

        market_group = QGroupBox("Market")
        market_form = QFormLayout(market_group)
        market_form.addRow("Period", self.period)
        market_form.addRow("", self.log_returns)
        market_form.addRow("Risk-free rate (annual)", self.risk_free)
        market_form.addRow("Currency", self.currency)

        constraints_group = QGroupBox("Constraints")
        cons_form = QFormLayout(constraints_group)
        cons_form.addRow("", self.weight_bounds)
        cons_form.addRow("Min weight", self.min_weight)
        cons_form.addRow("Max weight", self.max_weight)
        cons_form.addRow("Max drawdown threshold", self.max_drawdown)
        cons_form.addRow("", self.allow_short)

        simulation_group = QGroupBox("Simulation")
        sim_form = QFormLayout(simulation_group)
        sim_form.addRow("Monte Carlo simulations", self.mc_sims)

        study_group = QGroupBox("Study")
        study_form = QFormLayout(study_group)
        study_form.addRow("Study name", self.study_name)
        study_form.addRow("Capital (0 = skip)", self.capital)
        study_form.addRow("Base directory", self.base_dir)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        assets_group = QGroupBox("Assets")
        assets_form = QFormLayout(assets_group)
        assets_form.addRow("Tickers (comma separated)", self.tickers_input)
        layout.addWidget(assets_group)

        grid = QGridLayout()
        grid.addWidget(market_group, 0, 0)
        grid.addWidget(constraints_group, 0, 1)
        grid.addWidget(simulation_group, 1, 0)
        grid.addWidget(self.benchmark, 1, 1)
        grid.addWidget(study_group, 2, 0, 1, 2)

        output_box = QGroupBox("Outputs")
        out_layout = QHBoxLayout(output_box)
        open_excel = QPushButton("Open Excel")
        open_folder = QPushButton("Open folder")
        open_excel.setObjectName("secondary")
        open_folder.setObjectName("secondary")
        open_excel.clicked.connect(self._open_excel)
        open_folder.clicked.connect(self._open_folder)
        out_layout.addStretch(1)
        out_layout.addWidget(open_excel)
        out_layout.addWidget(open_folder)

        layout.addLayout(grid)
        layout.addWidget(output_box)
        layout.addStretch(1)

    def build_config(self) -> dict:
        tickers = normalize_tickers(self.tickers_input.text())
        if len(tickers) < 2:
            raise ValueError("Add at least two tickers.")

        max_dd = self.max_drawdown.text().strip()
        return {
            "tickers": ", ".join(tickers),
            "period": self.period.currentText(),
            "log_returns": self.log_returns.isChecked(),
            "risk_free_rate": float(self.risk_free.text().strip()),
            "capital": float(self.capital.text().strip()),
            "currency": self.currency.text().strip() or "USD",
            "mc_sims": int(self.mc_sims.value()),
            "benchmark_enabled": self.benchmark.is_enabled(),
            "benchmark_ticker": self.benchmark.ticker(),
            "min_weight": float(self.min_weight.text().strip()),
            "max_weight": float(self.max_weight.text().strip()),
            "max_drawdown_threshold": float(max_dd) if max_dd else None,
            "allow_short": self.allow_short.isChecked(),
            "study_name": self.study_name.text().strip() or "study",
            "weight_bounds_enabled": self.weight_bounds.isChecked(),
            "base_dir": self.base_dir.text().strip(),
        }

    def get_config(self) -> dict:
        return self.build_config()
