# 🤖 brich-telegram-bot

Bot privado de Telegram para controlar una Raspberry Pi por SSH y ejecutar acciones de teclado remoto de forma segura.

## ✨ Que hace este bot
- 🎛️ Menu interactivo con `ReplyKeyboardMarkup` (Texto, Teclas, Combos, Macros, Camara, Estado, Ajustes, NAVEGAR).
- ⚡ Atajos `InlineKeyboardMarkup` para combos frecuentes (incluyendo tecla Windows).
- 🔤 Soporte correcto de acentos y caracteres especiales (normalizacion Unicode NFC).
- 📸 Captura de webcam local y envio al chat autorizado.
- 🖼️ Resolucion de camara configurable (presets, `RES WxH`, default del dispositivo).
- 1️⃣ Modo `Una sola vez tras navegar` (captura una vez y se apaga solo).
- 🔁 Modo auto-foto tras navegar (`Auto tras navegar: ON/OFF`, continuo).
- 🧩 Recipes locales (`LOCAL:<nombre>`) para automatizar flujos simples.
- 🛠️ Control remoto del servicio (`restart/start/stop`) desde el menu Estado.
- 🧾 Vista legible de eventos de servicio y BLE en orden cronologico.
- 🔒 Bot de un solo usuario (`AUTHORIZED_CHAT_ID`) con validaciones de seguridad.
- 🛡️ Sanitizacion de inputs + quoting seguro + timeouts SSH + logs estructurados.

## 🧱 Arquitectura rapida
1. Telegram recibe comando o boton.
2. El bot valida autorizacion y sanitiza input.
3. Para acciones remotas, ejecuta `keyboard_ctl.py` por SSH en Raspberry.
4. Para Camara, captura localmente en la maquina donde corre el bot.
5. Devuelve resultado al chat con confirmacion o error claro.

## 📦 Requisitos
- Python `3.11+`
- Raspberry Pi accesible por SSH en la misma LAN
- `TELEGRAM_BOT_TOKEN`
- Webcam local funcional (si usaras Camara)

## 🚀 Instalacion

### macOS / Linux
```bash
cd brich-telegram-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Windows (PowerShell)
```powershell
cd brich-telegram-bot
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## 🔐 Configuracion de entorno (`.env`)
Referencia base: `.env.example`.

