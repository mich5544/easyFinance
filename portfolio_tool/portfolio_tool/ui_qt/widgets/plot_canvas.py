from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ImagePlotCanvas(FigureCanvas):
    def __init__(self, parent=None) -> None:
        self._figure = Figure(figsize=(5, 3))
        self._ax = self._figure.add_subplot(111)
        self._ax.axis("off")
        super().__init__(self._figure)
        if parent is not None:
            self.setParent(parent)

    def set_image(self, path: str | Path | None) -> None:
        self._ax.clear()
        self._ax.axis("off")
        if path:
            p = Path(path)
            if p.exists():
                img = mpimg.imread(p)
                self._ax.imshow(img)
        self.draw()
