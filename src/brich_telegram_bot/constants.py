from __future__ import annotations

MAIN_MENU_ROWS: list[list[str]] = [
    ["\U0001F4DD Texto", "\u2328\ufe0f Teclas"],
    ["\U0001F9E9 Combos", "\U0001F3AC Macros"],
    ["\U0001F4F8 Camara", "\U0001F4CA Estado"],
    ["\u2699\ufe0f Ajustes", "\U0001F9ED NAVEGAR"],
]

SETUP_CONFIRM_ROWS: list[list[str]] = [
    ["Guardar", "Cancelar"],
]

SETUP_RESET_CONFIRM_ROWS: list[list[str]] = [
    ["SI", "NO"],
]

AUTH_MODE_ROWS: list[list[str]] = [
    ["password", "key"],
]

LOG_LEVEL_ROWS: list[list[str]] = [
    ["DEBUG", "INFO", "WARNING", "ERROR"],
]

STATUS_MENU_ROWS: list[list[str]] = [
    ["\U0001F4CA Estado ahora", "\U0001F9FE Eventos BLE"],
    ["\U0001F4DC Eventos servicio"],
    ["\U0001F504 Reiniciar servicio", "\u25B6\ufe0f Iniciar servicio", "\u23F9\ufe0f Detener servicio"],
    ["\u274C Cancelar", "\U0001F3E0 Menu principal"],
]

KEYBOARD_KEYS: list[str] = [
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "HOME",
    "END",
    "INSERT",
    "DELETE",
    "PGUP",
    "PGDOWN",
    "ENTER",
    "TAB",
    "ESC",
    "BACKSPACE",
    "SPACE",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
]

KEY_MENU_ROWS: list[list[str]] = [
    ["\u2B06\ufe0f UP", "\u2B07\ufe0f DOWN", "\u2B05\ufe0f LEFT", "\u27A1\ufe0f RIGHT"],
    ["\u23CE ENTER", "\u21B9 TAB", "\u238B ESC", "\u232B BACKSPACE", "\u2420 SPACE"],
    ["F1", "F2", "F3", "F4", "F5", "F6"],
    ["F7", "F8", "F9", "F10", "F11", "F12"],
    ["\U0001F4DA Listar teclas", "\u2753 Ayuda teclas"],
    ["\u274C Cancelar", "\U0001F3E0 Menu principal"],
]

TEXT_SHORTCUT_ROWS: list[list[str]] = [
    ["\U0001F524 Prueba acentos: \u00e1\u00e9\u00ed\u00f3\u00fa \u00f1"],
    ["\u274C Cancelar", "\U0001F3E0 Menu principal"],
]

COMBO_SUGGESTION_ROWS: list[list[str]] = [
    ["\U0001F4CB CTRL+C", "\U0001F4E5 CTRL+V", "\u2702\ufe0f CTRL+X"],
    ["\U0001F6E0\ufe0f CTRL+ALT+T", "\U0001F4C8 CTRL+SHIFT+ESC", "\U0001F504 ALT+TAB"],
    ["\U0001FA9F GUI+R", "\U0001F5A5\ufe0f GUI+D", "\U0001F4C1 GUI+E"],
    ["\U0001FA9F GUI+TAB", "\u2194\ufe0f GUI+LEFT", "\u2194\ufe0f GUI+RIGHT"],
    ["\u2195\ufe0f GUI+UP", "\u2195\ufe0f GUI+DOWN", "\U0001F5A5\ufe0f GUI+P"],
    ["\U0001F4DA Ejemplos combos", "\u2753 Ayuda combos"],
    ["\u274C Cancelar", "\U0001F3E0 Menu principal"],
]

NAVIGATION_MENU_ROWS: list[list[str]] = [
    ["\u2B06\ufe0f UP", "\u2B07\ufe0f DOWN", "\u2B05\ufe0f LEFT", "\u27A1\ufe0f RIGHT"],
    ["\U0001F3C1 HOME", "\U0001F3C1 END", "\u2934\ufe0f PGUP", "\u2935\ufe0f PGDOWN"],
    ["\u21B9 TAB", "\u21A9\ufe0f SHIFT+TAB", "\u23CE ENTER", "\u238B ESC"],
    ["\U0001F504 ALT+TAB", "\U0001F504 ALT+SHIFT+TAB", "\U0001F9E9 CTRL+TAB", "\U0001F9E9 CTRL+SHIFT+TAB"],
    ["\U0001FA9F WIN+TAB", "\u2194\ufe0f WIN+LEFT", "\u2194\ufe0f WIN+RIGHT", "\u2195\ufe0f WIN+UP", "\u2195\ufe0f WIN+DOWN"],
    ["\U0001F5A5\ufe0f WIN+D", "\U0001F4C1 WIN+E", "\U0001F5A5\ufe0f WIN+P", "\U0001F5D5 WIN+M"],
    ["\U0001F9ED WIN+CTRL+LEFT", "\U0001F9ED WIN+CTRL+RIGHT"],
    ["\U0001F310 CTRL+L", "\U0001F3AF F6", "\u2420 SPACE", "\u232B BACKSPACE", "\u2326 DELETE"],
    ["\U0001F4F7 Tomar foto", "1\ufe0f\u20e3 Una sola vez tras navegar"],
    ["\U0001F7E2 Auto tras navegar: ON", "\U0001F534 Auto tras navegar: OFF"],
    ["\U0001F4DA Atajos navegar", "\u2753 Ayuda navegar"],
    ["\u274C Cancelar", "\U0001F3E0 Menu principal"],
]

