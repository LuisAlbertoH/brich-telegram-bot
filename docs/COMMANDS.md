# 🎮 COMMANDS

Guia operativa del bot en Telegram.

## 🚦 Comandos slash

### `/start`
- Muestra menu principal.
- Si falta configuracion, recomienda `/setup`.

### `/help`
- Muestra ayuda rapida de menus y tips.

### `/setup`
Asistente guiado para crear o actualizar `.env`:
1. Validar o crear `SETUP_PASSWORD`.
2. Capturar host/puerto/usuario SSH.
3. Definir auth mode (`password` o `key`) y secreto.
4. Definir ruta remota (`RPI_PROJECT_PATH`).
5. Confirmar y guardar.

### `/cancel`
- Cancela setup o accion pendiente.
- Regresa al menu principal.

## 🧭 Menu principal
- 📝 `Texto`
- ⌨️ `Teclas`
- 🧩 `Combos`
- 🎬 `Macros`
- 📸 `Camara`
- 📊 `Estado`
- ⚙️ `Ajustes`
- 🧭 `NAVEGAR`

## 📝 Texto
- Uso: enviar texto remoto, incluyendo acentos.
- Botones rapidos: `Prueba acentos: áéíóú ñ`, `Cancelar`, `Menu principal`.
- Comando remoto:
```bash
python3 <RPI_PROJECT_PATH>/keyboard_ctl.py text "<mensaje>"
```

Ejemplo:
```text
Hola desde Telegram 👋
```

## ⌨️ Teclas
- Uso: enviar teclas simples.
- Teclas sugeridas: `UP, DOWN, LEFT, RIGHT, ENTER, TAB, ESC, BACKSPACE, SPACE, F1..F12`.
- Tambien acepta teclas seguras custom: `PRINT_SCREEN`, `MEDIA_PLAY_PAUSE`.
- Botones rapidos: `Listar teclas`, `Ayuda teclas`.
- Comando remoto:
```bash
python3 <RPI_PROJECT_PATH>/keyboard_ctl.py key ENTER
```

## 🧩 Combos
- Formato: `MOD+KEY` o `MOD+MOD+KEY`.
- Mods validos: `CTRL`, `SHIFT`, `ALT`, `GUI`.
- Puedes escribir `WIN+...`; el bot lo normaliza a `GUI+...`.
- Inline keyboard disponible para atajos frecuentes.
- Botones rapidos: `Ejemplos combos`, `Ayuda combos`.
- Comando remoto:
```bash
python3 <RPI_PROJECT_PATH>/keyboard_ctl.py combo "CTRL+ALT+T"
```

Ejemplos:
```text
CTRL+ALT+T
CTRL+SHIFT+ESC
GUI+TAB
WIN+D
```

## 🎬 Macros
Flujo:
1. Presiona `Macros`.
2. El bot lista macros remotas + recipes locales.
3. Opciones:
   - `Listar macros`
   - `Ideas macros`
   - `Plantilla recipe`
   - `Ayuda macros`
4. Ejecuta macro remota o recipe local.

Ejecucion de recipe local:
- Formato: `LOCAL:<nombre_recipe>`
- Ejemplo: `LOCAL:open_browser_google`

Comando remoto para macro nativa:
```bash
python3 <RPI_PROJECT_PATH>/keyboard_ctl.py macro open_terminal_linux
```

### 🧪 Recipes locales
- Archivo: `LOCAL_RECIPES_PATH` (default `automation_recipes.json`).
- Plantilla base: `automation_recipes.example.json`.
- Tipos de paso soportados:
  - `key`
  - `combo`
  - `text`
  - `wait`

## 📸 Camara
- Captura desde webcam local (equipo donde corre el bot).
- Opciones:
  - `Tomar foto` (captura unica)
  - `Tomar otra` (captura unica)
  - `Auto tras navegar: ON/OFF`
  - `Estado camara`
  - `Ayuda camara`
- El bot envia la foto al chat y borra el temporal.

## 📊 Estado
Consulta remoto:
- `systemctl is-active brich-keyboard.service`
- `systemctl is-enabled brich-keyboard.service`
- `/tmp/brich_keyboard_status.json` (si existe)

## ⚙️ Ajustes
- Muestra configuracion activa sin secretos.
- Para cambiar configuracion usa `/setup`.

## 🧭 NAVEGAR
Modo persistente para navegacion rapida de foco/ventanas/pantallas.

Incluye:
- Direccion: `UP`, `DOWN`, `LEFT`, `RIGHT`
- Paginacion: `PGUP`, `PGDOWN`
- Foco: `TAB`, `SHIFT+TAB`, `F6`
- Ventanas: `ALT+TAB`, `ALT+SHIFT+TAB`, `WIN+TAB`
- Snap/Layout: `WIN+LEFT`, `WIN+RIGHT`, `WIN+UP`, `WIN+DOWN`
- Pantallas: `WIN+P`
- Escritorio: `WIN+D`, `WIN+M`
- Camara rapida: `Tomar foto`, `Auto tras navegar: ON`, `Auto tras navegar: OFF`

Tips:
- Usa `Atajos navegar` para ver recomendaciones.
- Usa `Ayuda navegar` para recordar formato.
- Usa `Cancelar` para salir.

## 🔒 Respuestas de seguridad
- Chat no autorizado:
```text
Acceso denegado. Este bot es privado para un solo chat autorizado.
```

- Input invalido:
```text
Error: <detalle>
Tip: <sugerencia del flujo>
```
