from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout, QWidget


class AITab(QWidget):
    def __init__(
        self,
        on_ai_study_callback,
        on_ai_benchmark_callback,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._on_ai_study = on_ai_study_callback
        self._on_ai_benchmark = on_ai_benchmark_callback

        header = QGroupBox("AI Assistant")
        header_layout = QHBoxLayout(header)
        title = QLabel("Narrative Insights")
        title.setStyleSheet("font-weight: 600;")
        self.study_btn = QPushButton("Study")
        self.benchmark_btn = QPushButton("Benchmark")
        self.study_btn.setObjectName("secondary")
        self.benchmark_btn.setObjectName("secondary")
        self.study_btn.clicked.connect(self._on_ai_study)
        self.benchmark_btn.clicked.connect(self._on_ai_benchmark)
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.study_btn)
        header_layout.addWidget(self.benchmark_btn)

        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setPlaceholderText("Generate insights to see formatted output here.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(header)
        layout.addWidget(self.viewer, 1)

    def set_text(self, text: str) -> None:
        # QTextBrowser supports markdown in recent Qt versions; fallback to plain text.
        try:
            self.viewer.setMarkdown(text)
        except Exception:
            self.viewer.setPlainText(text)

    def set_buttons_enabled(self, enabled: bool) -> None:
        self.study_btn.setEnabled(enabled)
        self.benchmark_btn.setEnabled(enabled)
