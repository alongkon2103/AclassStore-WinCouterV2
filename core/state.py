import sys
import json
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent  # Adjusted for being in core/

SETTINGS_FILE = get_base_dir() / "settings.json"

# ── defaults ───────────────────────────────────────────────────────────────────
DEFAULT_STATE = {
    "wins": 0, "max_wins": 10,
    "label_win": "WIN", "show_max": True, "show_label": True,
    "font_family": "Arial", "font_size": 72, "font_bold": True,
    "color_win": "#5E9EE4", "color_lose": "#64748B",
    "color_negative": "#EF4444", "color_label": "#FFFFFF",
    "allow_negative": False,
    "color_bg": "#000000", "stroke": True,
    "stroke_color": "#000000", "stroke_size": 3,
    "layout": "horizontal", "separator": "/", "bg_opacity": 0,
    "bg_border_radius": 14, "bg_padding_h": 24, "bg_padding_v": 12,
    "bg_gradient": False, "color_bg2": "#1a1a2e", "bg_gradient_dir": "to right",
    "key_win_plus": "F1", "key_win_minus": "F2", "key_reset": "F3",
    "custom_btn1_val": 2, "custom_btn2_val": 3, "custom_btn3_val": -1,
    "key_custom1": "F4", "key_custom2": "F5", "key_custom3": "F6",
    "key_spin": "F7",
    "spin_choices": "1,-5,-3,-4,5,10,6",
    "spin_color_up": "#A855F7",
    "spin_color_down": "#EF4444",
    "spin_color_zero": "#64748B",
    "spin_template": 1,
}

# แยก runtime state ออกจาก saved state
RUNTIME_STATE = {
    "spin_active": False,
    "spin_result": 0,
    "spin_seq": 0,   # ← sequence counter: overlay จับ edge นี้แทน boolean flag
    "spin_pending_result": 0,
}

PRESET_KEYS = {k for k in DEFAULT_STATE if k not in ("wins",)}

state: dict = {}

def load_settings():
    global state
    state.clear()
    state.update(DEFAULT_STATE)
    state.update(RUNTIME_STATE)   # runtime เริ่มต้นใหม่เสมอ
    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            for k, v in saved.items():
                if k in DEFAULT_STATE:   # โหลดเฉพาะ saved keys
                    state[k] = v
        except Exception as e:
            print(f"[Settings] load failed: {e}")

def save_settings():
    try:
        # บันทึกเฉพาะ DEFAULT_STATE keys (ไม่บันทึก runtime)
        to_save = {k: state[k] for k in DEFAULT_STATE if k in state}
        SETTINGS_FILE.write_text(json.dumps(to_save, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        print(f"[Settings] save failed: {e}")
        return False

def parse_choices(raw: str) -> list:
    result = []
    for part in raw.split(","):
        part = part.strip()
        try:
            result.append(int(part))
        except ValueError:
            pass
    return result if result else [0]
