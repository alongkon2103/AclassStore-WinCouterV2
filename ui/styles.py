# ── theme ──────────────────────────────────────────────────────────────────────
# Modern Dark (Slate Palette - comfortable for eyes)
BG = "#0F172A"; CARD = "#1E293B"; SURFACE = "#334155"
ACCENT = "#3B82F6"; ACCENT_H = "#60A5FA"; ACCENT_D = "#2563EB"
TEXT = "#F8FAFC"; MUTED = "#94A3B8"; BORDER = "#334155"
SUCCESS = "#10B981"; WARN = "#F59E0B"; DANGER = "#EF4444"
PURPLE = "#8B5CF6"; PURPLE_H = "#A78BFA"

# ── stylesheet ─────────────────────────────────────────────────────────────────
def stylesheet() -> str:
    return f"""
QMainWindow, QWidget{{
  background-color: {BG}; color: {TEXT};
  font-family: 'Inter', 'Segoe UI', 'SF Pro Text', sans-serif; font-size: 13px;
}}
QGroupBox {{
  background-color: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
  margin-top: 16px; padding: 20px 16px 12px 16px;
  color: {MUTED}; font-weight: 700; font-size: 11px; letter-spacing: 0.5px; text-transform: uppercase;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 8px; background: {CARD}; }}
QPushButton {{
  background-color: {SURFACE}; color: {TEXT}; border: 1px solid {BORDER};
  border-radius: 10px; padding: 8px 16px; font-size: 13px; font-weight: 500;
}}
QPushButton:hover {{ background-color: {BORDER}; border-color: {MUTED}; }}
QPushButton:pressed {{ background-color: {SURFACE}; }}
QPushButton#btn_win_plus {{
  background-color: {ACCENT}; border: none; color: #FFF; font-weight: 700; font-size: 16px; border-radius: 10px;
}}
QPushButton#btn_win_plus:hover {{ background-color: {ACCENT_H}; }}
QPushButton#btn_win_plus:pressed {{ background-color: {ACCENT_D}; }}
QPushButton#btn_spin {{
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {PURPLE}, stop:1 {PURPLE_H});
  border: none; color: #FFF; font-weight: 800; font-size: 16px; border-radius: 10px; letter-spacing: 1px;
}}
QPushButton#btn_spin:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {PURPLE_H}, stop:1 #C4B5FD); }}
QPushButton#btn_spin:pressed {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 {PURPLE}); }}
QPushButton#btn_spin:disabled {{ background: #1E293B; color: #475569; }}
QPushButton#btn_undo {{ background-color: rgba(239, 68, 68, 0.1); color: {DANGER}; border: 1px solid rgba(239, 68, 68, 0.2); }}
QPushButton#btn_undo:hover {{ background-color: rgba(239, 68, 68, 0.2); border-color: {DANGER}; }}
QPushButton#btn_reset {{ background-color: rgba(245, 158, 11, 0.1); color: {WARN}; border: 1px solid rgba(245, 158, 11, 0.2); }}
QPushButton#btn_reset:hover {{ background-color: rgba(245, 158, 11, 0.2); border-color: {WARN}; }}
QPushButton#btn_custom {{ background-color: rgba(59, 130, 246, 0.1); color: {ACCENT}; border: 1px solid rgba(59, 130, 246, 0.2); }}
QPushButton#btn_custom:hover {{ background-color: rgba(59, 130, 246, 0.2); border-color: {ACCENT}; }}
QPushButton#btn_save {{ background-color: {ACCENT}; color: #FFF; border: none; font-weight: 700; }}
QPushButton#btn_save:hover {{ background-color: {ACCENT_H}; }}
QPushButton#btn_save_ok {{ background-color: {SUCCESS}; border: none; color: #FFF; font-weight: 700; }}
QSpinBox, QLineEdit, QFontComboBox, QComboBox {{
  background-color: {BG}; color: {TEXT}; border: 1px solid {BORDER};
  border-radius: 8px; padding: 7px 12px; font-size: 13px;
  selection-background-color: {ACCENT};
}}
QSpinBox:focus, QLineEdit:focus, QFontComboBox:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down, QFontComboBox::drop-down {{ border: none; width: 30px; }}
QComboBox::down-arrow, QFontComboBox::down-arrow {{
  image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM5NEEzQjgiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJtNiA5IDYgNiA2LTYiLz48L3N2Zz4=");
  width: 14px; height: 14px;
}}
QComboBox QAbstractItemView, QFontComboBox QAbstractItemView{{
  background-color: {CARD}; color: {TEXT}; border: 1px solid {BORDER};
  selection-background-color: {ACCENT};
}}
QCheckBox {{ color: {TEXT}; spacing: 10px; font-size: 13px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 6px; border: 1px solid {BORDER}; background: {BG}; }}
QCheckBox::indicator:checked {{ background-color: {ACCENT}; border-color: {ACCENT}; image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTUgMTJsNSA1TDIwIDciLz48L3N2Zz4="); }}
QLabel {{ color: {MUTED}; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {SURFACE}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
