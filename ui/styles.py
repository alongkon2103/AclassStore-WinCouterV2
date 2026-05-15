# ── theme ──────────────────────────────────────────────────────────────────────
BG = "#070B13"; CARD = "#0E1420"; SURFACE = "#182132"
ACCENT = "#5499E8"; ACCENT_H = "#70AEEF"; ACCENT_D = "#3D7AC0"
TEXT = "#F8FAFC"; MUTED = "#8295AD"; BORDER = "#1E2A3F"
SUCCESS = "#10B981"; WARN = "#F59E0B"; DANGER = "#EF4444"
PURPLE = "#8B5CF6"; PURPLE_H = "#A78BFA"

# ── stylesheet ─────────────────────────────────────────────────────────────────
def stylesheet() -> str:
    return f"""
QMainWindow,QWidget{{
  background-color:{BG};color:{TEXT};
  font-family:'Segoe UI','SF Pro Text','Helvetica Neue',sans-serif;font-size:12px;
}}
QGroupBox{{
  background-color:{CARD};border:1px solid {BORDER};border-radius:8px;
  margin-top:14px;padding:14px 12px 10px 12px;
  color:{MUTED};font-weight:bold;font-size:10px;letter-spacing:0.8px;text-transform:uppercase;
}}
QGroupBox::title{{subcontrol-origin:margin;left:10px;padding:0 6px;background:{CARD};}}
QPushButton{{
  background-color:{SURFACE};color:{TEXT};border:1px solid {BORDER};
  border-radius:5px;padding:6px 14px;font-size:12px;
}}
QPushButton:hover{{border-color:{MUTED};background-color:#1e2d42;}}
QPushButton:pressed{{background-color:{CARD};}}
QPushButton#btn_win_plus{{
  background-color:{ACCENT};border:none;color:#FFF;font-weight:700;font-size:15px;border-radius:6px;
}}
QPushButton#btn_win_plus:hover{{background-color:{ACCENT_H};}}
QPushButton#btn_win_plus:pressed{{background-color:{ACCENT_D};}}
QPushButton#btn_spin{{
  background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6d28d9,stop:1 #a855f7);
  border:none;color:#FFF;font-weight:900;font-size:15px;border-radius:6px;letter-spacing:1px;
}}
QPushButton#btn_spin:hover{{
  background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c3aed,stop:1 #c084fc);
}}
QPushButton#btn_spin:pressed{{
  background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5b21b6,stop:1 #9333ea);
}}
QPushButton#btn_spin:disabled{{
  background:#2a1a4a;color:#6b46a0;
}}
QPushButton#btn_undo{{
  background-color:{SURFACE};color:{DANGER};border:1px solid #3a1a1a;font-weight:600;
}}
QPushButton#btn_undo:hover{{background-color:#2a1010;border-color:{DANGER};}}
QPushButton#btn_reset{{
  background-color:{SURFACE};color:{WARN};border:1px solid #3a2a10;font-weight:600;
}}
QPushButton#btn_reset:hover{{background-color:#2a1e08;border-color:{WARN};}}
QPushButton#btn_custom{{
  background-color:{SURFACE};color:{ACCENT_H};border:1px solid {BORDER};
  font-weight:700;font-size:13px;
}}
QPushButton#btn_custom:hover{{border-color:{ACCENT};background-color:#1e2d42;}}
QPushButton#btn_custom:pressed{{background-color:{ACCENT_D};color:#FFF;}}
QPushButton#btn_save{{border:1px solid {ACCENT};color:{ACCENT};font-weight:600;}}
QPushButton#btn_save:hover{{background-color:{ACCENT};color:#FFF;}}
QPushButton#btn_save_ok{{background-color:{SUCCESS};border:none;color:#FFF;font-weight:700;}}
QPushButton#btn_color{{
  border-radius:5px;min-width:28px;max-width:28px;min-height:28px;max-height:28px;
  border:1px solid {BORDER};padding:0;
}}
QPushButton#btn_color:hover{{border-color:{ACCENT_H};}}
QPushButton#chip_on{{
  background-color:{ACCENT};color:#FFF;border:none;border-radius:4px;
  padding:4px 14px;font-size:11px;font-weight:700;
}}
QPushButton#chip_off{{
  background-color:{SURFACE};color:{MUTED};border:1px solid {BORDER};
  border-radius:4px;padding:4px 14px;font-size:11px;
}}
QPushButton#chip_off:hover{{border-color:{ACCENT};color:{TEXT};}}
QPushButton#btn_key{{
  background-color:{SURFACE};color:{ACCENT_H};border:1px solid {BORDER};
  font-family:'Consolas','Menlo',monospace;font-size:11px;min-width:72px;
}}
QPushButton#btn_key_rec{{
  background-color:{ACCENT};color:#FFF;border:none;font-weight:700;font-size:11px;min-width:72px;
}}
QPushButton#btn_import{{
  background-color:{SURFACE};color:{PURPLE_H};border:1px solid {PURPLE};
  font-weight:600;border-radius:5px;padding:5px 14px;
}}
QPushButton#btn_import:hover{{background-color:#1e1530;border-color:{PURPLE_H};}}
QPushButton#btn_export{{
  background-color:{SURFACE};color:{ACCENT_H};border:1px solid {ACCENT};
  font-weight:600;border-radius:5px;padding:5px 14px;
}}
QPushButton#btn_export:hover{{background-color:{ACCENT};color:#FFF;}}
QSpinBox,QLineEdit,QFontComboBox,QComboBox{{
  background-color:{SURFACE};color:{TEXT};border:1px solid {BORDER};
  border-radius:5px;padding:5px 9px;font-size:12px;
  selection-background-color:{ACCENT};
}}
QSpinBox:focus,QLineEdit:focus,QFontComboBox:focus,QComboBox:focus{{border-color:{ACCENT};}}
QComboBox::drop-down{{border:none;width:20px;}}
QComboBox QAbstractItemView{{
  background-color:{SURFACE};color:{TEXT};border:1px solid {BORDER};
  selection-background-color:{ACCENT};
}}
QSpinBox::up-button,QSpinBox::down-button{{
  subcontrol-origin:border;width:16px;border:none;background:{CARD};
}}
QSpinBox::up-arrow,QSpinBox::down-arrow{{image:none;width:0;}}
QSlider::groove:horizontal{{height:4px;background:{BORDER};border-radius:2px;}}
QSlider::handle:horizontal{{
  background:{ACCENT};width:14px;height:14px;margin:-5px 0;
  border-radius:7px;border:2px solid {ACCENT_D};
}}
QSlider::handle:horizontal:hover{{background:{ACCENT_H};}}
QSlider::sub-page:horizontal{{background:{ACCENT};border-radius:2px;}}
QCheckBox{{color:{TEXT};spacing:8px;font-size:12px;}}
QCheckBox::indicator{{width:16px;height:16px;border-radius:4px;border:1px solid {BORDER};background:{SURFACE};}}
QCheckBox::indicator:checked{{background-color:{ACCENT};border-color:{ACCENT};}}
QLabel{{color:{MUTED};}}
QScrollArea{{border:none;background:transparent;}}
QScrollBar:vertical{{background:transparent;width:5px;margin:0;}}
QScrollBar::handle:vertical{{background:{BORDER};border-radius:3px;min-height:24px;}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
"""
