# 🧯 TROUBLESHOOTING

Guia de diagnostico rapido para `brich-telegram-bot`.

## 1) 🚫 El bot no arranca

Sintoma:
- Error tipo `TELEGRAM_BOT_TOKEN es obligatorio`.

Checklist:
- Verifica que `.env` exista en la raiz del proyecto.
- Verifica que `TELEGRAM_BOT_TOKEN` tenga valor real.
- Confirma que no tenga espacios o comillas extras.

Comandos utiles:
```powershell
Get-Content .env
.\.venv\Scripts\python.exe main.py
```

## 2) 🔒 "Acceso denegado" en Telegram

Sintoma:
- El bot responde que es privado para un solo chat.

Causa comun:
- `AUTHORIZED_CHAT_ID` no coincide con tu chat actual.

Solucion:
- Ejecuta `/setup` desde el chat correcto.
- O actualiza manualmente `AUTHORIZED_CHAT_ID` en `.env`.
- Reinicia el bot.

## 3) 🌐 Falla conexion SSH a Raspberry

Sintomas:
- Timeout SSH.
- Auth failure.
- No ejecuta comandos remotos.

Checklist `.env`:
- `RPI_HOST`, `RPI_PORT`, `RPI_USER`
- `RPI_AUTH_MODE`
- `RPI_PASSWORD` o `RPI_SSH_KEY_PATH`
- `RPI_PROJECT_PATH`

Prueba local de conectividad:
```bash
ssh pi@192.168.1.50
```

Si usas llave (`RPI_AUTH_MODE=key`):
- Verifica ruta local de la llave privada.
- Verifica que la llave publica este en `~/.ssh/authorized_keys` de Raspberry.
- En Windows, usa rutas tipo: `C:/Users/<usuario>/.ssh/id_ed25519`.

## 4) ⌨️ No responde teclado remoto

Sintoma:
- El bot responde pero la accion no impacta en destino.

Checklist en Raspberry:
```bash
systemctl status brich-keyboard.service
python3 /home/pi/brich/keyboard_ctl.py key ENTER
```

Verifica:
- Servicio `brich-keyboard.service` activo.
- Ruta correcta en `RPI_PROJECT_PATH`.
- Permisos de ejecucion para `keyboard_ctl.py`.

## 4.1) 🛠️ No se puede reiniciar/iniciar/detener servicio

Sintomas:
- Error al usar `Reiniciar servicio`, `Iniciar servicio` o `Detener servicio`.

Checklist:
- Verifica si tu usuario SSH puede usar `systemctl` para ese servicio.
- Si requiere sudo, confirma que permite `sudo -n` sin prompt para ese comando.
- Prueba manual en Raspberry:
```bash
systemctl restart brich-keyboard.service
sudo -n systemctl restart brich-keyboard.service
```
- Si `sudo -n` falla, configura regla sudoers para el usuario del bot.

## 4.2) 🧾 Eventos de servicio vacios o inaccesibles

Sintomas:
- `Eventos servicio` no muestra logs o devuelve error.

Checklist:
- Verifica que `journalctl` este disponible en Raspberry.
- Prueba lectura manual:
```bash
journalctl -u brich-keyboard.service --no-pager -o short-iso -n 40
```
- Si requiere permisos, prueba con sudo:
```bash
sudo -n journalctl -u brich-keyboard.service --no-pager -o short-iso -n 40
```

## 5) 📸 Camara no toma foto

Sintomas:
- `No se pudo abrir la webcam local`.
- `No se pudo capturar un frame valido`.

Checklist:
- Cierra apps que usen webcam (Zoom, Meet, OBS, Teams).
- Da permisos de camara a terminal/Python.
- Prueba cambiar `CAMERA_DEVICE_INDEX` (0, 1, 2...).
- Ajusta resolucion objetivo (`RES 1280x720`) si la webcam falla con resoluciones altas.
- Usa `Res default` para volver al modo nativo del dispositivo.
- Ajusta `CAMERA_WARMUP_FRAMES` (ej. 8-15).
- Aumenta `CAMERA_TIMEOUT_SEC` (ej. 8-12).

Nota:
- La captura es local, no en Raspberry.

## 5.1) 1️⃣ \"Una sola vez tras navegar\" no dispara

Sintomas:
- Activaste `Una sola vez tras navegar` y no ves foto.

Checklist:
- Asegura que despues de activarlo ejecutaste una accion valida en `NAVEGAR` (tecla o combo).
- Evita pensar que se dispara sola sin navegar: requiere una accion posterior.
- Recuerda que se consume en un intento y luego se desactiva.
- Si hubo error de camara, vuelve a activarlo y revisa permisos/dispositivo.

## 6) 🧩 Recipes locales no aparecen o fallan

Sintomas:
- `No se pudieron cargar recipes locales`.
- `Recipe local no encontrada`.

Checklist:
- `LOCAL_RECIPES_PATH` apunta al archivo correcto.
- JSON valido (sin comas sobrantes).
- Nombres de recipes con formato seguro (letras, numeros, `_` o `-`).
- Tipos de paso validos: `key`, `combo`, `text`, `wait`.

Valida JSON rapido (PowerShell):
```powershell
Get-Content automation_recipes.json | ConvertFrom-Json | Out-Null
```

## 7) 🔤 Problemas de acentos o caracteres raros

Sintomas:
- Texto con caracteres corruptos.

Checklist:
- Guarda archivos en UTF-8.
- Usa cliente Telegram actualizado.
- Evita copiar texto desde fuentes con encoding legacy.

El bot ya normaliza texto en NFC para preservar acentos y caracteres especiales.

## 8) 🧾 Logs y diagnostico avanzado

Activa logs detallados:
- En `.env`: `LOG_LEVEL=DEBUG`
- Reinicia bot.

Smoke test:
```bash
python scripts/smoke_test.py
```

Tests:
```bash
pytest
```

## 9) 🔄 Reinicio seguro del bot

Windows (PowerShell):
```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'brich-telegram-bot.*main.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Process .\.venv\Scripts\python.exe -ArgumentList 'main.py' -WorkingDirectory (Get-Location)
```

macOS/Linux:
```bash
pkill -f "brich-telegram-bot.*main.py" || true
./run_bot.sh
```
