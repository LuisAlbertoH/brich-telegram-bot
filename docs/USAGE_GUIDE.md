# 🧭 USAGE GUIDE

Guia practica orientada a casos reales de uso.

## Caso 1: 📝 Escribir texto con acentos

Objetivo:
- Escribir texto remoto sin perder caracteres especiales.

Pasos:
1. Abre Telegram y entra al bot.
2. Presiona `Texto`.
3. Escribe algo como:
```text
Configuración rápida: áéíóú ñ ¿listo?
```
4. Verifica que el texto se vea correcto en destino.

## Caso 2: 🧭 Navegar ventanas y tomar evidencia

Objetivo:
- Cambiar ventanas/pantalla y registrar evidencia con foto.

Pasos:
1. Presiona `NAVEGAR`.
2. Si quieres una sola evidencia, activa `Una sola vez tras navegar`.
3. Si quieres evidencia continua, activa `Auto tras navegar: ON`.
4. Usa atajos como `ALT+TAB`, `WIN+TAB`, `WIN+LEFT`.
5. Verifica la llegada de foto:
   - `Una sola vez tras navegar`: solo una captura y se desactiva sola.
   - `Auto tras navegar: ON`: captura despues de cada accion.
6. Si solo quieres una captura puntual manual, usa `Tomar foto`.
7. Para desactivar todo, pulsa `Auto tras navegar: OFF`.

## Caso 3: 🎬 Ejecutar macro remota

Objetivo:
- Reutilizar macros ya definidas en Raspberry.

Pasos:
1. Presiona `Macros`.
2. Pulsa `Listar macros`.
3. Selecciona una macro o escribe su nombre.
4. Confirma resultado en mensaje del bot.

## Caso 4: 🧩 Automatizar con recipe local

Objetivo:
- Crear automatizacion local tipo "abrir app + ejecutar comando".

Pasos:
1. Copia plantilla:
```bash
cp automation_recipes.example.json automation_recipes.json
```
En Windows PowerShell:
```powershell
Copy-Item automation_recipes.example.json automation_recipes.json
```
2. Edita `automation_recipes.json` con tu flujo.
3. En Telegram entra a `Macros`.
4. Ejecuta con formato `LOCAL:<nombre_recipe>`.

Ejemplo:
```text
LOCAL:open_terminal_and_run_top
```

## Caso 5: 📊 Verificar estado de servicio y BLE

Objetivo:
- Confirmar salud del backend remoto.

Pasos:
1. Presiona `Estado`.
2. Revisa:
   - `active` / `enabled` de `brich-keyboard.service`
   - contenido de `/tmp/brich_keyboard_status.json`

Si algo falla, revisa [`docs/TROUBLESHOOTING.md`](./TROUBLESHOOTING.md).

## Caso 6: ⚙️ Reconfigurar bot de forma segura

Objetivo:
- Cambiar host, usuario SSH, modo auth u otros parametros.

Pasos:
1. Ejecuta `/setup`.
2. Ingresa `SETUP_PASSWORD`.
3. Completa el flujo.
4. El bot guarda `.env` actualizado.
5. Reinicia el bot si hace falta.
