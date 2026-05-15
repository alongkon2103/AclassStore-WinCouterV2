import json
import random
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QSpinBox, QColorDialog, QGroupBox,
    QLineEdit, QFontComboBox, QCheckBox, QGridLayout, QScrollArea, QFrame,
    QSizePolicy, QComboBox, QFileDialog, QMessageBox, QRadioButton,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QColor, QPalette, QKeySequence

from core.state import state, save_settings, parse_choices, PRESET_KEYS, get_base_dir
from core.hotkeys import hotkey_manager
from ui.styles import (
    BG, CARD, SURFACE, ACCENT, ACCENT_H, ACCENT_D,
    TEXT, MUTED, BORDER, SUCCESS, WARN, DANGER,
    PURPLE, PURPLE_H, stylesheet
)

# ── helper widgets ─────────────────────────────────────────────────────────────
class KeyCaptureButton(QPushButton):
    key_captured = pyqtSignal(str)

    def __init__(self, key_str="", parent=None):
        super().__init__(parent)
        self.recording    = False
        self.current_key  = key_str
        self._show(key_str)
        self.clicked.connect(self._start)
        self.setFocusPolicy(Qt.StrongFocus)

    def _show(self, key_str):
        self.current_key = key_str
        self.setText(f"[ {key_str or chr(8212)} ]")
        self.setObjectName("btn_key")
        self._repoll()

    def _repoll(self):
        self.setStyleSheet("")
        self.style().unpolish(self)
        self.style().polish(self)

    def _start(self):
        self.recording = True
        self.setText("Press key…")
        self.setObjectName("btn_key_rec")
        self._repoll()
        self.setFocus()

    def event(self, e):
        if self.recording and e.type() == QEvent.KeyPress:
            self._handle_key_event(e)
            return True
        return super().event(e)

    def _handle_key_event(self, event):
        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt,
                   Qt.Key_Meta, Qt.Key_Super_L, Qt.Key_Super_R, Qt.Key_unknown):
            return
        key_str = QKeySequence(key).toString()
        if not key_str:
            key_str = event.text().upper()
        if not key_str:
            return
        self.recording = False
        self._show(key_str)
        self.key_captured.emit(key_str)
        event.accept()

    def focusOutEvent(self, event):
        if self.recording:
            self.recording = False
            self._show(self.current_key)
        super().focusOutEvent(event)

def rl(text, w=80):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{TEXT};font-size:12px;")
    lbl.setMinimumWidth(w)
    return lbl

def mk_chk(text, checked, slot):
    c = QCheckBox(text)
    c.setChecked(checked)
    c.stateChanged.connect(slot)
    return c

class ColorButton(QPushButton):
    color_changed = pyqtSignal(str)

    def __init__(self, hex_color="#ffffff", parent=None):
        super().__init__(parent)
        self.setObjectName("btn_color")
        self.hex_color = hex_color
        self._apply()
        self.clicked.connect(self._pick)

    def _apply(self):
        self.setStyleSheet(
            f"QPushButton#btn_color{{background-color:{self.hex_color};}}"
            f"QPushButton#btn_color:hover{{border:2px solid {ACCENT_H};}}"
        )

    def _pick(self):
        c = QColorDialog.getColor(QColor(self.hex_color), self, "Pick Color",
                                  QColorDialog.ShowAlphaChannel)
        if c.isValid():
            self.hex_color = c.name()
            self._apply()
            self.color_changed.emit(self.hex_color)

    def set_color(self, hex_color):
        self.hex_color = hex_color
        self._apply()

class ChipButton(QPushButton):
    def __init__(self, text, active=False, parent=None):
        super().__init__(text, parent)
        self.set_active(active)

    def set_active(self, active):
        self.setObjectName("chip_on" if active else "chip_off")
        self.setStyleSheet("")
        self.style().unpolish(self)
        self.style().polish(self)

