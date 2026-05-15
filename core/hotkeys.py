from core.state import state

class GlobalHotkeyManager:
    def __init__(self):
        self._listener = None
        self.actions = {}

    @staticmethod
    def _normalize(key) -> str:
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.upper()
        except Exception:
            pass
        try:
            name = key.name.lower()
            if name.startswith('f') and name[1:].isdigit():
                return name.upper()
            _MAP = {
                'space':'Space','enter':'Return','esc':'Escape',
                'backspace':'Backspace','delete':'Delete','tab':'Tab',
                'up':'Up','down':'Down','left':'Left','right':'Right',
                'home':'Home','end':'End','page_up':'PgUp','page_down':'PgDown',
                'insert':'Insert','caps_lock':'CapsLock',
            }
            return _MAP.get(name, name.upper())
        except Exception:
            pass
        return ''

    def _on_press(self, key):
        k = self._normalize(key)
        if not k:
            return
        for action_id, state_key in [
            ('plus','key_win_plus'),('minus','key_win_minus'),('reset','key_reset'),
            ('c1','key_custom1'),('c2','key_custom2'),('c3','key_custom3'),
            ('spin','key_spin'),
        ]:
            if k.upper() == str(state.get(state_key, '')).upper():
                fn = self.actions.get(action_id)
                if fn: fn()
                break

    def start(self, actions: dict):
        self.actions = actions
        if self._listener is None:
            try:
                from pynput import keyboard as kb
                self._listener = kb.Listener(on_press=self._on_press)
                self._listener.daemon = True
                self._listener.start()
            except Exception as e:
                print(f"[Hotkeys] cannot start: {e}")

    def stop(self):
        if self._listener:
            try: self._listener.stop()
            except Exception: pass
            self._listener = None

hotkey_manager = GlobalHotkeyManager()
