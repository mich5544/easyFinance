from __future__ import annotations


LIGHT_QSS = """
QWidget {
    font-family: "Segoe UI";
    color: #1f2937;
    background: #f5f7fb;
}
QMainWindow::separator {
    background: #d7dde7;
    width: 1px;
}
QGroupBox {
    border: 1px solid #d7dde7;
    border-radius: 8px;
    margin-top: 12px;
    padding: 10px;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px 0 6px;
    color: #334155;
    font-weight: 600;
}
QLabel {
    background: transparent;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 8px;
    background: #ffffff;
    min-height: 24px;
}
QTableView {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #e2e8f0;
}
QHeaderView::section {
    background: #eef2f7;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #d7dde7;
    font-weight: 600;
}
QPushButton {
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    min-height: 32px;
    min-width: 110px;
}
QPushButton:disabled {
    background: #94a3b8;
}
QPushButton#secondary {
    background: #e2e8f0;
    color: #1f2937;
}
QTabWidget::pane {
    border: 1px solid #d7dde7;
    border-radius: 8px;
    padding: 4px;
}
QTabBar::tab {
    background: #e8ecf4;
    padding: 8px 14px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background: #ffffff;
    font-weight: 600;
}
QStatusBar {
    background: #ffffff;
    border-top: 1px solid #e2e8f0;
}
"""


DARK_QSS = """
QWidget {
    font-family: "Segoe UI";
    color: #e2e8f0;
    background: #0f172a;
}
QGroupBox {
    border: 1px solid #1f2937;
    border-radius: 8px;
    margin-top: 12px;
    padding: 10px;
    background: #111827;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px 0 6px;
    color: #cbd5f5;
    font-weight: 600;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 8px;
    background: #0b1220;
    min-height: 24px;
}
QTableView {
    background: #0b1220;
    border: 1px solid #1f2937;
    border-radius: 6px;
    gridline-color: #1f2937;
}
QHeaderView::section {
    background: #111827;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #1f2937;
    font-weight: 600;
}
QPushButton {
    background: #38bdf8;
    color: #0b1220;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    min-height: 32px;
    min-width: 110px;
}
QPushButton:disabled {
    background: #475569;
    color: #94a3b8;
}
QPushButton#secondary {
    background: #1f2937;
    color: #e2e8f0;
}
QTabWidget::pane {
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 4px;
}
QTabBar::tab {
    background: #111827;
    padding: 8px 14px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background: #0b1220;
    font-weight: 600;
}
QStatusBar {
    background: #0b1220;
    border-top: 1px solid #1f2937;
}
"""