# ── main window ────────────────────────────────────────────────────────────────
class WinCounter(QMainWindow):
    sig_plus  = pyqtSignal()
    sig_minus = pyqtSignal()
    sig_reset = pyqtSignal()
    sig_c1    = pyqtSignal()
    sig_c2    = pyqtSignal()
    sig_c3    = pyqtSignal()
    sig_spin  = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Win Counter — Powered by A Class Store")
        self.setMinimumSize(800, 540)
        self.setStyleSheet(stylesheet())

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._auto_save)

        self.sig_plus.connect(lambda: self.win_add(1))
        self.sig_minus.connect(lambda: self.win_add(-1))
        self.sig_reset.connect(self.win_reset)
        self.sig_c1.connect(lambda: self.win_add(state["custom_btn1_val"]))
        self.sig_c2.connect(lambda: self.win_add(state["custom_btn2_val"]))
        self.sig_c3.connect(lambda: self.win_add(state["custom_btn3_val"]))
        self.sig_spin.connect(self.do_spin)

        self.setup_ui()
        self.refresh_display()
        self._start_hotkeys()

    def _start_hotkeys(self):
        hotkey_manager.start({
            'plus':  lambda: self.sig_plus.emit(),
            'minus': lambda: self.sig_minus.emit(),
            'reset': lambda: self.sig_reset.emit(),
            'c1':    lambda: self.sig_c1.emit(),
            'c2':    lambda: self.sig_c2.emit(),
            'c3':    lambda: self.sig_c3.emit(),
            'spin':  lambda: self.sig_spin.emit(),
        })

    def do_spin(self):
        # 1. ป้องกันการกดซ้ำระหว่างหมุน
        self.btn_spin.setEnabled(False)
        self.btn_spin.setText("⌛ SPINNING...")

        # 2. สุ่มผลลัพธ์
        pool = parse_choices(state.get("spin_choices", "0"))
        result = random.choice(pool)
        
        # 3. ส่งข้อมูลไปที่ Overlay (เพิ่ม seq เพื่อเริ่มหมุน) 
        state["spin_result"] = result
        state["spin_seq"] = state.get("spin_seq", 0) + 1
        
        # 4. ตั้ง Timer ให้รอจนกว่า Animation จะจบ
        QTimer.singleShot(3850, lambda: self.apply_spin_result(result))

    def apply_spin_result(self, result):
        """ ฟังก์ชันนี้จะถูกเรียกหลังจากหมุนเสร็จแล้ว """
        new_val = state["wins"] + result
        
        if state.get("allow_negative", False):
            new_val = min(new_val, state["max_wins"])
        else:
            new_val = max(0, min(new_val, state["max_wins"]))

        state["wins"] = new_val
        self.refresh_display()
        save_settings()
        
        self.btn_spin.setEnabled(True)
        self.btn_spin.setText("🎲  SPIN!")
        print(f"[Spin Completed] result={result} total_wins={new_val}")

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # header
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet(f"background:{CARD};border-bottom:1px solid {BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 0, 18, 0)
        hl.setSpacing(10)

        ttl = QLabel("🏆  WIN COUNTER — A Class Store")
        ttl.setStyleSheet(f"color:{TEXT};font-size:12px;font-weight:800;letter-spacing:2px;")
        hl.addWidget(ttl)
        hl.addStretch()

        live = QLabel("● LIVE")
        live.setStyleSheet(f"color:{SUCCESS};font-size:10px;font-weight:700;letter-spacing:1px;")
        hl.addWidget(live)

        for url, color, label in [
            ("http://localhost:5000/overlay", ACCENT_H, "Overlay"),
            ("http://localhost:5000/spin",    PURPLE_H, "Spin"),
        ]:
            url_lbl = QLabel(url)
            url_lbl.setStyleSheet(
                f"color:{color};font-size:10px;font-family:'Consolas','Menlo',monospace;"
                f"background:{SURFACE};border:1px solid {BORDER};border-radius:4px;padding:2px 8px;"
            )
            url_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            hl.addWidget(url_lbl)
            cp = QPushButton(f"Copy {label}")
            cp.setFixedHeight(26)
            _url = url
            cp.clicked.connect(lambda _, u=_url: QApplication.clipboard().setText(u))
            hl.addWidget(cp)

        root.addWidget(header)

        # scroll body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget()
        body.setStyleSheet("background:transparent;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(18, 18, 18, 14)
        bl.setSpacing(14)

        # control buttons
        ctrl = QVBoxLayout()
        ctrl.setSpacing(8)

        self.btn_plus = QPushButton("WIN  +1")
        self.btn_plus.setObjectName("btn_win_plus")
        self.btn_plus.setMinimumHeight(54)
        self.btn_plus.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_plus.clicked.connect(lambda: self.win_add(1))
        ctrl.addWidget(self.btn_plus)

        self.btn_spin = QPushButton("🎲  SPIN!")
        self.btn_spin.setObjectName("btn_spin")
        self.btn_spin.setMinimumHeight(46)
        self.btn_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_spin.clicked.connect(self.do_spin)
        ctrl.addWidget(self.btn_spin)

        under = QHBoxLayout()
        under.setSpacing(8)
        self.btn_minus = QPushButton("UNDO  −1")
        self.btn_minus.setObjectName("btn_undo")
        self.btn_minus.setMinimumHeight(36)
        self.btn_minus.clicked.connect(lambda: self.win_add(-1))
        self.btn_reset_ui = QPushButton("↺  RESET")
        self.btn_reset_ui.setObjectName("btn_reset")
        self.btn_reset_ui.setMinimumHeight(36)
        self.btn_reset_ui.clicked.connect(self.win_reset)
        under.addWidget(self.btn_minus)
        under.addWidget(self.btn_reset_ui)
        ctrl.addLayout(under)

        cust = QHBoxLayout()
        cust.setSpacing(8)
        self.btn_c1 = self._make_custom_btn(1)
        self.btn_c2 = self._make_custom_btn(2)
        self.btn_c3 = self._make_custom_btn(3)
        cust.addWidget(self.btn_c1)
        cust.addWidget(self.btn_c2)
        cust.addWidget(self.btn_c3)
        ctrl.addLayout(cust)

        hints = QHBoxLayout()
        hints.setSpacing(0)
        self.lbl_h = {}
        for k, label in [
            ("key_win_plus", "+1"), ("key_win_minus", "−1"), ("key_reset", "↺"),
            ("key_custom1", "C1"), ("key_custom2", "C2"), ("key_custom3", "C3"),
            ("key_spin", "🎲"),
        ]:
            lbl = QLabel(f"[{state[k]}] {label}")
            lbl.setStyleSheet(f"color:{MUTED};font-size:10px;")
            lbl.setAlignment(Qt.AlignCenter)
            hints.addWidget(lbl)
            self.lbl_h[k] = lbl
        ctrl.addLayout(hints)
        bl.addLayout(ctrl)

        # settings columns
        cols = QHBoxLayout()
        cols.setSpacing(14)
        left  = QVBoxLayout(); left.setSpacing(10)
        right = QVBoxLayout(); right.setSpacing(10)

        self._section_counter(left)
        self._section_font(left)
        self._section_colors(left)
        self._section_spin(left)
        left.addStretch()

        self._section_shortcuts(right)
        self._section_stroke(right)
        self._section_layout_obs(right)
        self._section_background(right)
        right.addStretch()

        cols.addLayout(left,  stretch=1)
        cols.addLayout(right, stretch=1)
        bl.addLayout(cols)

        # preset bar
        preset_grp = QGroupBox("Preset")
        preset_lay = QHBoxLayout(preset_grp)
        preset_lay.setSpacing(10)
        desc = QLabel("Import/Export settings as .json file")
        desc.setStyleSheet(f"color:{MUTED};font-size:11px;")
        preset_lay.addWidget(desc)
        preset_lay.addStretch()
        self.btn_import = QPushButton("Import Preset")
        self.btn_import.setObjectName("btn_import")
        self.btn_import.setFixedHeight(32)
        self.btn_import.clicked.connect(self._import_preset)
        preset_lay.addWidget(self.btn_import)
        self.btn_export = QPushButton("Export Preset")
        self.btn_export.setObjectName("btn_export")
        self.btn_export.setFixedHeight(32)
        self.btn_export.clicked.connect(self._export_preset)
        preset_lay.addWidget(self.btn_export)
        bl.addWidget(preset_grp)

        # save bar
        save_row = QHBoxLayout()
        self.lbl_save = QLabel("Settings saved")
        self.lbl_save.setStyleSheet(f"color:{MUTED};font-size:11px;")
        save_row.addWidget(self.lbl_save)
        save_row.addStretch()
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setFixedHeight(32)
        self.btn_save.clicked.connect(self._manual_save)
        save_row.addWidget(self.btn_save)
        bl.addLayout(save_row)

        footer = QLabel("Powered by <b>A Class</b> <span style='color:#5499E8;'>Store</span>")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size:10px;color:#2e4060;margin-top:4px;border:none;")
        bl.addWidget(footer)

        scroll.setWidget(body)
        root.addWidget(scroll)

    def _section_spin(self, parent):
        grp = QGroupBox("Spin Wheel")
        grp.setStyleSheet(
            f"QGroupBox{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 #120c2a,stop:1 {CARD});"
            f"border:1px solid {PURPLE};border-radius:10px;"
            f"margin-top:14px;padding:16px 14px 12px 14px;"
            f"color:{PURPLE_H};font-weight:900;font-size:11px;letter-spacing:1px;}}"
            f"QGroupBox::title{{subcontrol-origin:margin;left:10px;"
            f"padding:0 8px;background:#120c2a;color:{PURPLE_H};}}"
        )
        lay = QVBoxLayout(grp)
        lay.setSpacing(10)

        lbl_choices = QLabel("Spin Choices  (คั่นด้วย , เช่น   1,-5,-3,-4,5,10,6)")
        lbl_choices.setStyleSheet(f"color:{TEXT};font-size:11px;font-weight:600;")
        lay.addWidget(lbl_choices)

        self.edit_choices = QLineEdit(state.get("spin_choices", "1,-5,-3,-4,5,10,6"))
        self.edit_choices.setPlaceholderText("e.g.  1,-5,-3,-4,5,10,6")
        self.edit_choices.setStyleSheet(
            f"QLineEdit{{background:#0d0820;border:1px solid {PURPLE};"
            f"border-radius:7px;padding:7px 12px;font-size:13px;"
            f"color:{PURPLE_H};letter-spacing:1px;font-family:'Consolas','Menlo',monospace;}}"
            f"QLineEdit:focus{{border-color:#c084fc;background:#120c2a;}}"
        )
        self.edit_choices.textChanged.connect(self._on_choices_changed)
        lay.addWidget(self.edit_choices)

        self.pool_preview_layout = QHBoxLayout()
        self.pool_preview_layout.setSpacing(5)
        self.pool_preview_layout.setAlignment(Qt.AlignLeft)
        lay.addLayout(self.pool_preview_layout)
        self._refresh_pool_preview()

        hint = QLabel(
            "✦  ใส่ตัวเลขคั่นด้วย comma  |  ค่าบวก = UP  |  ค่าลบ = DOWN  |  0 = ZERO"
        )
        hint.setStyleSheet(f"color:{MUTED};font-size:10px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        lay.addSpacing(5)
        lay.addWidget(rl("Template (รูปแบบสปิน):", w=150))
        row_tpl = QHBoxLayout()
        self.rdo_tpl1 = QRadioButton("Template 1")
        self.rdo_tpl2 = QRadioButton("Template 2")
        self.rdo_tpl3 = QRadioButton("Template 3")
        
        tpl_val = state.get("spin_template", 1)
        if tpl_val == 2: self.rdo_tpl2.setChecked(True)
        elif tpl_val == 3: self.rdo_tpl3.setChecked(True)
        else: self.rdo_tpl1.setChecked(True)

        self.rdo_tpl1.toggled.connect(lambda v: v and self._us("spin_template", 1))
        self.rdo_tpl2.toggled.connect(lambda v: v and self._us("spin_template", 2))
        self.rdo_tpl3.toggled.connect(lambda v: v and self._us("spin_template", 3))

        for r in [self.rdo_tpl1, self.rdo_tpl2, self.rdo_tpl3]:
            r.setStyleSheet(f"color:{TEXT};font-size:11px;font-weight:bold;margin-right:8px;")
            row_tpl.addWidget(r)
        row_tpl.addStretch()
        lay.addLayout(row_tpl)

        parent.addWidget(grp)

    def _on_choices_changed(self, text: str):
        state["spin_choices"] = text
        self._refresh_pool_preview()
        self._mark_dirty()

    def _refresh_pool_preview(self):
        while self.pool_preview_layout.count():
            item = self.pool_preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pool = parse_choices(state.get("spin_choices", "0"))
        for v in pool:
            chip = QLabel(f"{'+' if v > 0 else ''}{v}")
            if v > 0:
                chip.setStyleSheet(
                    f"color:#c084fc;background:rgba(109,40,217,0.25);"
                    f"border:1px solid rgba(168,85,247,0.4);border-radius:6px;"
                    f"padding:3px 10px;font-family:'Consolas',monospace;font-size:12px;font-weight:700;"
                )
            elif v < 0:
                chip.setStyleSheet(
                    f"color:#f87171;background:rgba(153,27,27,0.25);"
                    f"border:1px solid rgba(239,68,68,0.4);border-radius:6px;"
                    f"padding:3px 10px;font-family:'Consolas',monospace;font-size:12px;font-weight:700;"
                )
            else:
                chip.setStyleSheet(
                    f"color:#94a3b8;background:rgba(30,41,59,0.5);"
                    f"border:1px solid rgba(100,116,139,0.3);border-radius:6px;"
                    f"padding:3px 10px;font-family:'Consolas',monospace;font-size:12px;font-weight:700;"
                )
            self.pool_preview_layout.addWidget(chip)

    def _import_preset(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Preset File", str(get_base_dir()), "JSON Preset (*.json);;All Files (*)")
        if not path: return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Cannot read file:\n{e}")
            return
        valid_keys = [k for k in data if k in PRESET_KEYS]
        if not valid_keys:
            QMessageBox.warning(self, "Invalid File", "No recognized keys found in preset.")
            return
        for k in valid_keys:
            state[k] = data[k]
        save_settings()
        self._rebuild_ui()

    def _export_preset(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", str(get_base_dir() / "my_preset.json"),
            "JSON Preset (*.json);;All Files (*)")
        if not path: return
        export_data = {k: v for k, v in state.items() if k in PRESET_KEYS}
        try:
            Path(path).write_text(
                json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")
            QMessageBox.information(self, "Exported", f"Saved preset to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def _rebuild_ui(self):
        new_win = WinCounter()
        new_win.resize(self.width(), self.height())
        new_win.show()
        QApplication.instance()._main_win = new_win
        self.close()

    def _make_custom_btn(self, idx):
        val = state[f"custom_btn{idx}_val"]
        btn = QPushButton(f"{val:+d}")
        btn.setObjectName("btn_custom")
        btn.setMinimumHeight(32)
        sig = [self.sig_c1, self.sig_c2, self.sig_c3][idx - 1]
        btn.clicked.connect(sig.emit)
        return btn

    def _refresh_custom_btn(self, idx):
        getattr(self, f"btn_c{idx}").setText(f"{state[f'custom_btn{idx}_val']:+d}")

    def _section_counter(self, parent):
        grp = QGroupBox("Counter")
        g = QGridLayout(grp)
        g.setSpacing(8)
        g.setColumnStretch(1, 1)

        g.addWidget(rl("Max Wins"), 0, 0)
        self.spin_max = QSpinBox()
        self.spin_max.setRange(1, 9999)
        self.spin_max.setValue(state["max_wins"])
        self.spin_max.valueChanged.connect(lambda v: self._us("max_wins", v))
        g.addWidget(self.spin_max, 0, 1)

        g.addWidget(rl("Label"), 1, 0)
        self.edit_label = QLineEdit(state["label_win"])
        self.edit_label.textChanged.connect(lambda v: self._us("label_win", v))
        g.addWidget(self.edit_label, 1, 1)

        g.addWidget(rl("Separator"), 2, 0)
        self.edit_sep = QLineEdit(state["separator"])
        self.edit_sep.textChanged.connect(lambda v: self._us("separator", v))
        g.addWidget(self.edit_sep, 2, 1)

        chk_row = QHBoxLayout()
        chk_row.addWidget(mk_chk("Show Max",   state["show_max"],   lambda v: self._us("show_max",   bool(v))))
        chk_row.addWidget(mk_chk("Show Label", state["show_label"], lambda v: self._us("show_label", bool(v))))
        chk_row.addStretch()
        g.addLayout(chk_row, 3, 0, 1, 2)

        parent.addWidget(grp)

    def _section_font(self, parent):
        grp = QGroupBox("Typography")
        g = QGridLayout(grp)
        g.setSpacing(8)
        g.setColumnStretch(1, 1)

        g.addWidget(rl("Font"), 0, 0)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(state["font_family"]))
        self.font_combo.currentFontChanged.connect(lambda f: self._us("font_family", f.family()))
        g.addWidget(self.font_combo, 0, 1)

        g.addWidget(rl("Size"), 1, 0)
        sz_row = QHBoxLayout()
        self.spin_size = QSpinBox()
        self.spin_size.setRange(12, 300)
        self.spin_size.setValue(state["font_size"])
        self.spin_size.valueChanged.connect(lambda v: self._us("font_size", v))
        sz_row.addWidget(self.spin_size)
        sz_row.addWidget(mk_chk("Bold", state["font_bold"], lambda v: self._us("font_bold", bool(v))))
        sz_row.addStretch()
        g.addLayout(sz_row, 1, 1)

        parent.addWidget(grp)

    def _section_colors(self, parent):
        grp = QGroupBox("Colors")
        g = QGridLayout(grp)
        g.setSpacing(10)

        for col, (label, key) in enumerate([
            ("Win",      "color_win"),
            ("Lose/Max", "color_lose"),
            ("Label",    "color_label"),
            ("Negative", "color_negative"),
        ]):
            g.addWidget(rl(label, w=50), 0, col, Qt.AlignCenter)
            cb = ColorButton(state[key])
            cb.color_changed.connect(lambda c, k=key: self._us(k, c))
            g.addWidget(cb, 1, col, Qt.AlignCenter)

        chk_neg = mk_chk("Allow negative wins", state.get("allow_negative", False),
                          lambda v: self._us("allow_negative", bool(v)))
        chk_neg.setStyleSheet(f"color:{TEXT};font-size:11px;margin-top:4px;")
        g.addWidget(chk_neg, 2, 0, 1, 4)

        parent.addWidget(grp)

    def _section_shortcuts(self, parent):
        grp = QGroupBox("Hotkeys & Custom Steps")
        g = QGridLayout(grp)
        g.setSpacing(7)

        for col, txt in [(1, "Key"), (2, "Step")]:
            lbl = QLabel(txt)
            lbl.setStyleSheet(f"color:{MUTED};font-size:10px;font-weight:bold;")
            g.addWidget(lbl, 0, col)

        self._key_row(g, "WIN (+1)", "key_win_plus", 1, None)
        self._key_row(g, "UNDO (−1)", "key_win_minus", 2, None)
        self._key_row(g, "RESET",     "key_reset",     3, None)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{BORDER};")
        g.addWidget(sep, 4, 0, 1, 3)

        self._key_row(g, "Custom 1", "key_custom1", 5, 1)
        self._key_row(g, "Custom 2", "key_custom2", 6, 2)
        self._key_row(g, "Custom 3", "key_custom3", 7, 3)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color:{PURPLE};")
        g.addWidget(sep2, 8, 0, 1, 3)

        g.addWidget(rl("🎲 SPIN", w=65), 9, 0)
        btn_spin_key = KeyCaptureButton(state.get("key_spin", "F7"))
        btn_spin_key.key_captured.connect(lambda key: self._on_key_captured("key_spin", key))
        g.addWidget(btn_spin_key, 9, 1)

        parent.addWidget(grp)

    def _key_row(self, grid, label, state_key, row, custom_idx):
        grid.addWidget(rl(label, w=65), row, 0)
        btn = KeyCaptureButton(state[state_key])
        btn.key_captured.connect(lambda key, k=state_key: self._on_key_captured(k, key))
        grid.addWidget(btn, row, 1)
        if custom_idx is not None:
            sp = QSpinBox()
            sp.setRange(-999, 999)
            sp.setValue(state[f"custom_btn{custom_idx}_val"])
            sp.setMaximumWidth(62)
            sp.valueChanged.connect(lambda v, i=custom_idx: self._on_custom_val_changed(i, v))
            grid.addWidget(sp, row, 2)

    def _on_key_captured(self, state_key, key):
        state[state_key] = key
        _sfx = {
            "key_win_plus": "+1", "key_win_minus": "−1", "key_reset": "↺",
            "key_custom1": "C1", "key_custom2": "C2", "key_custom3": "C3",
            "key_spin": "🎲",
        }
        for k, lbl in self.lbl_h.items():
            lbl.setText(f"[{state[k]}] {_sfx[k]}")
        self._mark_dirty()

    def _on_custom_val_changed(self, idx, val):
        state[f"custom_btn{idx}_val"] = val
        self._refresh_custom_btn(idx)
        self._mark_dirty()

    def _section_stroke(self, parent):
        grp = QGroupBox("Text Outline / Stroke")
        g = QGridLayout(grp)
        g.setSpacing(8)
        g.setColumnStretch(1, 1)

        g.addWidget(mk_chk("Enable Outline", state["stroke"],
                            lambda v: self._us("stroke", bool(v))), 0, 0, 1, 3)

        g.addWidget(rl("Color"), 1, 0)
        sc_btn = ColorButton(state["stroke_color"])
        sc_btn.color_changed.connect(lambda c: self._us("stroke_color", c))
        g.addWidget(sc_btn, 1, 1)

        g.addWidget(rl("Size"), 2, 0)
        row_h = QHBoxLayout()
        self.slider_stroke = QSlider(Qt.Horizontal)
        self.slider_stroke.setRange(0, 8)
        self.slider_stroke.setValue(min(state["stroke_size"], 8))
        self.slider_stroke.valueChanged.connect(lambda v: self._us("stroke_size", v))
        self.lbl_stroke_val = QLabel(f"{state['stroke_size']}px")
        self.lbl_stroke_val.setStyleSheet(f"color:{TEXT};min-width:32px;")
        self.slider_stroke.valueChanged.connect(lambda v: self.lbl_stroke_val.setText(f"{v}px"))
        row_h.addWidget(self.slider_stroke)
        row_h.addWidget(self.lbl_stroke_val)
        g.addLayout(row_h, 2, 1)

        hint = QLabel("Max 8px — ป้องกันตัวหนังสือซ้อนกัน")
        hint.setStyleSheet(f"color:{MUTED};font-size:10px;")
        g.addWidget(hint, 3, 0, 1, 3)

        parent.addWidget(grp)

    def _section_layout_obs(self, parent):
        grp = QGroupBox("Overlay Layout")
        lay = QHBoxLayout(grp)
        self.chip_h = ChipButton("⟷  Horizontal", state["layout"] == "horizontal")
        self.chip_v = ChipButton("↕  Vertical",   state["layout"] == "vertical")
        self.chip_h.clicked.connect(lambda: self._set_layout("horizontal"))
        self.chip_v.clicked.connect(lambda: self._set_layout("vertical"))
        lay.addWidget(self.chip_h)
        lay.addWidget(self.chip_v)
        lay.addStretch()
        parent.addWidget(grp)

    def _section_background(self, parent):
        grp = QGroupBox("Overlay Background")
        g = QGridLayout(grp)
        g.setSpacing(8)
        g.setColumnStretch(1, 1)

        g.addWidget(rl("Opacity", w=80), 0, 0)
        row_op = QHBoxLayout()
        self.slider_bg_opacity = QSlider(Qt.Horizontal)
        self.slider_bg_opacity.setRange(0, 100)
        self.slider_bg_opacity.setValue(int(state.get("bg_opacity", 0)))
        self.lbl_bg_opacity = QLabel(f"{int(state.get('bg_opacity', 0))}%")
        self.lbl_bg_opacity.setStyleSheet(f"color:{TEXT};min-width:36px;")
        self.slider_bg_opacity.valueChanged.connect(self._on_bg_opacity_changed)
        row_op.addWidget(self.slider_bg_opacity)
        row_op.addWidget(self.lbl_bg_opacity)
        g.addLayout(row_op, 0, 1)

        g.addWidget(rl("Color 1", w=80), 1, 0)
        c1_row = QHBoxLayout()
        self.btn_bg_color = ColorButton(state.get("color_bg", "#000000"))
        self.btn_bg_color.color_changed.connect(lambda c: self._us("color_bg", c))
        c1_row.addWidget(self.btn_bg_color)
        c1_row.addStretch()
        g.addLayout(c1_row, 1, 1)

        self.chk_gradient = mk_chk("Enable Gradient", state.get("bg_gradient", False),
                                   self._on_gradient_toggled)
        g.addWidget(self.chk_gradient, 2, 0, 1, 2)

        self.lbl_bg_color2 = rl("Color 2", w=80)
        g.addWidget(self.lbl_bg_color2, 3, 0)
        c2_row = QHBoxLayout()
        self.btn_bg_color2 = ColorButton(state.get("color_bg2", "#1a1a2e"))
        self.btn_bg_color2.color_changed.connect(lambda c: self._us("color_bg2", c))
        c2_row.addWidget(self.btn_bg_color2)
        c2_row.addStretch()
        g.addLayout(c2_row, 3, 1)

        self.lbl_grad_dir = rl("Direction", w=80)
        g.addWidget(self.lbl_grad_dir, 4, 0)
        self.combo_grad_dir = QComboBox()
        for label, val in [
            ("→  Left → Right",   "to right"),
            ("←  Right → Left",   "to left"),
            ("↓  Top → Bottom",   "to bottom"),
            ("↑  Bottom → Top",   "to top"),
            ("↘  Diagonal ↘",     "to bottom right"),
            ("↗  Diagonal ↗",     "to top right"),
        ]:
            self.combo_grad_dir.addItem(label, val)
        cur_dir = state.get("bg_gradient_dir", "to right")
        for i in range(self.combo_grad_dir.count()):
            if self.combo_grad_dir.itemData(i) == cur_dir:
                self.combo_grad_dir.setCurrentIndex(i)
                break
        self.combo_grad_dir.currentIndexChanged.connect(
            lambda: self._us("bg_gradient_dir", self.combo_grad_dir.currentData()))
        g.addWidget(self.combo_grad_dir, 4, 1)

        g.addWidget(rl("Rounded", w=80), 5, 0)
        row_br = QHBoxLayout()
        self.slider_bg_radius = QSlider(Qt.Horizontal)
        self.slider_bg_radius.setRange(0, 60)
        self.slider_bg_radius.setValue(int(state.get("bg_border_radius", 14)))
        self.lbl_bg_radius = QLabel(f"{int(state.get('bg_border_radius', 14))}px")
        self.lbl_bg_radius.setStyleSheet(f"color:{TEXT};min-width:36px;")
        self.slider_bg_radius.valueChanged.connect(
            lambda v: (self._us("bg_border_radius", v), self.lbl_bg_radius.setText(f"{v}px")))
        row_br.addWidget(self.slider_bg_radius)
        row_br.addWidget(self.lbl_bg_radius)
        g.addLayout(row_br, 5, 1)

        g.addWidget(rl("Padding H", w=80), 6, 0)
        row_ph = QHBoxLayout()
        self.slider_bg_pad_h = QSlider(Qt.Horizontal)
        self.slider_bg_pad_h.setRange(0, 80)
        self.slider_bg_pad_h.setValue(int(state.get("bg_padding_h", 24)))
        self.lbl_bg_pad_h = QLabel(f"{int(state.get('bg_padding_h', 24))}px")
        self.lbl_bg_pad_h.setStyleSheet(f"color:{TEXT};min-width:36px;")
        self.slider_bg_pad_h.valueChanged.connect(
            lambda v: (self._us("bg_padding_h", v), self.lbl_bg_pad_h.setText(f"{v}px")))
        row_ph.addWidget(self.slider_bg_pad_h)
        row_ph.addWidget(self.lbl_bg_pad_h)
        g.addLayout(row_ph, 6, 1)

        g.addWidget(rl("Padding V", w=80), 7, 0)
        row_pv = QHBoxLayout()
        self.slider_bg_pad_v = QSlider(Qt.Horizontal)
        self.slider_bg_pad_v.setRange(0, 60)
        self.slider_bg_pad_v.setValue(int(state.get("bg_padding_v", 12)))
        self.lbl_bg_pad_v = QLabel(f"{int(state.get('bg_padding_v', 12))}px")
        self.lbl_bg_pad_v.setStyleSheet(f"color:{TEXT};min-width:36px;")
        self.slider_bg_pad_v.valueChanged.connect(
            lambda v: (self._us("bg_padding_v", v), self.lbl_bg_pad_v.setText(f"{v}px")))
        row_pv.addWidget(self.slider_bg_pad_v)
        row_pv.addWidget(self.lbl_bg_pad_v)
        g.addLayout(row_pv, 7, 1)

        parent.addWidget(grp)
        self._update_gradient_visibility()

    def _on_bg_opacity_changed(self, v):
        self.lbl_bg_opacity.setText(f"{v}%")
        self._us("bg_opacity", v)

    def _on_gradient_toggled(self, v):
        self._us("bg_gradient", bool(v))
        self._update_gradient_visibility()

    def _update_gradient_visibility(self):
        is_grad = state.get("bg_gradient", False)
        for w in [self.lbl_bg_color2, self.btn_bg_color2, self.lbl_grad_dir, self.combo_grad_dir]:
            w.setVisible(is_grad)

    def win_add(self, amount):
        new_val = state["wins"] + amount
        if state.get("allow_negative", False):
            new_val = min(new_val, state["max_wins"])
        else:
            new_val = max(0, min(new_val, state["max_wins"]))
        if new_val != state["wins"]:
            state["wins"] = new_val
            self.refresh_display()
            self._mark_dirty()

    def win_reset(self):
        state["wins"] = 0
        self.refresh_display()
        self._mark_dirty()

    def _set_layout(self, direction):
        state["layout"] = direction
        self.chip_h.set_active(direction == "horizontal")
        self.chip_v.set_active(direction == "vertical")
        self._mark_dirty()

    def _us(self, key, value):
        state[key] = value
        self.refresh_display()
        self._mark_dirty()

    def _mark_dirty(self):
        self.lbl_save.setText("● Unsaved changes")
        self.lbl_save.setStyleSheet(f"color:{WARN};font-size:11px;")
        self._save_timer.start(1500)

    def _auto_save(self):
        if save_settings():
            self._on_saved()

    def _manual_save(self):
        self._save_timer.stop()
        if save_settings():
            self._on_saved()

    def _on_saved(self):
        self.lbl_save.setText("✓  Saved")
        self.lbl_save.setStyleSheet(f"color:{SUCCESS};font-size:11px;")
        self.btn_save.setObjectName("btn_save_ok")
        self.btn_save.setText("✓  Saved")
        self._repoll_btn(self.btn_save)
        QTimer.singleShot(1800, self._reset_save_btn)

    def _reset_save_btn(self):
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setText("Save Settings")
        self._repoll_btn(self.btn_save)

    @staticmethod
    def _repoll_btn(btn):
        btn.setStyleSheet("")
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def refresh_display(self):
        self.btn_plus.setText(f"WIN  +1   [ {state['wins']} ]")

    def closeEvent(self, event):
        hotkey_manager.stop()
        save_settings()
        super().closeEvent(event)