CAMERA_MENU_ROWS: list[list[str]] = [
    ["\U0001F4F7 Tomar foto"],
    ["\U0001F501 Tomar otra"],
    ["\U0001F5BC\ufe0f Res 640x480", "\U0001F5BC\ufe0f Res 1280x720", "\U0001F5BC\ufe0f Res 1920x1080"],
    ["\u270D\ufe0f Resolucion custom (RES WxH)", "\u267B\ufe0f Res default"],
    ["1\ufe0f\u20e3 Una sola vez tras navegar"],
    ["\U0001F7E2 Auto tras navegar: ON", "\U0001F534 Auto tras navegar: OFF"],
    ["\U0001F4CC Estado camara", "\u2753 Ayuda camara"],
    ["\u274C Cancelar", "\U0001F3E0 Menu principal"],
]

INLINE_COMBO_SHORTCUTS: list[list[tuple[str, str]]] = [
    [("WIN+D", "GUI+D"), ("WIN+E", "GUI+E"), ("WIN+TAB", "GUI+TAB")],
    [("WIN+LEFT", "GUI+LEFT"), ("WIN+RIGHT", "GUI+RIGHT"), ("WIN+P", "GUI+P")],
    [("ALT+TAB", "ALT+TAB"), ("CTRL+SHIFT+ESC", "CTRL+SHIFT+ESC")],
]

MACRO_MENU_FOOTER: list[list[str]] = [
    ["\U0001F4DA Listar macros", "\U0001F4A1 Ideas macros"],
    ["\U0001F9EA Plantilla recipe"],
    ["\u2753 Ayuda macros"],
    ["\u274C Cancelar", "\U0001F3E0 Menu principal"],
]

COMMON_COMBO_EXAMPLES: list[str] = [
    "CTRL+ALT+T",
    "CTRL+SHIFT+ESC",
    "CTRL+C",
    "CTRL+V",
    "GUI+R",
    "GUI+D",
    "GUI+E",
    "GUI+TAB",
    "GUI+LEFT",
    "GUI+RIGHT",
    "GUI+P",
]

COMMON_MACRO_EXAMPLES: list[str] = [
    "open_terminal_linux",
    "close_window",
    "open_browser",
]

NAVIGATION_COMBO_EXAMPLES: list[str] = [
    "ALT+TAB",
    "ALT+SHIFT+TAB",
    "WIN+TAB",
    "WIN+LEFT",
    "WIN+RIGHT",
    "WIN+UP",
    "WIN+DOWN",
    "WIN+D",
    "WIN+P",
    "WIN+CTRL+LEFT",
    "WIN+CTRL+RIGHT",
    "CTRL+TAB",
    "CTRL+SHIFT+TAB",
]

