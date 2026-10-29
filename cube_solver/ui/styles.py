"""Folha de estilo QSS escura e moderna para o aplicativo CubeSolver."""

DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #0b1120;
    color: #f1f5f9;
    font-family: "Segoe UI", system-ui, sans-serif;
    font-size: 13px;
}

QWidget {
    color: #f1f5f9;
    font-family: "Segoe UI", system-ui, sans-serif;
}

QGroupBox {
    background-color: #151f32;
    border: 1px solid #26354d;
    border-radius: 10px;
    margin-top: 10px;
    padding: 10px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #38bdf8;
    font-size: 13px;
    font-weight: 700;
}

QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 7px;
    padding: 6px 12px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #38bdf8;
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton:disabled {
    background-color: #0f172a;
    color: #64748b;
    border-color: #1e293b;
}

QPushButton#primaryButton {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
    padding: 8px 16px;
}

QPushButton#primaryButton:hover {
    background-color: #1d4ed8;
    border-color: #60a5fa;
}

QPushButton#successButton {
    background-color: #059669;
    border: 1px solid #10b981;
    color: #ffffff;
    font-weight: 700;
}

QPushButton#successButton:hover {
    background-color: #047857;
}

QPushButton#cameraButton {
    background-color: #0284c7;
    border: 1px solid #38bdf8;
    color: #ffffff;
    font-weight: 700;
}

QPushButton#cameraButton:hover {
    background-color: #0369a1;
}

QCheckBox {
    spacing: 6px;
    color: #cbd5e1;
    font-size: 12px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #0f172a;
}

QCheckBox::indicator:checked {
    background-color: #10b981;
    border-color: #34d399;
}

QListWidget {
    background-color: #0f172a;
    border: 1px solid #26354d;
    border-radius: 8px;
    padding: 4px;
    color: #e2e8f0;
}

QListWidget::item {
    padding: 6px 8px;
    border-radius: 5px;
    margin-bottom: 2px;
}

QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 700;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QComboBox, QSlider {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px 8px;
    color: #f8fafc;
}

QStatusBar {
    background-color: #0f172a;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
}
"""