Variables clave:
- `TELEGRAM_BOT_TOKEN`: token del bot de Telegram (obligatorio).
- `AUTHORIZED_CHAT_ID`: chat permitido para operar el bot (se puede definir en setup).
- `SETUP_PASSWORD`: clave para proteger `/setup`.
- `RPI_HOST`, `RPI_PORT`, `RPI_USER`: destino SSH de Raspberry.
- `RPI_AUTH_MODE`: `password` o `key`.
- `RPI_PASSWORD`: obligatorio si `RPI_AUTH_MODE=password`.
- `RPI_SSH_KEY_PATH`: obligatorio si `RPI_AUTH_MODE=key`.
- `RPI_PROJECT_PATH`: ruta remota donde existe `keyboard_ctl.py`.
- `SSH_TIMEOUT_SEC`: timeout SSH por comando.
- `CAMERA_DEVICE_INDEX`, `CAMERA_FRAME_WIDTH`, `CAMERA_FRAME_HEIGHT`, `CAMERA_WARMUP_FRAMES`, `CAMERA_TIMEOUT_SEC`: control de webcam.
- `LOCAL_RECIPES_PATH`: JSON local de recipes.
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`.

## 🛠️ Setup inicial por Telegram
Si `.env` no existe o falta configuracion:
1. Inicia el bot.
2. En Telegram usa `/start` o `/setup`.
3. Sigue el asistente:
   - password de setup
   - host/puerto/usuario SSH
   - auth mode (`password` o `key`)
   - ruta de proyecto remoto
   - timeout y nivel de log
4. El bot guarda `.env` automaticamente.

Si `.env` ya existe y esta completo, el bot arranca sin pedir setup.

## ▶️ Ejecucion

### Script rapido (macOS/Linux)
```bash
./run_bot.sh
```

### Script rapido (Windows)
```powershell
.\run_bot.ps1
```

### Manual
```bash
python main.py
```

## 🧭 Guia de uso rapido

### 1) 📝 Texto
- Entra a `Texto`.
- Escribe cualquier mensaje (incluye acentos, simbolos y saltos de linea).
- El bot ejecuta remoto: `keyboard_ctl.py text "..."`.

### 2) 🧭 NAVEGAR + 📸 evidencia automatica
- Entra a `NAVEGAR`.
- Usa flechas, TAB, PGUP/PGDOWN, ALT+TAB, WIN+TAB, WIN+LEFT/RIGHT, etc.
- Activa `Una sola vez tras navegar` si quieres solo la siguiente captura y desactivacion automatica.
- Activa `Auto tras navegar: ON` para tomar foto despues de cada accion.
- Usa `Tomar foto` para captura unica manual sin salir del menu.
- Define resolucion desde `Camara` con presets o `RES WxH` (ej: `RES 1280x720`).

### 3) 🎬 Macros y recipes
- Entra a `Macros`.
- Usa `Listar macros` para ver macros remotas.
- Usa `Ideas macros` para inspirarte.
- Usa `Plantilla recipe` para copiar base JSON.
- Ejecuta recipe local con `LOCAL:nombre_recipe`.

### 4) 📊 Estado y ⚙️ Ajustes
- `Estado`: submenu para:
  - `Estado ahora` (active/enabled + resumen BLE)
  - `Eventos servicio` (timeline cronologico desde `journalctl`)
  - `Eventos BLE` (timeline cronologico si existe en status BLE)
  - `Reiniciar/Iniciar/Detener servicio`
- `Ajustes`: muestra configuracion activa (sin secretos).

## 🧩 Recipes locales (automatizacion)
Ruta por defecto: `automation_recipes.json` (configurable por `LOCAL_RECIPES_PATH`).

Plantilla incluida: `automation_recipes.example.json`.

Ejemplo minimo:
```json
{
  "abrir_navegador_url": [
    {"kind": "combo", "value": "GUI+R"},
    {"kind": "wait", "ms": 500},
    {"kind": "text", "value": "chrome https://www.google.com"},
    {"kind": "key", "value": "ENTER"}
  ]
}
```

Tipos de paso soportados:
- `key`
- `combo`
- `text`
- `wait` (milisegundos)

## 🧪 Pruebas
```bash
pytest
python scripts/smoke_test.py
```

## 🛡️ Seguridad aplicada
- Validacion estricta de teclas, combos y nombres de macro.
- Sanitizacion de texto con limite de longitud.
- Quoting seguro para comandos remotos.
- Timeouts SSH configurables.
- Logs JSON sin secretos.

## 🧯 Troubleshooting rapido
- ❌ `TELEGRAM_BOT_TOKEN es obligatorio`
  - Verifica `.env` y formato del token.
- ❌ `Acceso denegado`
  - Revisa `AUTHORIZED_CHAT_ID`.
- ❌ Falla SSH
  - Valida host/usuario/credencial/timeout y conectividad LAN.
- ❌ No se puede controlar el servicio desde Estado
  - Revisa permisos `systemctl`/`sudo -n` del usuario SSH en Raspberry.
- ❌ Camara no captura
  - Revisa permisos de webcam y `CAMERA_DEVICE_INDEX`.
- ❌ No se dispara `Una sola vez tras navegar`
  - Recuerda que se consume en la siguiente accion valida de `NAVEGAR` y luego se desactiva.
- ❌ Recipe local no aparece
  - Verifica `LOCAL_RECIPES_PATH`, JSON valido y nombre de recipe.

Guia extendida: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)

## 📚 Documentacion
- 🎮 Comandos y menus: [`docs/COMMANDS.md`](docs/COMMANDS.md)
- 🧭 Casos de uso guiados: [`docs/USAGE_GUIDE.md`](docs/USAGE_GUIDE.md)
- 🧯 Troubleshooting completo: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)

## 🍎 Ejecucion persistente en macOS (launchd)
Plantilla: `deploy/launchd/com.brich.telegram-bot.plist`

Pasos sugeridos:
```bash
launchctl unload ~/Library/LaunchAgents/com.brich.telegram-bot.plist 2>/dev/null || true
cp deploy/launchd/com.brich.telegram-bot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.brich.telegram-bot.plist
launchctl start com.brich.telegram-bot
```

## 🗂️ Estructura del proyecto
```text
brich-telegram-bot/
  src/brich_telegram_bot/
    config.py
    security.py
    ssh_client.py
    remote_control.py
    camera_capture.py
    local_recipes.py
    telegram_bot.py
  docs/
    COMMANDS.md
    USAGE_GUIDE.md
    TROUBLESHOOTING.md
  deploy/launchd/com.brich.telegram-bot.plist
  tests/
  scripts/smoke_test.py
  .env.example
  automation_recipes.example.json
  requirements.txt
  run_bot.sh
  run_bot.ps1
  main.py
```