BUTTON_ALIASES: dict[str, str] = {
    # Main menu
    "\U0001F4DD Texto": "Texto",
    "\u2328\ufe0f Teclas": "Teclas",
    "\U0001F9E9 Combos": "Combos",
    "\U0001F3AC Macros": "Macros",
    "\U0001F4F8 Camara": "Camara",
    "\U0001F4CA Estado": "Estado",
    "\u2699\ufe0f Ajustes": "Ajustes",
    "\U0001F9ED NAVEGAR": "NAVEGAR",
    # Generic controls
    "\u274C Cancelar": "Cancelar",
    "\U0001F3E0 Menu principal": "Menu principal",
    # Text shortcuts
    "\U0001F524 Prueba acentos: \u00e1\u00e9\u00ed\u00f3\u00fa \u00f1": "Prueba acentos: \u00e1\u00e9\u00ed\u00f3\u00fa \u00f1",
    # Key help/actions
    "\U0001F4DA Listar teclas": "Listar teclas",
    "\u2753 Ayuda teclas": "Ayuda teclas",
    # Combo help/actions
    "\U0001F4DA Ejemplos combos": "Ejemplos combos",
    "\u2753 Ayuda combos": "Ayuda combos",
    # Combo labels
    "\U0001F4CB CTRL+C": "CTRL+C",
    "\U0001F4E5 CTRL+V": "CTRL+V",
    "\u2702\ufe0f CTRL+X": "CTRL+X",
    "\U0001F6E0\ufe0f CTRL+ALT+T": "CTRL+ALT+T",
    "\U0001F4C8 CTRL+SHIFT+ESC": "CTRL+SHIFT+ESC",
    "\U0001F504 ALT+TAB": "ALT+TAB",
    "\U0001FA9F GUI+R": "GUI+R",
    "\U0001F5A5\ufe0f GUI+D": "GUI+D",
    "\U0001F4C1 GUI+E": "GUI+E",
    "\U0001FA9F GUI+TAB": "GUI+TAB",
    "\u2194\ufe0f GUI+LEFT": "GUI+LEFT",
    "\u2194\ufe0f GUI+RIGHT": "GUI+RIGHT",
    "\u2195\ufe0f GUI+UP": "GUI+UP",
    "\u2195\ufe0f GUI+DOWN": "GUI+DOWN",
    "\U0001F5A5\ufe0f GUI+P": "GUI+P",
    # Macro help/actions
    "\U0001F4DA Listar macros": "Listar macros",
    "\U0001F4A1 Ideas macros": "Ideas macros",
    "\U0001F9EA Plantilla recipe": "Plantilla recipe",
    "\u2753 Ayuda macros": "Ayuda macros",
    # Camera help/actions
    "\U0001F4F7 Tomar foto": "Tomar foto",
    "\U0001F501 Tomar otra": "Tomar otra",
    "\U0001F5BC\ufe0f Res 640x480": "RES 640x480",
    "\U0001F5BC\ufe0f Res 1280x720": "RES 1280x720",
    "\U0001F5BC\ufe0f Res 1920x1080": "RES 1920x1080",
    "\u270D\ufe0f Resolucion custom (RES WxH)": "Resolucion custom (RES WxH)",
    "\u267B\ufe0f Res default": "RES DEFAULT",
    "1\ufe0f\u20e3 Una sola vez tras navegar": "Una sola vez tras navegar",
    "Una sola vez": "Una sola vez tras navegar",
    "\U0001F7E2 Auto tras navegar: ON": "Auto tras navegar: ON",
    "\U0001F534 Auto tras navegar: OFF": "Auto tras navegar: OFF",
    "\U0001F4CC Estado camara": "Estado camara",
    "\u2753 Ayuda camara": "Ayuda camara",
    # Status actions
    "\U0001F4CA Estado ahora": "Estado ahora",
    "\U0001F9FE Eventos BLE": "Eventos BLE",
    "\U0001F4DC Eventos servicio": "Eventos servicio",
    "\U0001F504 Reiniciar servicio": "Reiniciar servicio",
    "\u25B6\ufe0f Iniciar servicio": "Iniciar servicio",
    "\u23F9\ufe0f Detener servicio": "Detener servicio",
    # Navigation help/actions
    "\U0001F4DA Atajos navegar": "Atajos navegar",
    "\u2753 Ayuda navegar": "Ayuda navegar",
    # Key labels
    "\u2B06\ufe0f UP": "UP",
    "\u2B07\ufe0f DOWN": "DOWN",
    "\u2B05\ufe0f LEFT": "LEFT",
    "\u27A1\ufe0f RIGHT": "RIGHT",
    "\u23CE ENTER": "ENTER",
    "\u21B9 TAB": "TAB",
    "\u238B ESC": "ESC",
    "\u232B BACKSPACE": "BACKSPACE",
    "\u2420 SPACE": "SPACE",
    "\u2326 DELETE": "DELETE",
    "\U0001F3C1 HOME": "HOME",
    "\U0001F3C1 END": "END",
    "\u2934\ufe0f PGUP": "PGUP",
    "\u2935\ufe0f PGDOWN": "PGDOWN",
    # Navigation combos
    "\u21A9\ufe0f SHIFT+TAB": "SHIFT+TAB",
    "\U0001F504 ALT+SHIFT+TAB": "ALT+SHIFT+TAB",
    "\U0001F9E9 CTRL+TAB": "CTRL+TAB",
    "\U0001F9E9 CTRL+SHIFT+TAB": "CTRL+SHIFT+TAB",
    "\U0001FA9F WIN+TAB": "WIN+TAB",
    "\u2194\ufe0f WIN+LEFT": "WIN+LEFT",
    "\u2194\ufe0f WIN+RIGHT": "WIN+RIGHT",
    "\u2195\ufe0f WIN+UP": "WIN+UP",
    "\u2195\ufe0f WIN+DOWN": "WIN+DOWN",
    "\U0001F5A5\ufe0f WIN+D": "WIN+D",
    "\U0001F4C1 WIN+E": "WIN+E",
    "\U0001F5A5\ufe0f WIN+P": "WIN+P",
    "\U0001F5D5 WIN+M": "WIN+M",
    "\U0001F9ED WIN+CTRL+LEFT": "WIN+CTRL+LEFT",
    "\U0001F9ED WIN+CTRL+RIGHT": "WIN+CTRL+RIGHT",
    "\U0001F310 CTRL+L": "CTRL+L",
    "\U0001F3AF F6": "F6",
}

SERVICE_NAME = "brich-keyboard.service"
BLE_STATUS_FILE = "/tmp/brich_keyboard_status.json"

MAX_TEXT_LENGTH = 500
