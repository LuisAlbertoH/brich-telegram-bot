# brich-telegram-bot

Bot privado de Telegram para controlar una Raspberry Pi por SSH y ejecutar acciones de teclado remoto.

## Caracteristicas
- Bot de Telegram con menu interactivo por botones (`ReplyKeyboardMarkup`).
- Control remoto por SSH contra scripts de la Raspberry:
  - `python3 /home/pi/brich/keyboard_ctl.py text "..."`
  - `python3 /home/pi/brich/keyboard_ctl.py key ENTER`
  - `python3 /home/pi/brich/keyboard_ctl.py combo "CTRL+ALT+T"`
  - `python3 /home/pi/brich/keyboard_ctl.py macro open_terminal_linux`
- Flujo de setup conversacional para crear/actualizar `.env`.
- Bot de un solo usuario (`AUTHORIZED_CHAT_ID`).
- Validaciones de input, quoting de comandos SSH, timeouts y manejo de errores.
- Logs estructurados en JSON sin exponer secretos.

## Requisitos
- Python 3.11+
- Raspberry accesible por SSH en la misma LAN
- Token de bot de Telegram (`TELEGRAM_BOT_TOKEN`)

## Estructura
```
brich-telegram-bot/
  src/brich_telegram_bot/
    config.py
    security.py
    ssh_client.py
    remote_control.py
    telegram_bot.py
  docs/COMMANDS.md
  deploy/launchd/com.brich.telegram-bot.plist
  tests/
  scripts/smoke_test.py
  .env.example
  requirements.txt
  run_bot.sh
  run_bot.ps1
  main.py
```

## Instalacion

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

## Primer setup (si no existe .env)
1. Asegura que `TELEGRAM_BOT_TOKEN` este definido en entorno o `.env`.
2. Inicia el bot con `python main.py` (o script de arranque).
3. En Telegram, ejecuta `/start` o `/setup`.
4. Completa el flujo:
   - Password de setup (validar existente o crear nueva)
   - IP/host Raspberry
   - Usuario/puerto SSH
   - Modo de auth SSH (`password` o `key`)
   - Ruta remota del proyecto (`RPI_PROJECT_PATH`)
5. El bot guarda `.env` automaticamente y fija `AUTHORIZED_CHAT_ID` al chat actual.

## Variables de entorno
Ver `.env.example`. Variables esperadas:
- `TELEGRAM_BOT_TOKEN` (obligatoria)
- `AUTHORIZED_CHAT_ID`
- `SETUP_PASSWORD`
- `RPI_HOST`
- `RPI_PORT`
- `RPI_USER`
- `RPI_AUTH_MODE` (`password` o `key`)
- `RPI_PASSWORD`
- `RPI_SSH_KEY_PATH`
- `RPI_PROJECT_PATH`
- `SSH_TIMEOUT_SEC`
- `LOG_LEVEL`

## Ejecucion

### Script simple
```bash
./run_bot.sh
```

### PowerShell
```powershell
.\run_bot.ps1
```

### Manual
```bash
python main.py
```

## Menu y comandos
- `/start`
- `/help`
- `/setup`
- `/cancel`
- Botones:
  - Texto
  - Teclas
  - Combos
  - Macros
  - Estado
  - Ajustes

Detalle de uso y ejemplos en [`docs/COMMANDS.md`](docs/COMMANDS.md).

## launchd (macOS, opcional)
Archivo plantilla: `deploy/launchd/com.brich.telegram-bot.plist`

Pasos:
1. Copia y ajusta rutas absolutas.
2. Carga el servicio:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.brich.telegram-bot.plist 2>/dev/null || true
   cp deploy/launchd/com.brich.telegram-bot.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.brich.telegram-bot.plist
   launchctl start com.brich.telegram-bot
   ```

## Pruebas
```bash
pytest
python scripts/smoke_test.py
```

## Troubleshooting
- Error `TELEGRAM_BOT_TOKEN es obligatorio`:
  - Define token real en `.env` o variable de entorno.
- `Acceso denegado`:
  - El `chat_id` no coincide con `AUTHORIZED_CHAT_ID`.
- Error SSH:
  - Revisa `RPI_HOST`, `RPI_USER`, auth mode y timeout.
  - Verifica conectividad desde la maquina local:
    - `ssh pi@192.168.1.50`
- Servicio no activo:
  - En Raspberry: `systemctl status brich-keyboard.service`
- BLE sin estado:
  - Revisa existencia de `/tmp/brich_keyboard_status.json`.

## Seguridad minima aplicada
- Validacion estricta de teclas, combos y macros.
- Sanitizacion de texto y limite de longitud.
- Quoting seguro en comandos enviados por SSH.
- Timeouts SSH configurables.
- Logs JSON sin contrasenas/token.
