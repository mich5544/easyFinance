from __future__ import annotations

from typing import Dict

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib import image as mpimg
from PySide6.QtWidgets import QGroupBox, QGridLayout, QLabel, QVBoxLayout, QWidget


class ChartPanel(QGroupBox):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self.figure = Figure(figsize=(4, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.axis("off")
        self.placeholder = QLabel("No chart available")
        self.placeholder.setStyleSheet("color: #777;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        layout.addWidget(self.placeholder)
        self.placeholder.hide()

    def set_image(self, path: str | None) -> None:
        self.ax.clear()
        self.ax.axis("off")
        if not path:
            self.placeholder.show()
            self.canvas.draw_idle()
            return
        try:
            image = mpimg.imread(path)
        except (FileNotFoundError, OSError):
            self.placeholder.show()
            self.canvas.draw_idle()
            return
        self.placeholder.hide()
        self.ax.imshow(image)
        self.canvas.draw_idle()


class ChartsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.charts = {
            "monte_carlo": ChartPanel("Monte Carlo + Frontier"),
            "frontier": ChartPanel("Efficient Frontier"),
            "weights_min_var": ChartPanel("Min Variance Allocation"),
            "weights_max_sharpe": ChartPanel("Max Sharpe Allocation"),
            "prices": ChartPanel("Prices"),
            "correlation": ChartPanel("Correlation"),
        }

        layout = QGridLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self.charts["monte_carlo"], 0, 0)
        layout.addWidget(self.charts["frontier"], 0, 1)
        layout.addWidget(self.charts["weights_min_var"], 1, 0)
        layout.addWidget(self.charts["weights_max_sharpe"], 1, 1)
        layout.addWidget(self.charts["prices"], 2, 0)
        layout.addWidget(self.charts["correlation"], 2, 1)
        layout.setRowStretch(3, 1)

    def clear(self) -> None:
        for panel in self.charts.values():
            panel.set_image(None)

    def update_charts(self, result: Dict) -> None:
        figures = result.get("report_paths", {}).get("figures", {})
        for key, panel in self.charts.items():
            panel.set_image(figures.get(key))
