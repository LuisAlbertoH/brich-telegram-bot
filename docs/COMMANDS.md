# COMMANDS

## Comandos slash

### `/start`
Muestra menu principal. Si no hay configuracion completa, indica iniciar `/setup`.

### `/help`
Muestra ayuda rapida y lista de opciones.

### `/setup`
Inicia setup guiado:
1. Validar/crear password de setup.
2. Capturar host, puerto, usuario SSH.
3. Capturar auth mode (`password` o `key`) y secreto correspondiente.
4. Capturar ruta de proyecto remoto.
5. Guardar `.env` y fijar `AUTHORIZED_CHAT_ID`.

### `/cancel`
Cancela flujo activo (setup o accion pendiente).

## Menu principal
- `Texto`
- `Teclas`
- `Combos`
- `Macros`
- `Estado`
- `Ajustes`

## Flujos por boton

### Texto
1. Presiona `Texto`.
2. Escribe mensaje (max 500 chars).
3. Bot ejecuta:
   - `python3 <RPI_PROJECT_PATH>/keyboard_ctl.py text "<mensaje>"`

Ejemplo:
```
Hola desde Telegram
```

### Teclas
1. Presiona `Teclas`.
2. Elige o escribe:
   - `UP, DOWN, LEFT, RIGHT, ENTER, TAB, ESC, BACKSPACE, SPACE, F1..F12`
3. Bot ejecuta:
   - `python3 <RPI_PROJECT_PATH>/keyboard_ctl.py key ENTER`

### Combos
1. Presiona `Combos`.
2. Escribe combo:
   - Formato: `MOD+MOD+KEY`
   - Mods validos: `CTRL, SHIFT, ALT, GUI`
3. Bot ejecuta:
   - `python3 <RPI_PROJECT_PATH>/keyboard_ctl.py combo "CTRL+ALT+T"`

Ejemplos:
```
CTRL+ALT+T
CTRL+SHIFT+ESC
GUI+R
```

### Macros
1. Presiona `Macros`.
2. Bot intenta listar macros remoto (`macro --list` / `macro list`).
3. Selecciona macro o escribe nombre manual.
4. Bot ejecuta:
   - `python3 <RPI_PROJECT_PATH>/keyboard_ctl.py macro open_terminal_linux`

### Estado
Consulta:
- `systemctl is-active brich-keyboard.service`
- `systemctl is-enabled brich-keyboard.service`
- `/tmp/brich_keyboard_status.json` (si existe)

### Ajustes
Muestra resumen de configuracion actual (sin secretos) y ruta para reconfigurar.

## Respuestas de seguridad
- Chat no autorizado:
  - `Acceso denegado. Este bot es privado para un solo chat autorizado.`
- Input invalido:
  - Mensaje claro de validacion y no se ejecuta comando remoto.

