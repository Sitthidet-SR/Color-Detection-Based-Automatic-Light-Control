"""ธีมสีเข้มตามแบบ UI (QSS)"""

BG = "#11161D"
CARD = "#151B23"
BORDER = "#222B36"
INPUT = "#0F141A"
TEXT = "#E6EDF3"
MUTED = "#8B98A5"
GREEN = "#22C55E"
RED = "#EF4444"
PRIMARY = "#2563EB"
TX_BLUE = "#60A5FA"

QSS = f"""
QWidget {{
    background: {BG};
    color: {TEXT};
    font-family: "Inter", "Segoe UI", "Noto Sans Thai", sans-serif;
    font-size: 13px;
}}
QToolBar {{
    background: {BG};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px 14px;
    spacing: 8px;
}}
QLabel#appTitle {{ font-size: 16px; font-weight: 700; }}
QLabel#appLogo {{
    border-radius: 5px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {GREEN}, stop:1 {RED});
}}
QLabel#muted, QLabel#formKey {{ color: {MUTED}; background: transparent; }}

QFrame#card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame#card QWidget {{ background: transparent; }}
QLabel#cardTitle {{
    color: {MUTED};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QComboBox, QSpinBox {{
    background: {INPUT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 20px;
}}
QComboBox {{ min-width: 90px; }}
QComboBox QAbstractItemView {{
    background: {CARD};
    border: 1px solid {BORDER};
    selection-background-color: {PRIMARY};
}}
QSpinBox {{ qproperty-alignment: AlignCenter; }}
QFrame#card QComboBox, QFrame#card QSpinBox {{ background: {INPUT}; }}

QPushButton, QToolButton {{
    background: #1C2430;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}}
QPushButton:hover, QToolButton:hover {{ background: #232D3A; }}
QPushButton:disabled {{ color: #4B5664; background: #171D25; }}
QFrame#card QPushButton {{ background: #1C2430; }}
QFrame#card QPushButton:hover {{ background: #232D3A; }}
QFrame#card QPushButton:disabled {{ color: #4B5664; background: #171D25; }}

QPushButton#primary, QFrame#card QPushButton#primary {{
    background: {PRIMARY}; border-color: {PRIMARY}; color: white;
}}
QPushButton#primary:hover, QFrame#card QPushButton#primary:hover {{ background: #1D4ED8; }}

QPushButton#connectBtn {{
    background: {PRIMARY}; border-color: {PRIMARY}; color: white; min-width: 90px;
}}
QPushButton#connectBtn:checked {{
    background: #3A1A1D; border-color: #7F1D1D; color: #FCA5A5;
}}
QFrame#card QPushButton#startBtn {{
    background: #13361F; border-color: #166534; color: #86EFAC;
}}
QFrame#card QPushButton#startBtn:checked {{
    background: #13361F; border-color: {GREEN}; color: #86EFAC;
}}

QLabel#pill {{
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: 600;
    background: #1F2630;
    color: {MUTED};
}}
QLabel#pill[state="ok"] {{ background: #12301E; color: {GREEN}; }}
QLabel#pill[state="wait"] {{ background: #352A0E; color: #FBBF24; }}

QFrame#segmented {{
    background: {INPUT};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#segmented QPushButton {{
    background: transparent; border: none; color: {MUTED};
    padding: 5px 12px; font-weight: 500;
}}
QFrame#segmented QPushButton:checked {{ background: {PRIMARY}; color: white; font-weight: 600; }}

QLabel#video {{ background: #0B0F14; border-radius: 6px; color: {MUTED}; }}

QPlainTextEdit#log {{
    background: {INPUT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    font-family: "JetBrains Mono", "DejaVu Sans Mono", monospace;
    font-size: 12px;
    padding: 4px;
}}

QLabel#ledText {{ font-size: 26px; font-weight: 800; }}
QLabel#ledText[on="true"] {{ color: {GREEN}; }}
QLabel#ledText[on="false"] {{ color: {MUTED}; }}
QLabel#mono {{ font-family: "JetBrains Mono", "DejaVu Sans Mono", monospace; }}

QProgressBar {{
    background: {INPUT}; border: 1px solid {BORDER}; border-radius: 4px;
    max-height: 8px; text-align: center;
}}
QProgressBar::chunk {{ background: {GREEN}; border-radius: 3px; }}

QRadioButton, QCheckBox {{ spacing: 8px; }}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 14px; height: 14px; border: 1px solid #3A4553; background: {INPUT};
}}
QRadioButton::indicator {{ border-radius: 8px; }}
QCheckBox::indicator {{ border-radius: 3px; }}
QRadioButton::indicator:checked {{ background: {PRIMARY}; border: 3px solid {INPUT}; outline: none; }}
QCheckBox::indicator:checked {{ background: {PRIMARY}; border-color: {PRIMARY}; }}

QTabWidget::pane {{ border: none; border-top: 1px solid {BORDER}; }}
QTabBar::tab {{
    background: transparent; color: {MUTED}; padding: 6px 14px;
    border-bottom: 2px solid transparent; font-weight: 600;
}}
QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {GREEN}; }}

QLabel#rangeValue {{
    background: {INPUT}; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 4px 6px; min-width: 62px;
    font-family: "JetBrains Mono", "DejaVu Sans Mono", monospace;
}}

QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #2A3441; border-radius: 3px; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QStatusBar {{ background: {BG}; border-top: 1px solid {BORDER}; color: {MUTED}; }}
QStatusBar QLabel {{ color: {MUTED}; padding: 0 10px; }}
"""
