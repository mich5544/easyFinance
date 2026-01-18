from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtCore import QObject, QThread, Signal, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import data as data_module
from ..main import StudyError, run_study
from ..symbol_resolver import resolve_symbols
from ..utils import normalize_tickers
from .tabs.settings_tab import SettingsTab
from .theme import DARK_QSS, LIGHT_QSS
from .widgets.data_horizon_dialog import DataHorizonDialog


class StudyWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    status = Signal(str)

    def __init__(self, config: Dict) -> None:
        super().__init__()
        self._config = config

    @Slot()
    def run(self) -> None:
        try:
            self.status.emit("Running study...")
            result = run_study(self._config)
            self.finished.emit(result)
        except StudyError as exc:
            self.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class HorizonWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    status = Signal(str)

    def __init__(self, config: Dict) -> None:
        super().__init__()
        self._config = config

    @Slot()
    def run(self) -> None:
        try:
            self.status.emit("Checking data horizon...")
            tickers = normalize_tickers(self._config.get("tickers", []))
            assets = self._config.get("assets")
            if assets is None:
                assets = [{"user_symbol": t} for t in tickers]
            if not assets:
                raise StudyError("No tickers provided.")

            base_dir = Path(self._config.get("base_dir", Path.cwd()))
            resolved = resolve_symbols(
                assets,
                base_dir=base_dir,
                target_currency=self._config.get("currency"),
            )
            yahoo_symbols = [a.yahoo_symbol for a in resolved if a.yahoo_symbol]
            ranges = data_module.get_date_ranges(yahoo_symbols, period=self._config.get("period", "5y"))

            assets_info = []
            for asset in resolved:
                if asset.yahoo_symbol in ranges:
                    info = ranges[asset.yahoo_symbol]
                    assets_info.append(
                        {
                            "user_symbol": asset.user_symbol,
                            "yahoo_symbol": asset.yahoo_symbol,
                            "start": info["start"],
                            "end": info["end"],
                            "name": asset.name,
                            "isin": asset.isin,
                        }
                    )

            if len(assets_info) < 2:
                raise StudyError("Not enough valid assets after data check.")

            self.finished.emit(
                {
                    "config": self._config,
                    "assets_info": assets_info,
                }
            )
        except StudyError as exc:
            self.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Portfolio Tool - Markowitz Analyzer")
        self.resize(1200, 800)

        self._worker_thread: QThread | None = None
        self._worker: StudyWorker | None = None
        self._horizon_thread: QThread | None = None
        self._horizon_worker: HorizonWorker | None = None
        self._latest_result: Dict | None = None
        self._last_config: Dict | None = None

        self.settings_tab = SettingsTab(self._open_excel, self._open_folder, self)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.settings_tab, "Study Setup")

        title = QLabel("Portfolio Tool (Markowitz)")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_study)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.currentTextChanged.connect(self._apply_theme)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(16, 16, 16, 8)
        top_bar.addWidget(title)
        top_bar.addStretch(1)
        top_bar.addWidget(QLabel("Theme"))
        top_bar.addWidget(self.theme_combo)
        top_bar.addWidget(self.run_button)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 0, 12, 12)
        layout.addLayout(top_bar)
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")
        self._apply_theme(self.theme_combo.currentText())

    def _open_excel(self) -> None:
        if not self._latest_result:
            QMessageBox.information(self, "Info", "Run a study first.")
            return
        excel_path = self._latest_result.get("report_paths", {}).get("excel")
        if not excel_path or not Path(excel_path).exists():
            QMessageBox.information(self, "Info", "Excel file not found.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(excel_path))))

    def _open_folder(self) -> None:
        if not self._latest_result:
            QMessageBox.information(self, "Info", "Run a study first.")
            return
        excel_path = self._latest_result.get("report_paths", {}).get("excel")
        if not excel_path:
            QMessageBox.information(self, "Info", "Study folder not found.")
            return
        folder = Path(excel_path).parent
        if folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        else:
            QMessageBox.information(self, "Info", "Study folder not found.")

    def _reset_results(self) -> None:
        self._latest_result = None
        self._last_config = None

    def run_study(self) -> None:
        try:
            config = self.settings_tab.get_config()
        except ValueError as exc:
            QMessageBox.warning(self, "Input error", str(exc))
            return

        self._reset_results()
        self._last_config = config
        self.run_button.setEnabled(False)
        self.status.showMessage("Starting...")
        self._start_horizon_check(config)

    @Slot(dict)
    def _handle_finished(self, result: Dict) -> None:
        self._latest_result = result
        self.run_button.setEnabled(True)
        self.status.showMessage("Study completed.")

        benchmark = result.get("benchmark") or {}
        status = benchmark.get("status")
        if status and status != "OK":
            self.status.showMessage(f"Benchmark warning: {status}")

    @Slot(str)
    def _handle_error(self, message: str) -> None:
        self.run_button.setEnabled(True)
        self.status.showMessage("Failed.")
        QMessageBox.critical(self, "Run failed", message)

    def _clear_worker(self) -> None:
        self._worker = None

    def _clear_horizon_worker(self) -> None:
        self._horizon_worker = None

    def _start_horizon_check(self, config: Dict) -> None:
        worker = HorizonWorker(config)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.status.connect(self.status.showMessage)
        worker.finished.connect(self._handle_horizon_finished)
        worker.error.connect(self._handle_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._horizon_worker = worker
        self._horizon_thread = thread
        thread.finished.connect(self._clear_horizon_worker)
        thread.start()

    @Slot(dict)
    def _handle_horizon_finished(self, payload: Dict) -> None:
        config = payload["config"]
        assets_info = payload["assets_info"]

        starts = {a["start"] for a in assets_info}
        drop = []
        if len(starts) > 1:
            dialog = DataHorizonDialog(assets_info, self)
            if dialog.exec() == QDialog.Accepted:
                drop = dialog.selected_drop()
            else:
                self.run_button.setEnabled(True)
                self.status.showMessage("Cancelled.")
                return

        if drop:
            remaining = [a for a in assets_info if a["yahoo_symbol"] not in drop]
            config["assets"] = [
                {
                    "user_symbol": a["user_symbol"],
                    "name": a["name"],
                    "isin": a["isin"],
                }
                for a in remaining
            ]
            config["tickers"] = ", ".join([a["user_symbol"] for a in remaining])

        self._last_config = config
        self._start_run_worker(config)

    def _start_run_worker(self, config: Dict) -> None:
        worker = StudyWorker(config)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._handle_finished)
        worker.error.connect(self._handle_error)
        worker.status.connect(self.status.showMessage)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._worker = worker
        self._worker_thread = thread
        thread.finished.connect(self._clear_worker)
        thread.start()

    def _apply_theme(self, theme: str) -> None:
        qss = LIGHT_QSS if theme == "Light" else DARK_QSS
        self.setStyleSheet(qss)

