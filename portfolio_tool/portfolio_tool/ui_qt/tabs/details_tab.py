from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .asset_summary_tab import AssetSummaryTab
from .charts_tab import ChartsTab
from .weights_tab import WeightsTab


class DetailsTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.weights_tab = WeightsTab()
        self.charts_tab = ChartsTab()
        self.asset_summary_tab = AssetSummaryTab()

        tabs = QTabWidget()
        tabs.addTab(self.weights_tab, "Weights")
        tabs.addTab(self.charts_tab, "Charts")
        tabs.addTab(self.asset_summary_tab, "Asset Summary")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(tabs)

    def clear(self) -> None:
        self.weights_tab.clear()
        self.charts_tab.clear()
        self.asset_summary_tab.clear()

    def update_details(self, result: dict) -> None:
        self.weights_tab.update_weights(result)
        self.charts_tab.update_charts(result)
        self.asset_summary_tab.update_summary(result)
