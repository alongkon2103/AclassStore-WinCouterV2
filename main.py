import sys
import threading
from pathlib import Path
from flask import Flask, jsonify, Response
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPalette

from core.state import state, load_settings, get_base_dir
from ui.widgets import WinCounter
from ui.styles import BG, TEXT, SURFACE, CARD, ACCENT

# ── Flask ──────────────────────────────────────────────────────────────────────
flask_app = Flask(__name__)

def get_html(filename):
    path = Path(__file__).parent / "web" / filename
    return path.read_text(encoding="utf-8")

@flask_app.route("/overlay")
def overlay_route():
    return Response(get_html("overlay.html"), mimetype="text/html")

@flask_app.route("/spin")
def spin_route():
    tpl = state.get("spin_template", 1)
    filename = f"spin_{tpl}.html"
    return Response(get_html(filename), mimetype="text/html")

@flask_app.route("/state")
def state_route():
    return jsonify(state)

def run_flask():
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    load_settings()
    
    threading.Thread(target=run_flask, daemon=True).start()
    print("[Flask] OBS Overlay  → http://localhost:5000/overlay")
    print("[Flask] Spin Overlay → http://localhost:5000/spin")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(BG))
    pal.setColor(QPalette.WindowText,      QColor(TEXT))
    pal.setColor(QPalette.Base,            QColor(SURFACE))
    pal.setColor(QPalette.AlternateBase,   QColor(CARD))
    pal.setColor(QPalette.Text,            QColor(TEXT))
    pal.setColor(QPalette.Button,          QColor(CARD))
    pal.setColor(QPalette.ButtonText,      QColor(TEXT))
    pal.setColor(QPalette.Highlight,       QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)

    win = WinCounter()
    app._main_win = win
    win.resize(900, 780)
    win.show()
    sys.exit(app.exec())
