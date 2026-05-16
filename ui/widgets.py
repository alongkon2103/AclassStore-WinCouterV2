import json
import random
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QSpinBox, QColorDialog, QGroupBox,
    QLineEdit, QFontComboBox, QCheckBox, QGridLayout, QScrollArea, QFrame,
    QSizePolicy, QComboBox, QFileDialog, QMessageBox, QRadioButton,
    QBoxLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, QEvent
from PySide6.QtGui import QFont, QColor, QPalette, QKeySequence

from core.state import state, save_settings, parse_choices, PRESET_KEYS, get_base_dir
from core.hotkeys import hotkey_manager
from ui.styles import (
    BG, CARD, SURFACE, ACCENT, ACCENT_H, ACCENT_D,
    TEXT, MUTED, BORDER, SUCCESS, WARN, DANGER,
    PURPLE, PURPLE_H, stylesheet
)

# ── helper widgets ─────────────────────────────────────────────────────────────
class KeyCaptureButton(QPushButton):
    key_captured = Signal(str)

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
    color_changed = Signal(str)

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
    sig_plus  = Signal()
    sig_minus = Signal()
    sig_reset = Signal()
    sig_c1    = Signal()
    sig_c2    = Signal()
    sig_c3    = Signal()
    sig_spin  = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Win Counter — Powered by A Class Store")
        self.setMinimumSize(850, 600)
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
        self.btn_spin.setEnabled(False)
        self.btn_spin.setText("⌛ SPINNING...")
        pool = parse_choices(state.get("spin_choices", "0"))
        result = random.choice(pool)
        state["spin_result"] = result
        state["spin_seq"] = state.get("spin_seq", 0) + 1
        QTimer.singleShot(3850, lambda: self.apply_spin_result(result))

    def apply_spin_result(self, result):
        new_val = state["wins"] + result
        if not state.get("allow_negative", False):
            new_val = max(0, new_val)
        state["wins"] = new_val
        self.refresh_display()
        save_settings()
        self.btn_spin.setEnabled(True)
        self.btn_spin.setText("🎲  SPIN WHEEL!")

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet(f"background:{CARD}; border-bottom:1px solid {BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.setSpacing(12)

        ttl = QLabel("🏆 WIN COUNTER")
        ttl.setStyleSheet(f"color:{TEXT}; font-size:16px; font-weight:800; letter-spacing:1px;")
        hl.addWidget(ttl)
        
        brand = QLabel("A Class Store")
        brand.setStyleSheet(f"color:{ACCENT}; font-size:11px; font-weight:700; ")
        hl.addWidget(brand)
        hl.addStretch()

        for url, color, label in [
            ("http://localhost:5000/overlay", ACCENT, "Overlay"),
            ("http://localhost:5000/spin",    PURPLE, "Spin"),
        ]:
            cp = QPushButton(label)
            cp.setFixedWidth(90)
            cp.setFixedHeight(34)
            cp.setStyleSheet(f"background:{SURFACE}; color:{TEXT}; border:1px solid {BORDER}; font-size:12px; font-weight:600;")
            cp.clicked.connect(lambda _, u=url: QApplication.clipboard().setText(u))
            hl.addWidget(cp)

        root.addWidget(header)

        # Scrollable Body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget()
        body.setStyleSheet(f"background:{BG};")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(32, 32, 32, 32)
        bl.setSpacing(24)

        # Main Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.btn_plus = QPushButton("WIN  +1")
        self.btn_plus.setObjectName("btn_win_plus")
        self.btn_plus.setMinimumHeight(72)
        self.btn_plus.clicked.connect(lambda: self.win_add(1))
        ctrl.addWidget(self.btn_plus)

        self.btn_spin = QPushButton("🎲  SPIN WHEEL!")
        self.btn_spin.setObjectName("btn_spin")
        self.btn_spin.setMinimumHeight(60)
        self.btn_spin.clicked.connect(self.do_spin)
        ctrl.addWidget(self.btn_spin)

        under = QHBoxLayout()
        under.setSpacing(12)
        self.btn_minus = QPushButton("UNDO −1")
        self.btn_minus.setObjectName("btn_undo")
        self.btn_minus.setMinimumHeight(44)
        self.btn_minus.clicked.connect(lambda: self.win_add(-1))
        self.btn_reset_ui = QPushButton("↺ RESET")
        self.btn_reset_ui.setObjectName("btn_reset")
        self.btn_reset_ui.setMinimumHeight(44)
        self.btn_reset_ui.clicked.connect(self.win_reset)
        under.addWidget(self.btn_minus)
        under.addWidget(self.btn_reset_ui)
        ctrl.addLayout(under)

        cust = QHBoxLayout()
        cust.setSpacing(12)
        self.btn_c1 = self._make_custom_btn(1)
        self.btn_c2 = self._make_custom_btn(2)
        self.btn_c3 = self._make_custom_btn(3)
        for b in [self.btn_c1, self.btn_c2, self.btn_c3]:
            b.setMinimumHeight(40)
            cust.addWidget(b)
        ctrl.addLayout(cust)

        # Custom Win Adjuster
        adj = QHBoxLayout()
        adj.setSpacing(8)
        self.edit_custom_win = QLineEdit()
        self.edit_custom_win.setPlaceholderText("Custom Adjust (e.g. +10, -5)")
        self.edit_custom_win.setMinimumHeight(44)
        self.edit_custom_win.returnPressed.connect(self.apply_custom_win)
        self.btn_apply_custom = QPushButton("APPLY")
        self.btn_apply_custom.setStyleSheet("padding: 4px 12px; background:rgba(59, 130, 246, 0.1); border-radius:14px;")
        self.btn_apply_custom.setFixedWidth(120)
        self.btn_apply_custom.setMinimumHeight(44)
        self.btn_apply_custom.setObjectName("btn_save")
        self.btn_apply_custom.clicked.connect(self.apply_custom_win)
        adj.addWidget(self.edit_custom_win)
        adj.addWidget(self.btn_apply_custom)
        ctrl.addLayout(adj)

        hints = QHBoxLayout()
        hints.setSpacing(15)
        self.lbl_h = {}
        for k, label in [
            ("key_win_plus", "+1"), ("key_win_minus", "−1"), ("key_reset", "↺"),
            ("key_custom1", "C1"), ("key_custom2", "C2"), ("key_custom3", "C3"),
            ("key_spin", "🎲"),
        ]:
            lbl = QLabel(f"<span style='color:{MUTED};'>[{state[k]}]</span> {label}")
            lbl.setAlignment(Qt.AlignCenter)
            hints.addWidget(lbl)
            self.lbl_h[k] = lbl
        ctrl.addLayout(hints)
        bl.addLayout(ctrl)

        # Responsive Settings Container
        self.settings_pane = QWidget()
        self.settings_layout = QBoxLayout(QBoxLayout.LeftToRight, self.settings_pane)
        self.settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_layout.setSpacing(24)

        self.left_col = QWidget()
        self.left_lay = QVBoxLayout(self.left_col)
        self.left_lay.setContentsMargins(0, 0, 0, 0)
        self.left_lay.setSpacing(18)

        self.right_col = QWidget()
        self.right_lay = QVBoxLayout(self.right_col)
        self.right_lay.setContentsMargins(0, 0, 0, 0)
        self.right_lay.setSpacing(18)

        self._section_counter(self.left_lay)
        self._section_font(self.left_lay)
        self._section_colors(self.left_lay)
        self._section_spin(self.left_lay)
        self.left_lay.addStretch()

        self._section_shortcuts(self.right_lay)
        self._section_stroke(self.right_lay)
        self._section_layout_obs(self.right_lay)
        self._section_background(self.right_lay)
        self.right_lay.addStretch()

        self.settings_layout.addWidget(self.left_col, stretch=1)
        self.settings_layout.addWidget(self.right_col, stretch=1)
        bl.addWidget(self.settings_pane)

        # Preset & Save
        preset_grp = QGroupBox("Preset Management")
        preset_lay = QHBoxLayout(preset_grp)
        preset_lay.setSpacing(12)
        desc = QLabel("Backup or migrate settings via JSON.")
        desc.setStyleSheet(f"color:{MUTED}; font-size:12px;")
        preset_lay.addWidget(desc)
        preset_lay.addStretch()
        self.btn_import = QPushButton("Import")
        self.btn_import.setFixedHeight(36)
        self.btn_import.clicked.connect(self._import_preset)
        self.btn_export = QPushButton("Export")
        self.btn_export.setFixedHeight(36)
        self.btn_export.clicked.connect(self._export_preset)
        preset_lay.addWidget(self.btn_import)
        preset_lay.addWidget(self.btn_export)
        bl.addWidget(preset_grp)

        save_row = QHBoxLayout()
        self.lbl_save = QLabel("✓ Settings synchronized")
        self.lbl_save.setStyleSheet(f"color:{MUTED}; font-size:12px;")
        save_row.addWidget(self.lbl_save)
        save_row.addStretch()
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setMinimumHeight(44)
        self.btn_save.setFixedWidth(160)
        self.btn_save.clicked.connect(self._manual_save)
        save_row.addWidget(self.btn_save)
        bl.addLayout(save_row)

        footer = QLabel("<b>A Class</b> <span style='color:{ACCENT};'>Store</span> — Desktop Suite")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(f"font-size:11px; color:{MUTED}; margin-top:20px;")
        bl.addWidget(footer)

        scroll.setWidget(body)
        root.addWidget(scroll)

    def resizeEvent(self, event):
        if hasattr(self, 'settings_layout'):
            if self.width() < 850:
                if self.settings_layout.direction() != QBoxLayout.TopToBottom:
                    self.settings_layout.setDirection(QBoxLayout.TopToBottom)
            else:
                if self.settings_layout.direction() != QBoxLayout.LeftToRight:
                    self.settings_layout.setDirection(QBoxLayout.LeftToRight)
        super().resizeEvent(event)

    def _section_spin(self, parent):
        grp = QGroupBox("Spin Wheel Settings")
        lay = QVBoxLayout(grp)
        lay.setSpacing(12)

        lay.addWidget(rl("Choices (comma separated):", w=200))
        self.edit_choices = QLineEdit(state.get("spin_choices", "1,-5,-3,-4,5,10,6"))
        self.edit_choices.setPlaceholderText("e.g. 1,-5,10")
        self.edit_choices.textChanged.connect(self._on_choices_changed)
        lay.addWidget(self.edit_choices)

        self.pool_preview_layout = QHBoxLayout()
        self.pool_preview_layout.setSpacing(6)
        self.pool_preview_layout.setAlignment(Qt.AlignLeft)
        lay.addLayout(self.pool_preview_layout)
        self._refresh_pool_preview()

        lay.addWidget(rl("Template Selection:", w=200))
        row_tpl = QHBoxLayout()
        self.rdo_tpl1 = QRadioButton("T1")
        self.rdo_tpl2 = QRadioButton("T2")
        self.rdo_tpl3 = QRadioButton("T3")
        for r in [self.rdo_tpl1, self.rdo_tpl2, self.rdo_tpl3]:
            row_tpl.addWidget(r)
        
        tpl_val = state.get("spin_template", 1)
        if tpl_val == 2: self.rdo_tpl2.setChecked(True)
        elif tpl_val == 3: self.rdo_tpl3.setChecked(True)
        else: self.rdo_tpl1.setChecked(True)

        self.rdo_tpl1.toggled.connect(lambda v: v and self._us("spin_template", 1))
        self.rdo_tpl2.toggled.connect(lambda v: v and self._us("spin_template", 2))
        self.rdo_tpl3.toggled.connect(lambda v: v and self._us("spin_template", 3))
        lay.addLayout(row_tpl)
        parent.addWidget(grp)

    def _on_choices_changed(self, text: str):
        state["spin_choices"] = text
        self._refresh_pool_preview()
        self._mark_dirty()

    def _refresh_pool_preview(self):
        while self.pool_preview_layout.count():
            item = self.pool_preview_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        pool = parse_choices(state.get("spin_choices", "0"))
        for v in pool:
            chip = QLabel(f"{v:+d}")
            color = SUCCESS if v > 0 else (DANGER if v < 0 else MUTED)
            chip.setStyleSheet(f"color:{color}; background:{SURFACE}; border:1px solid {BORDER}; border-radius:6px; padding:4px 10px; font-weight:700;")
            self.pool_preview_layout.addWidget(chip)

    def _import_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import", str(get_base_dir()), "JSON (*.json)")
        if not path: return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            for k in [k for k in data if k in PRESET_KEYS]: state[k] = data[k]
            save_settings(); self._rebuild_ui()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _export_preset(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export", str(get_base_dir() / "settings.json"), "JSON (*.json)")
        if not path: return
        try:
            export_data = {k: v for k, v in state.items() if k in PRESET_KEYS}
            Path(path).write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

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
        btn.clicked.connect(getattr(self, f"sig_c{idx}").emit)
        return btn

    def _refresh_custom_btn(self, idx):
        getattr(self, f"btn_c{idx}").setText(f"{state[f'custom_btn{idx}_val']:+d}")

    def _section_counter(self, parent):
        grp = QGroupBox("Counter Configuration")
        g = QGridLayout(grp)
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
        chk_row = QHBoxLayout()
        chk_row.addWidget(mk_chk("Show Max", state["show_max"], lambda v: self._us("show_max", bool(v))))
        chk_row.addWidget(mk_chk("Show Label", state["show_label"], lambda v: self._us("show_label", bool(v))))
        g.addLayout(chk_row, 2, 0, 1, 2)
        parent.addWidget(grp)

    def _section_font(self, parent):
        grp = QGroupBox("Typography")
        g = QGridLayout(grp)
        g.addWidget(rl("Font Family"), 0, 0)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(state["font_family"]))
        self.font_combo.currentFontChanged.connect(lambda f: self._us("font_family", f.family()))
        g.addWidget(self.font_combo, 0, 1)
        g.addWidget(rl("Font Size"), 1, 0)
        sz_row = QHBoxLayout()
        self.spin_size = QSpinBox(); self.spin_size.setRange(10, 300); self.spin_size.setValue(state["font_size"])
        self.spin_size.valueChanged.connect(lambda v: self._us("font_size", v))
        sz_row.addWidget(self.spin_size)
        sz_row.addWidget(mk_chk("Bold", state["font_bold"], lambda v: self._us("font_bold", bool(v))))
        g.addLayout(sz_row, 1, 1)
        parent.addWidget(grp)

    def _section_colors(self, parent):
        grp = QGroupBox("Overlay Colors")
        g = QGridLayout(grp)
        for i, (l, k) in enumerate([("Win", "color_win"), ("Lose", "color_lose"), ("Label", "color_label"), ("Neg", "color_negative")]):
            g.addWidget(rl(l, w=40), 0, i, Qt.AlignCenter)
            cb = ColorButton(state[k])
            cb.color_changed.connect(lambda c, k=k: self._us(k, c))
            g.addWidget(cb, 1, i, Qt.AlignCenter)
        chk_neg = mk_chk("Allow negative wins", state.get("allow_negative", False), lambda v: self._us("allow_negative", bool(v)))
        g.addWidget(chk_neg, 2, 0, 1, 4)
        parent.addWidget(grp)

    def _section_shortcuts(self, parent):
        grp = QGroupBox("Global Hotkeys")
        g = QGridLayout(grp)
        self._key_row(g, "WIN (+1)", "key_win_plus", 0, None)
        self._key_row(g, "UNDO (-1)", "key_win_minus", 1, None)
        self._key_row(g, "RESET", "key_reset", 2, None)
        self._key_row(g, "Custom 1", "key_custom1", 3, 1)
        self._key_row(g, "Custom 2", "key_custom2", 4, 2)
        self._key_row(g, "Custom 3", "key_custom3", 5, 3)
        self._key_row(g, "🎲 SPIN", "key_spin", 6, None)
        parent.addWidget(grp)

    def _key_row(self, grid, label, state_key, row, custom_idx):
        grid.addWidget(rl(label, w=80), row, 0)
        btn = KeyCaptureButton(state[state_key])
        btn.key_captured.connect(lambda key, k=state_key: self._on_key_captured(k, key))
        grid.addWidget(btn, row, 1)
        if custom_idx is not None:
            sp = QSpinBox(); sp.setRange(-999, 999); sp.setValue(state[f"custom_btn{custom_idx}_val"])
            sp.setFixedWidth(60); sp.valueChanged.connect(lambda v, i=custom_idx: self._on_custom_val_changed(i, v))
            grid.addWidget(sp, row, 2)

    def _on_key_captured(self, state_key, key):
        state[state_key] = key; self._mark_dirty()
        _sfx = {"key_win_plus": "+1", "key_win_minus": "-1", "key_reset": "↺", "key_custom1": "C1", "key_custom2": "C2", "key_custom3": "C3", "key_spin": "🎲"}
        for k, lbl in self.lbl_h.items(): lbl.setText(f"[{state[k]}] {_sfx[k]}")

    def _on_custom_val_changed(self, idx, val):
        state[f"custom_btn{idx}_val"] = val; self._refresh_custom_btn(idx); self._mark_dirty()

    def _section_stroke(self, parent):
        grp = QGroupBox("Text Outline")
        g = QGridLayout(grp)
        g.addWidget(mk_chk("Enable Outline", state["stroke"], lambda v: self._us("stroke", bool(v))), 0, 0, 1, 2)
        g.addWidget(rl("Color"), 1, 0)
        sc_btn = ColorButton(state["stroke_color"]); sc_btn.color_changed.connect(lambda c: self._us("stroke_color", c))
        g.addWidget(sc_btn, 1, 1)
        g.addWidget(rl("Size"), 2, 0)
        row = QHBoxLayout(); sl = QSlider(Qt.Horizontal); sl.setRange(0, 10); sl.setValue(state["stroke_size"])
        sl.valueChanged.connect(lambda v: self._us("stroke_size", v))
        lbl = QLabel(f"{state['stroke_size']}px"); sl.valueChanged.connect(lambda v: lbl.setText(f"{v}px"))
        row.addWidget(sl); row.addWidget(lbl); g.addLayout(row, 2, 1)
        parent.addWidget(grp)

    def _section_layout_obs(self, parent):
        grp = QGroupBox("Display Layout")
        lay = QHBoxLayout(grp)
        self.chip_h = ChipButton("⟷ Horizontal", state["layout"] == "horizontal")
        self.chip_v = ChipButton("↕ Vertical", state["layout"] == "vertical")
        self.chip_h.clicked.connect(lambda: self._set_layout("horizontal"))
        self.chip_v.clicked.connect(lambda: self._set_layout("vertical"))
        lay.addWidget(self.chip_h); lay.addWidget(self.chip_v); lay.addStretch()
        parent.addWidget(grp)

    def _section_background(self, parent):
        grp = QGroupBox("Overlay Background")
        g = QGridLayout(grp)
        g.addWidget(rl("Opacity"), 0, 0)
        row = QHBoxLayout(); sl = QSlider(Qt.Horizontal); sl.setRange(0, 100); sl.setValue(state.get("bg_opacity", 0))
        lbl = QLabel(f"{state.get('bg_opacity', 0)}%"); sl.valueChanged.connect(lambda v: (self._us("bg_opacity", v), lbl.setText(f"{v}%")))
        row.addWidget(sl); row.addWidget(lbl); g.addLayout(row, 0, 1)
        g.addWidget(rl("Color 1"), 1, 0)
        c1 = ColorButton(state.get("color_bg", "#000000")); c1.color_changed.connect(lambda c: self._us("color_bg", c))
        g.addWidget(c1, 1, 1)
        g.addWidget(mk_chk("Enable Gradient", state.get("bg_gradient", False), self._on_gradient_toggled), 2, 0, 1, 2)
        parent.addWidget(grp)

    def _on_gradient_toggled(self, v): self._us("bg_gradient", bool(v)); self._update_gradient_visibility()
    def _update_gradient_visibility(self): pass 

    def win_add(self, amount):
        new_val = state["wins"] + amount
        if not state.get("allow_negative", False): new_val = max(0, new_val)
        if new_val != state["wins"]:
            state["wins"] = new_val; self.refresh_display(); self._mark_dirty()

    def apply_custom_win(self):
        val = self.edit_custom_win.text().strip()
        if not val: return
        try: self.win_add(int(val)); self.edit_custom_win.clear()
        except: pass

    def win_reset(self): state["wins"] = 0; self.refresh_display(); self._mark_dirty()
    def _set_layout(self, d): state["layout"] = d; self.chip_h.set_active(d == "horizontal"); self.chip_v.set_active(d == "vertical"); self._mark_dirty()
    def _us(self, k, v): state[k] = v; self.refresh_display(); self._mark_dirty()
    def _mark_dirty(self): self.lbl_save.setText("● Unsaved changes"); self.lbl_save.setStyleSheet(f"color:{WARN};"); self._save_timer.start(1500)
    def _auto_save(self): save_settings() and self._on_saved()
    def _manual_save(self): self._save_timer.stop(); save_settings() and self._on_saved()
    def _on_saved(self):
        self.lbl_save.setText("✓ Saved"); self.lbl_save.setStyleSheet(f"color:{SUCCESS};")
        self.btn_save.setText("✓ Saved"); QTimer.singleShot(1800, lambda: self.btn_save.setText("Save Settings"))
    def refresh_display(self): self.btn_plus.setText(f"WIN +1  [ {state['wins']} ]")
    def closeEvent(self, e): hotkey_manager.stop(); save_settings(); super().closeEvent(e)
