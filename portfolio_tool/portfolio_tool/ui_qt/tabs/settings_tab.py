from __future__ import annotations

from pathlib import Path
import os

from PySide6.QtCore import Qt
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
    QSizePolicy,
    QScrollArea,
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
        self._debug_layout = bool(int(os.getenv("UI_DEBUG_LAYOUT", "0")))

        self.tickers_input = QLineEdit()
        self.tickers_input.setPlaceholderText("SPY, QQQ, VWCE.DE")
        self.tickers_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.period = QComboBox()
        self.period.addItems(["1y", "3y", "5y", "max"])
        self.period.setCurrentText("5y")
        self.period.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.log_returns = QCheckBox("Log returns")
        self.allow_short = QCheckBox("Allow short")
        self.weight_bounds = QCheckBox("Enable weight bounds")
        self.weight_bounds.setChecked(True)

        self.risk_free = QLineEdit("0.00")
        self.currency = QLineEdit("USD")
        self.min_weight = QLineEdit("0.03")
        self.max_weight = QLineEdit("0.25")
        self.max_drawdown = QLineEdit("")
        for widget in (self.risk_free, self.currency, self.min_weight, self.max_weight, self.max_drawdown):
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.mc_sims = QSpinBox()
        self.mc_sims.setRange(100, 200000)
        self.mc_sims.setSingleStep(500)
        self.mc_sims.setValue(20000)
        self.mc_sims.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.study_name = QLineEdit("study")
        self.capital = QLineEdit("0")
        self.base_dir = QLineEdit(str(Path.cwd()))
        self.base_dir.setReadOnly(True)
        for widget in (self.study_name, self.capital, self.base_dir):
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.benchmark = BenchmarkBox()

        market_group = QGroupBox("Market")
        market_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        market_form = QFormLayout(market_group)
        market_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        market_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
        market_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        market_form.addRow("Period", self.period)
        market_form.addRow("", self.log_returns)
        market_form.addRow("Risk-free rate (annual)", self.risk_free)
        market_form.addRow("Currency", self.currency)

        constraints_group = QGroupBox("Constraints")
        constraints_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        cons_grid = QGridLayout(constraints_group)
        cons_grid.setColumnStretch(1, 1)
        cons_grid.setHorizontalSpacing(10)
        cons_grid.setVerticalSpacing(8)
        cons_grid.addWidget(self.weight_bounds, 0, 0, 1, 2)
        cons_grid.addWidget(QLabel("Min weight"), 1, 0)
        cons_grid.addWidget(self.min_weight, 1, 1)
        cons_grid.addWidget(QLabel("Max weight"), 2, 0)
        cons_grid.addWidget(self.max_weight, 2, 1)
        cons_grid.addWidget(QLabel("Max drawdown threshold"), 3, 0)
        cons_grid.addWidget(self.max_drawdown, 3, 1)
        cons_grid.addWidget(self.allow_short, 4, 0, 1, 2)
        cons_grid.setRowMinimumHeight(0, self.weight_bounds.sizeHint().height())
        cons_grid.setRowMinimumHeight(1, self.min_weight.sizeHint().height())
        cons_grid.setRowMinimumHeight(2, self.max_weight.sizeHint().height())
        cons_grid.setRowMinimumHeight(3, self.max_drawdown.sizeHint().height())
        cons_grid.setRowMinimumHeight(4, self.allow_short.sizeHint().height())

        simulation_group = QGroupBox("Simulation")
        simulation_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sim_form = QFormLayout(simulation_group)
        sim_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        sim_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
        sim_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        sim_form.addRow("Monte Carlo simulations", self.mc_sims)

        study_group = QGroupBox("Study")
        study_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        study_form = QFormLayout(study_group)
        study_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        study_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
        study_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        study_form.addRow("Study name", self.study_name)
        study_form.addRow("Capital (0 = skip)", self.capital)
        study_form.addRow("Base directory", self.base_dir)

        self._content = QWidget()
        layout = QVBoxLayout(self._content)
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
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 0)

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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._debug_widgets = {
            "market_group": market_group,
            "constraints_group": constraints_group,
            "simulation_group": simulation_group,
            "benchmark_group": self.benchmark,
            "study_group": study_group,
            "min_weight": self.min_weight,
            "max_weight": self.max_weight,
            "max_drawdown": self.max_drawdown,
        }

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

    def resizeEvent(self, event) -> None:
        if self._debug_layout:
            for name, widget in self._debug_widgets.items():
                size = widget.size()
                hint = widget.sizeHint()
                min_hint = widget.minimumSizeHint()
                policy = widget.sizePolicy()
                print(
                    f"[UI_DEBUG] {name}: size={size.width()}x{size.height()} "
                    f"hint={hint.width()}x{hint.height()} "
                    f"min_hint={min_hint.width()}x{min_hint.height()} "
                    f"policy={policy.horizontalPolicy()},{policy.verticalPolicy()}"
                )
        super().resizeEvent(event)
