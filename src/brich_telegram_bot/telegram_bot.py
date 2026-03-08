from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from .camera_capture import CameraCaptureError, CapturedPhoto, capture_webcam_photo
from .config import AppConfig, is_valid_host, load_config, write_env_file
from .constants import (
    AUTH_MODE_ROWS,
    BUTTON_ALIASES,
    CAMERA_MENU_ROWS,
    COMBO_SUGGESTION_ROWS,
    COMMON_COMBO_EXAMPLES,
    COMMON_MACRO_EXAMPLES,
    INLINE_COMBO_SHORTCUTS,
    KEY_MENU_ROWS,
    KEYBOARD_KEYS,
    LOG_LEVEL_ROWS,
    MACRO_MENU_FOOTER,
    MAIN_MENU_ROWS,
    NAVIGATION_COMBO_EXAMPLES,
    NAVIGATION_MENU_ROWS,
    SETUP_CONFIRM_ROWS,
    SETUP_RESET_CONFIRM_ROWS,
    TEXT_SHORTCUT_ROWS,
)
from .local_recipes import LocalRecipeError, execute_local_recipe, list_local_recipe_names
from .remote_control import RemoteControlError, RemoteKeyboardController
from .security import validate_project_path

logger = logging.getLogger(__name__)

CHAT_KEY_PENDING_ACTION = "pending_action"
CHAT_KEY_SETUP = "setup_state"
CHAT_KEY_MACRO_OPTIONS = "macro_options"
CHAT_KEY_CAMERA_AUTO = "camera_auto_after_navigation"

ACTION_TEXT = "text"
ACTION_KEY = "key"
ACTION_COMBO = "combo"
ACTION_MACRO = "macro"
ACTION_NAVIGATE = "navigate"
ACTION_CAMERA = "camera"

SETUP_STEP_CONFIRM_RESET = "confirm_reset"
SETUP_STEP_PASSWORD = "setup_password"
SETUP_STEP_HOST = "rpi_host"
SETUP_STEP_PORT = "rpi_port"
SETUP_STEP_USER = "rpi_user"
SETUP_STEP_AUTH_MODE = "rpi_auth_mode"
SETUP_STEP_AUTH_SECRET = "rpi_auth_secret"
SETUP_STEP_PROJECT_PATH = "rpi_project_path"
SETUP_STEP_TIMEOUT = "ssh_timeout"
SETUP_STEP_LOG_LEVEL = "log_level"
SETUP_STEP_CONFIRM_SAVE = "confirm_save"


class BrichTelegramBot:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._application = Application.builder().token(config.telegram_bot_token).build()
        self._register_handlers()

    @property
    def config(self) -> AppConfig:
        return self._config

    def _register_handlers(self) -> None:
        self._application.add_handler(CommandHandler("start", self.handle_start))
        self._application.add_handler(CommandHandler("help", self.handle_help))
        self._application.add_handler(CommandHandler("setup", self.handle_setup))
        self._application.add_handler(CommandHandler("cancel", self.handle_cancel))
        self._application.add_handler(CallbackQueryHandler(self.handle_inline_callback))
        self._application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))

    def run(self) -> None:
        logger.info(
            "bot_starting",
            extra={
                "authorized_chat_id": self._config.authorized_chat_id,
                "env_file": str(self._config.env_file),
                "remote_ready": self._config.remote_ready,
            },
        )
        # Python 3.14 no crea un loop por defecto en el hilo principal.
        # python-telegram-bot espera un loop activo al llamar run_polling.
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        self._application.run_polling(drop_pending_updates=False)

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._allow_start_or_setup(update):
            return
        if not self._config.fully_configured:
            await self._reply(
                update,
                "Bot sin configuracion completa. Ejecuta /setup para iniciar la configuracion guiada.",
            )
            if not self._config.env_file_exists:
                await self._begin_setup(update, context, from_start=True)
            return
        await self._reply(
            update,
            "Bot listo. Usa los botones para enviar acciones al teclado remoto.",
            reply_markup=self._main_menu(),
        )

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._allow_start_or_setup(update):
            return
        help_text = (
            "Comandos disponibles:\n"
            "/start - Mostrar menu principal\n"
            "/help - Mostrar ayuda\n"
            "/setup - Iniciar o reconfigurar setup\n"
            "/cancel - Cancelar flujo actual\n\n"
            "Menu principal:\n"
            "- Texto\n"
            "- Teclas\n"
            "- Combos\n"
            "- Macros\n"
            "- Camara\n"
            "- Estado\n"
            "- Ajustes\n"
            "- NAVEGAR\n\n"
            "Tips:\n"
            "- Texto soporta acentos y caracteres especiales.\n"
            "- En Teclas/Combos/Macros usa los botones de ayuda para ejemplos.\n"
            "- Camara captura una foto desde la webcam local y la envia al chat.\n"
            "- En Camara puedes activar auto-foto despues de navegar.\n"
            "- En Macros usa Ideas macros para crear automatizaciones simples.\n"
            "- NAVEGAR esta enfocado en atajos de pantalla/ventanas.\n"
            "- Puedes probar teclas nuevas con formato seguro (ej: PRINT_SCREEN)."
        )
        await self._reply(update, help_text, reply_markup=self._main_menu())

    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_data = context.chat_data
        chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
        chat_data.pop(CHAT_KEY_SETUP, None)
        chat_data.pop(CHAT_KEY_MACRO_OPTIONS, None)
        await self._reply(
            update,
            "Operacion cancelada.",
            reply_markup=self._main_menu() if self._config.fully_configured else ReplyKeyboardRemove(),
        )

    async def handle_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._allow_setup_entry(update):
            return
        await self._begin_setup(update, context, from_start=False)

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message:
            return
        text = (update.message.text or "").strip()
        if not text:
            return
        canonical_text = self._canonical_input(text)

        setup_state = context.chat_data.get(CHAT_KEY_SETUP)
        if isinstance(setup_state, dict) and setup_state.get("active"):
            await self._handle_setup_step(update, context, text)
            return

        if not await self._ensure_authorized(update):
            return

        pending_action = context.chat_data.get(CHAT_KEY_PENDING_ACTION)
        if isinstance(pending_action, str):
            await self._handle_pending_action(update, context, pending_action, canonical_text)
            return

        lower_text = canonical_text.lower()
        if lower_text in {"cancelar", "menu principal"}:
            await self.handle_cancel(update, context)
            return

        if canonical_text == "Texto":
            context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_TEXT
            await self._reply(
                update,
                "Modo Texto:\n"
                "- Escribe cualquier texto, incluidos acentos y caracteres especiales.\n"
                "- Se enviara tal cual al script remoto.\n"
                "- Usa Cancelar para salir.",
                reply_markup=self._text_menu(),
            )
            return
        if canonical_text == "Teclas":
            context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_KEY
            await self._reply(
                update,
                self._key_help_text(),
                reply_markup=self._key_menu(),
            )
            return
        if canonical_text == "Combos":
            context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_COMBO
            await self._reply(
                update,
                self._combo_help_text(),
                reply_markup=self._combo_menu(),
            )
            await self._reply(
                update,
                "Atajos inline (tap para ejecutar de inmediato):",
                reply_markup=self._combo_inline_menu(),
            )
            return
        if canonical_text == "Macros":
            await self._begin_macro_flow(update, context)
            return
        if canonical_text == "Camara":
            context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_CAMERA
            await self._reply(
                update,
                self._camera_help_text(),
                reply_markup=self._camera_menu(),
            )
            await self._reply(
                update,
                self._camera_auto_status_text(context),
                reply_markup=self._camera_menu(),
            )
            return
        if canonical_text == "Estado":
            await self._send_status(update)
            return
        if canonical_text == "Ajustes":
            await self._send_settings(update)
            return
        if canonical_text == "NAVEGAR":
            context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_NAVIGATE
            await self._reply(
                update,
                self._navigation_help_text(),
                reply_markup=self._navigation_menu(),
            )
            await self._reply(
                update,
                self._camera_auto_status_text(context),
                reply_markup=self._navigation_menu(),
            )
            await self._reply(
                update,
                self._navigation_shortcuts_text(),
                reply_markup=self._navigation_menu(),
            )
            return
        await self._reply(
            update,
            "No reconozco esa opcion. Usa /help o responde con un boton del menu.",
            reply_markup=self._main_menu(),
        )

    async def handle_inline_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not await self._ensure_authorized(update):
            return

        data = query.data or ""
        if data == "combo:help":
            await self._reply(update, self._combo_help_text(), reply_markup=self._combo_menu())
            return
        if not data.startswith("combo:"):
            return

        if not self._config.remote_ready:
            await self._reply(update, "Configuracion remota incompleta. Usa /setup.")
            return

        combo = data.split(":", 1)[1]
        try:
            sent_combo = await asyncio.to_thread(self._controller().send_combo, combo)
        except (ValueError, RemoteControlError) as exc:
            await self._reply(update, f"Error: {exc}\n{self._action_hint(ACTION_COMBO)}", reply_markup=self._combo_menu())
            return

        context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
        await self._reply(
            update,
            self._dynamic_success_message(ACTION_COMBO, f"Combo enviado desde inline keyboard: {sent_combo}"),
            reply_markup=self._main_menu(),
        )

    async def _handle_pending_action(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        action: str,
        text: str,
    ) -> None:
        canonical_text = self._canonical_input(text)
        lower_text = canonical_text.lower()
        if lower_text in {"cancelar", "menu principal"}:
            await self.handle_cancel(update, context)
            return

        remote_actions = {ACTION_TEXT, ACTION_KEY, ACTION_COMBO, ACTION_MACRO, ACTION_NAVIGATE}
        if action in remote_actions and not self._config.remote_ready:
            context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            await self._reply(update, "Configuracion remota incompleta. Usa /setup.")
            return

        try:
            if action == ACTION_TEXT:
                sent_text = await asyncio.to_thread(self._controller().send_text, canonical_text)
                await self._reply(
                    update,
                    self._dynamic_success_message(
                        ACTION_TEXT,
                        f'Texto enviado correctamente.\nContenido: "{self._preview_text(sent_text)}"',
                    ),
                    reply_markup=self._main_menu(),
                )
                context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            elif action == ACTION_KEY:
                if canonical_text == "Listar teclas":
                    await self._reply(update, self._list_keys_text(), reply_markup=self._key_menu())
                    return
                if canonical_text == "Ayuda teclas":
                    await self._reply(update, self._key_help_text(), reply_markup=self._key_menu())
                    return
                sent_key = await asyncio.to_thread(self._controller().send_key, canonical_text)
                await self._reply(
                    update,
                    self._dynamic_success_message(ACTION_KEY, f"Tecla enviada: {sent_key}"),
                    reply_markup=self._main_menu(),
                )
                context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            elif action == ACTION_COMBO:
                if canonical_text == "Ejemplos combos":
                    await self._reply(update, self._combo_examples_text(), reply_markup=self._combo_menu())
                    await self._reply(update, "Atajos inline:", reply_markup=self._combo_inline_menu())
                    return
                if canonical_text == "Ayuda combos":
                    await self._reply(update, self._combo_help_text(), reply_markup=self._combo_menu())
                    await self._reply(update, "Atajos inline:", reply_markup=self._combo_inline_menu())
                    return
                sent_combo = await asyncio.to_thread(
                    self._controller().send_combo,
                    self._normalize_navigation_input(canonical_text),
                )
                await self._reply(
                    update,
                    self._dynamic_success_message(ACTION_COMBO, f"Combo enviado: {sent_combo}"),
                    reply_markup=self._main_menu(),
                )
                context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            elif action == ACTION_MACRO:
                if canonical_text == "Listar macros":
                    await self._begin_macro_flow(update, context)
                    return
                if canonical_text == "Ideas macros":
                    await self._reply(
                        update,
                        self._macro_ideas_text(),
                        reply_markup=self._macro_menu_hint(),
                    )
                    return
                if canonical_text == "Plantilla recipe":
                    await self._reply(
                        update,
                        self._macro_recipe_template_text(),
                        reply_markup=self._macro_menu_hint(),
                    )
                    return
                if canonical_text == "Ayuda macros":
                    await self._reply(update, self._macro_help_text(), reply_markup=self._macro_menu_hint())
                    return
                macro_meta = context.chat_data.get(CHAT_KEY_MACRO_OPTIONS, {})
                local_recipes = set(macro_meta.get("local", [])) if isinstance(macro_meta, dict) else set()
                if canonical_text.startswith("LOCAL:"):
                    local_name = canonical_text.split(":", 1)[1].strip()
                    steps_count = await asyncio.to_thread(
                        execute_local_recipe,
                        self._config.local_recipes_path,
                        local_name,
                        self._controller(),
                    )
                    await self._reply(
                        update,
                        self._dynamic_success_message(
                            ACTION_MACRO,
                            f"Recipe local ejecutada: {local_name} ({steps_count} pasos)",
                        ),
                        reply_markup=self._main_menu(),
                    )
                    context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
                    return
                if canonical_text in local_recipes:
                    steps_count = await asyncio.to_thread(
                        execute_local_recipe,
                        self._config.local_recipes_path,
                        canonical_text,
                        self._controller(),
                    )
                    await self._reply(
                        update,
                        self._dynamic_success_message(
                            ACTION_MACRO,
                            f"Recipe local ejecutada: {canonical_text} ({steps_count} pasos)",
                        ),
                        reply_markup=self._main_menu(),
                    )
                    context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
                    return

                macro_name = await asyncio.to_thread(self._controller().run_macro, canonical_text)
                await self._reply(
                    update,
                    self._dynamic_success_message(ACTION_MACRO, f"Macro ejecutada: {macro_name}"),
                    reply_markup=self._main_menu(),
                )
                context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            elif action == ACTION_NAVIGATE:
                if canonical_text == "Ayuda navegar":
                    await self._reply(
                        update,
                        self._navigation_help_text(),
                        reply_markup=self._navigation_menu(),
                    )
                    return
                if canonical_text == "Atajos navegar":
                    await self._reply(
                        update,
                        self._navigation_shortcuts_text(),
                        reply_markup=self._navigation_menu(),
                    )
                    return
                if canonical_text == "Auto tras navegar: ON":
                    self._set_camera_auto_enabled(context, True)
                    await self._reply(
                        update,
                        "Auto-foto tras navegacion activada.",
                        reply_markup=self._navigation_menu(),
                    )
                    return
                if canonical_text == "Auto tras navegar: OFF":
                    self._set_camera_auto_enabled(context, False)
                    await self._reply(
                        update,
                        "Auto-foto tras navegacion desactivada.",
                        reply_markup=self._navigation_menu(),
                    )
                    return
                if canonical_text in {"Tomar foto", "Tomar otra"}:
                    try:
                        captured = await asyncio.to_thread(
                            capture_webcam_photo,
                            self._config.camera_device_index,
                            self._config.camera_warmup_frames,
                            self._config.camera_timeout_sec,
                        )
                        await self._reply_photo(update, captured, reply_markup=self._navigation_menu())
                    except CameraCaptureError as exc:
                        await self._reply(
                            update,
                            f"No se pudo tomar foto: {exc}",
                            reply_markup=self._navigation_menu(),
                        )
                    return

                normalized_input = self._normalize_navigation_input(canonical_text)
                if "+" in normalized_input:
                    sent = await asyncio.to_thread(self._controller().send_combo, normalized_input)
                    detail = f"Atajo de navegacion enviado: {sent}"
                else:
                    sent = await asyncio.to_thread(self._controller().send_key, normalized_input)
                    detail = f"Tecla de navegacion enviada: {sent}"

                await self._reply(
                    update,
                    self._dynamic_success_message(
                        ACTION_NAVIGATE,
                        f"{detail}\nPuedes seguir navegando o usar Cancelar.",
                    ),
                    reply_markup=self._navigation_menu(),
                )
                if self._camera_auto_enabled(context):
                    try:
                        captured = await asyncio.to_thread(
                            capture_webcam_photo,
                            self._config.camera_device_index,
                            self._config.camera_warmup_frames,
                            self._config.camera_timeout_sec,
                        )
                        await self._reply_photo(update, captured, reply_markup=self._navigation_menu())
                    except CameraCaptureError as exc:
                        await self._reply(
                            update,
                            f"Auto-foto tras navegar fallida: {exc}",
                            reply_markup=self._navigation_menu(),
                        )
            elif action == ACTION_CAMERA:
                if canonical_text == "Ayuda camara":
                    await self._reply(
                        update,
                        self._camera_help_text(),
                        reply_markup=self._camera_menu(),
                    )
                    return
                if canonical_text == "Estado camara":
                    await self._reply(
                        update,
                        self._camera_auto_status_text(context),
                        reply_markup=self._camera_menu(),
                    )
                    return
                if canonical_text == "Auto tras navegar: ON":
                    self._set_camera_auto_enabled(context, True)
                    await self._reply(
                        update,
                        "Auto-foto tras navegacion activada.",
                        reply_markup=self._camera_menu(),
                    )
                    return
                if canonical_text == "Auto tras navegar: OFF":
                    self._set_camera_auto_enabled(context, False)
                    await self._reply(
                        update,
                        "Auto-foto tras navegacion desactivada.",
                        reply_markup=self._camera_menu(),
                    )
                    return
                if canonical_text not in {"Tomar foto", "Tomar otra"}:
                    await self._reply(
                        update,
                        "Usa los botones de camara para capturar una foto.",
                        reply_markup=self._camera_menu(),
                    )
                    return
                try:
                    captured = await asyncio.to_thread(
                        capture_webcam_photo,
                        self._config.camera_device_index,
                        self._config.camera_warmup_frames,
                        self._config.camera_timeout_sec,
                    )
                    await self._reply_photo(update, captured, reply_markup=self._camera_menu())
                except CameraCaptureError as exc:
                    await self._reply(
                        update,
                        f"No se pudo tomar foto: {exc}",
                        reply_markup=self._camera_menu(),
                    )
                    return
            else:
                await self._reply(update, "Estado interno invalido. Usa /cancel.")
                return
        except (ValueError, RemoteControlError, LocalRecipeError) as exc:
            await self._reply(update, f"Error: {exc}\n{self._action_hint(action)}", reply_markup=self._action_menu(action))
            return

    async def _begin_macro_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._config.remote_ready:
            await self._reply(update, "Configuracion remota incompleta. Usa /setup.")
            return
        context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_MACRO
        remote_macros: list[str] = []
        local_recipes: list[str] = []
        try:
            remote_macros = await asyncio.to_thread(self._controller().list_macros)
        except RemoteControlError as exc:
            await self._reply(update, f"No se pudieron listar macros: {exc}")
        try:
            local_recipes = await asyncio.to_thread(list_local_recipe_names, self._config.local_recipes_path)
        except LocalRecipeError as exc:
            await self._reply(update, f"No se pudieron cargar recipes locales: {exc}")

        context.chat_data[CHAT_KEY_MACRO_OPTIONS] = {
            "remote": remote_macros,
            "local": local_recipes,
        }
        merged_options = [*remote_macros, *[f"LOCAL:{name}" for name in local_recipes]]

        if merged_options:
            summary_lines = [
                "Modo Macros:",
                f"- Macros remotas: {len(remote_macros)}",
                f"- Recipes locales: {len(local_recipes)}",
                "- Usa Ideas macros para aprender a crear automatizaciones simples.",
            ]
            await self._reply(
                update,
                "\n".join(summary_lines),
                reply_markup=self._macro_menu(merged_options),
            )
            return
        await self._reply(
            update,
            "No se detectaron macros remotas ni recipes locales.\n"
            "Usa Ideas macros para ver plantillas y como crearlas.",
            reply_markup=self._macro_menu_hint(),
        )

    async def _send_status(self, update: Update) -> None:
        if not self._config.remote_ready:
            await self._reply(update, "Configuracion remota incompleta. Usa /setup.")
            return
        try:
            snapshot = await asyncio.to_thread(self._controller().status_snapshot)
        except RemoteControlError as exc:
            await self._reply(update, f"No se pudo consultar estado: {exc}")
            return

        service = snapshot.get("service", {})
        ble = snapshot.get("ble", {})
        ble_json = json.dumps(ble, ensure_ascii=False, indent=2) if ble else "{}"
        message = (
            "Estado remoto:\n"
            f"- Servicio active: {service.get('active', 'unknown')}\n"
            f"- Servicio enabled: {service.get('enabled', 'unknown')}\n"
            f"- BLE status file: {ble_json}"
        )
        await self._reply(update, message, reply_markup=self._main_menu())

    async def _send_settings(self, update: Update) -> None:
        summary = self._config.redacted_summary()
        await self._reply(
            update,
            f"Ajustes actuales:\n{summary}\n\nUsa /setup para reconfigurar.",
            reply_markup=self._main_menu(),
        )

    async def _allow_start_or_setup(self, update: Update) -> bool:
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is None:
            return False
        if self._config.authorized_chat_id is not None and chat_id != self._config.authorized_chat_id:
            await self._reply(update, "Acceso denegado. Este bot es privado para un solo chat autorizado.")
            return False
        return True

    async def _allow_setup_entry(self, update: Update) -> bool:
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is None:
            return False
        if self._config.authorized_chat_id is not None and chat_id != self._config.authorized_chat_id:
            await self._reply(update, "Acceso denegado. Solo el chat autorizado puede reconfigurar.")
            return False
        return True

    async def _ensure_authorized(self, update: Update) -> bool:
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is None:
            return False
        if self._config.authorized_chat_id is None:
            await self._reply(update, "Bot no configurado. Ejecuta /setup.")
            return False
        if chat_id != self._config.authorized_chat_id:
            await self._reply(update, "Acceso denegado. Este bot es privado para un solo chat autorizado.")
            return False
        return True

    async def _begin_setup(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        from_start: bool,
    ) -> None:
        chat_data = context.chat_data
        chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
        chat_data.pop(CHAT_KEY_MACRO_OPTIONS, None)

        setup_data: dict[str, Any] = {
            "active": True,
            "step": "",
            "payload": {},
        }

        if self._config.env_file_exists and self._config.fully_configured:
            setup_data["step"] = SETUP_STEP_CONFIRM_RESET
            chat_data[CHAT_KEY_SETUP] = setup_data
            await self._reply(
                update,
                "Ya existe una configuracion. Escribe SI para sobrescribir o NO para cancelar.",
                reply_markup=ReplyKeyboardMarkup(SETUP_RESET_CONFIRM_ROWS, resize_keyboard=True),
            )
            return

        setup_data["step"] = SETUP_STEP_PASSWORD
        setup_data["payload"]["password_mode"] = "verify" if self._config.setup_password else "create"
        chat_data[CHAT_KEY_SETUP] = setup_data
        if from_start:
            await self._reply(update, "Iniciando setup inicial...")
        await self._prompt_setup_password(update, setup_data["payload"]["password_mode"])

    async def _prompt_setup_password(self, update: Update, mode: str) -> None:
        if mode == "verify":
            await self._reply(
                update,
                "Ingresa SETUP_PASSWORD para continuar:",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        await self._reply(
            update,
            "No hay SETUP_PASSWORD cargado. Define una nueva (minimo 6 chars):",
            reply_markup=ReplyKeyboardRemove(),
        )

    async def _handle_setup_step(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
    ) -> None:
        setup_state = context.chat_data.get(CHAT_KEY_SETUP)
        if not isinstance(setup_state, dict):
            await self._reply(update, "No hay setup activo. Usa /setup.")
            return

        step = setup_state.get("step")
        payload = setup_state.setdefault("payload", {})

        if step == SETUP_STEP_CONFIRM_RESET:
            upper = text.strip().upper()
            if upper == "NO":
                context.chat_data.pop(CHAT_KEY_SETUP, None)
                await self._reply(update, "Reconfiguracion cancelada.", reply_markup=self._main_menu())
                return
            if upper != "SI":
                await self._reply(update, "Responde SI o NO.")
                return
            setup_state["step"] = SETUP_STEP_PASSWORD
            payload["password_mode"] = "verify" if self._config.setup_password else "create"
            await self._prompt_setup_password(update, payload["password_mode"])
            return

        if step == SETUP_STEP_PASSWORD:
            password_mode = payload.get("password_mode", "verify")
            if password_mode == "verify":
                if text != self._config.setup_password:
                    context.chat_data.pop(CHAT_KEY_SETUP, None)
                    await self._reply(update, "SETUP_PASSWORD invalido. Setup cancelado.")
                    return
                payload["SETUP_PASSWORD"] = self._config.setup_password
            else:
                if len(text) < 6:
                    await self._reply(update, "La nueva clave debe tener al menos 6 caracteres.")
                    return
                payload["SETUP_PASSWORD"] = text
            setup_state["step"] = SETUP_STEP_HOST
            await self._reply(update, "RPI_HOST (IP o hostname):")
            return

        if step == SETUP_STEP_HOST:
            if not is_valid_host(text):
                await self._reply(update, "Host invalido. Ejemplo: 192.168.1.50")
                return
            payload["RPI_HOST"] = text
            setup_state["step"] = SETUP_STEP_PORT
            await self._reply(update, "RPI_PORT (default 22):")
            return

        if step == SETUP_STEP_PORT:
            raw_port = text.strip()
            if not raw_port:
                payload["RPI_PORT"] = "22"
            else:
                try:
                    value = int(raw_port)
                    if value < 1 or value > 65535:
                        raise ValueError
                except ValueError:
                    await self._reply(update, "Puerto invalido. Debe estar entre 1 y 65535.")
                    return
                payload["RPI_PORT"] = str(value)
            setup_state["step"] = SETUP_STEP_USER
            await self._reply(update, "RPI_USER (ejemplo: pi):")
            return

        if step == SETUP_STEP_USER:
            if not re.fullmatch(r"^[A-Za-z_][A-Za-z0-9_-]{0,31}$", text):
                await self._reply(update, "Usuario invalido para SSH.")
                return
            payload["RPI_USER"] = text
            setup_state["step"] = SETUP_STEP_AUTH_MODE
            await self._reply(
                update,
                "RPI_AUTH_MODE (password o key):",
                reply_markup=ReplyKeyboardMarkup(AUTH_MODE_ROWS, resize_keyboard=True),
            )
            return

        if step == SETUP_STEP_AUTH_MODE:
            mode = text.strip().lower()
            if mode not in {"password", "key"}:
                await self._reply(update, "Modo invalido. Usa password o key.")
                return
            payload["RPI_AUTH_MODE"] = mode
            setup_state["step"] = SETUP_STEP_AUTH_SECRET
            if mode == "password":
                await self._reply(update, "RPI_PASSWORD:")
            else:
                await self._reply(update, "RPI_SSH_KEY_PATH (ejemplo ~/.ssh/id_ed25519):")
            return

        if step == SETUP_STEP_AUTH_SECRET:
            mode = payload.get("RPI_AUTH_MODE", "")
            if mode == "password":
                if not text:
                    await self._reply(update, "RPI_PASSWORD no puede estar vacio.")
                    return
                payload["RPI_PASSWORD"] = text
                payload["RPI_SSH_KEY_PATH"] = ""
            else:
                key_path = text.strip()
                if not key_path or "\n" in key_path or "\r" in key_path:
                    await self._reply(update, "RPI_SSH_KEY_PATH invalido.")
                    return
                payload["RPI_SSH_KEY_PATH"] = key_path
                payload["RPI_PASSWORD"] = ""
            setup_state["step"] = SETUP_STEP_PROJECT_PATH
            await self._reply(update, "RPI_PROJECT_PATH (ejemplo /home/pi/brich):")
            return

        if step == SETUP_STEP_PROJECT_PATH:
            try:
                payload["RPI_PROJECT_PATH"] = validate_project_path(text)
            except ValueError:
                await self._reply(update, "Ruta invalida. Debe ser absoluta en Linux.")
                return
            setup_state["step"] = SETUP_STEP_TIMEOUT
            await self._reply(update, "SSH_TIMEOUT_SEC (default 10):")
            return

        if step == SETUP_STEP_TIMEOUT:
            raw_timeout = text.strip()
            if not raw_timeout:
                payload["SSH_TIMEOUT_SEC"] = "10"
            else:
                try:
                    timeout_sec = int(raw_timeout)
                    if timeout_sec < 1 or timeout_sec > 120:
                        raise ValueError
                except ValueError:
                    await self._reply(update, "Timeout invalido. Rango 1..120.")
                    return
                payload["SSH_TIMEOUT_SEC"] = str(timeout_sec)
            setup_state["step"] = SETUP_STEP_LOG_LEVEL
            await self._reply(
                update,
                "LOG_LEVEL:",
                reply_markup=ReplyKeyboardMarkup(LOG_LEVEL_ROWS, resize_keyboard=True),
            )
            return

        if step == SETUP_STEP_LOG_LEVEL:
            level = text.strip().upper()
            if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
                await self._reply(update, "LOG_LEVEL invalido.")
                return
            payload["LOG_LEVEL"] = level
            setup_state["step"] = SETUP_STEP_CONFIRM_SAVE
            summary = self._build_setup_summary(update, payload)
            await self._reply(
                update,
                f"Resumen de setup:\n{summary}\n\nEscribe Guardar para persistir o Cancelar.",
                reply_markup=ReplyKeyboardMarkup(SETUP_CONFIRM_ROWS, resize_keyboard=True),
            )
            return

        if step == SETUP_STEP_CONFIRM_SAVE:
            upper_text = text.strip().upper()
            if upper_text == "CANCELAR":
                context.chat_data.pop(CHAT_KEY_SETUP, None)
                await self._reply(update, "Setup cancelado.", reply_markup=self._main_menu())
                return
            if upper_text != "GUARDAR":
                await self._reply(update, "Responde Guardar o Cancelar.")
                return
            try:
                self._persist_setup(update, payload)
            except Exception as exc:
                logger.exception("setup_persist_failed")
                await self._reply(update, f"No se pudo guardar .env: {exc}")
                return

            context.chat_data.pop(CHAT_KEY_SETUP, None)
            await self._reply(
                update,
                "Setup guardado correctamente. El bot ya esta listo.",
                reply_markup=self._main_menu(),
            )
            return

        await self._reply(update, "Setup en estado desconocido. Usa /setup de nuevo.")
        context.chat_data.pop(CHAT_KEY_SETUP, None)

    def _persist_setup(self, update: Update, payload: dict[str, Any]) -> None:
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is None:
            raise RuntimeError("No se pudo detectar chat_id")

        setup_password = payload.get("SETUP_PASSWORD") or self._config.setup_password
        if not setup_password:
            raise RuntimeError("SETUP_PASSWORD no definido")

        values = {
            "TELEGRAM_BOT_TOKEN": self._config.telegram_bot_token,
            "AUTHORIZED_CHAT_ID": str(chat_id),
            "SETUP_PASSWORD": setup_password,
            "RPI_HOST": payload.get("RPI_HOST", ""),
            "RPI_PORT": payload.get("RPI_PORT", "22"),
            "RPI_USER": payload.get("RPI_USER", ""),
            "RPI_AUTH_MODE": payload.get("RPI_AUTH_MODE", "password"),
            "RPI_PASSWORD": payload.get("RPI_PASSWORD", ""),
            "RPI_SSH_KEY_PATH": payload.get("RPI_SSH_KEY_PATH", ""),
            "RPI_PROJECT_PATH": payload.get("RPI_PROJECT_PATH", ""),
            "SSH_TIMEOUT_SEC": payload.get("SSH_TIMEOUT_SEC", "10"),
            "CAMERA_DEVICE_INDEX": str(self._config.camera_device_index),
            "CAMERA_WARMUP_FRAMES": str(self._config.camera_warmup_frames),
            "CAMERA_TIMEOUT_SEC": str(self._config.camera_timeout_sec),
            "LOCAL_RECIPES_PATH": str(self._config.local_recipes_path),
            "LOG_LEVEL": payload.get("LOG_LEVEL", "INFO"),
        }

        write_env_file(values, self._config.env_file)
        self._config = load_config(self._config.env_file)

    def _build_setup_summary(self, update: Update, payload: dict[str, Any]) -> str:
        chat_id = update.effective_chat.id if update.effective_chat else None
        auth_mode = payload.get("RPI_AUTH_MODE", "password")
        auth_secret = "set" if (
            (auth_mode == "password" and payload.get("RPI_PASSWORD"))
            or (auth_mode == "key" and payload.get("RPI_SSH_KEY_PATH"))
        ) else "missing"
        return (
            f"AUTHORIZED_CHAT_ID={chat_id}\n"
            f"RPI_HOST={payload.get('RPI_HOST')}\n"
            f"RPI_PORT={payload.get('RPI_PORT')}\n"
            f"RPI_USER={payload.get('RPI_USER')}\n"
            f"RPI_AUTH_MODE={auth_mode}\n"
            f"RPI_AUTH_SECRET={auth_secret}\n"
            f"RPI_PROJECT_PATH={payload.get('RPI_PROJECT_PATH')}\n"
            f"SSH_TIMEOUT_SEC={payload.get('SSH_TIMEOUT_SEC')}\n"
            f"CAMERA_DEVICE_INDEX={self._config.camera_device_index}\n"
            f"CAMERA_WARMUP_FRAMES={self._config.camera_warmup_frames}\n"
            f"CAMERA_TIMEOUT_SEC={self._config.camera_timeout_sec}\n"
            f"LOCAL_RECIPES_PATH={self._config.local_recipes_path}\n"
            f"LOG_LEVEL={payload.get('LOG_LEVEL')}"
        )

    async def _reply(self, update: Update, text: str, reply_markup: Any | None = None) -> None:
        target_message = update.message
        if target_message is None and update.callback_query:
            target_message = update.callback_query.message
        if target_message is None:
            return
        await target_message.reply_text(text, reply_markup=reply_markup)

    async def _reply_photo(
        self,
        update: Update,
        photo: CapturedPhoto,
        reply_markup: Any | None = None,
    ) -> None:
        target_message = update.message
        if target_message is None and update.callback_query:
            target_message = update.callback_query.message
        if target_message is None:
            return

        caption = (
            f"Foto capturada desde webcam local.\n"
            f"Resolucion: {photo.width}x{photo.height}"
        )
        try:
            with photo.path.open("rb") as photo_file:
                await target_message.reply_photo(
                    photo=photo_file,
                    caption=caption,
                    reply_markup=reply_markup,
                )
        finally:
            try:
                photo.path.unlink(missing_ok=True)
            except OSError:
                logger.warning("temporary_photo_cleanup_failed", extra={"path": str(photo.path)})

    def _dynamic_success_message(self, action: str, detail: str) -> str:
        templates = {
            ACTION_TEXT: [
                "Listo, texto enviado.",
                "Hecho. Texto transmitido.",
                "Perfecto, texto ejecutado en Raspberry.",
            ],
            ACTION_KEY: [
                "Accion completada.",
                "Tecla procesada correctamente.",
                "Listo, la tecla fue enviada.",
            ],
            ACTION_COMBO: [
                "Combinacion aplicada.",
                "Combo ejecutado correctamente.",
                "Listo, combo enviado al host remoto.",
            ],
            ACTION_MACRO: [
                "Macro ejecutada con exito.",
                "Listo, macro disparada.",
                "Accion de macro completada.",
            ],
            ACTION_NAVIGATE: [
                "Movimiento aplicado.",
                "Atajo de navegacion ejecutado.",
                "Navegacion enviada correctamente.",
            ],
            ACTION_CAMERA: [
                "Camara lista.",
                "Captura completada.",
                "Foto tomada correctamente.",
            ],
        }
        prefix = random.choice(templates.get(action, ["Operacion completada."]))
        return f"{prefix}\n{detail}"

    def _action_hint(self, action: str) -> str:
        if action == ACTION_TEXT:
            return "Tip: Puedes usar acentos y caracteres especiales. Ejemplo: ping\u00fcino \u00e1\u00e9\u00ed\u00f3\u00fa \u00f1"
        if action == ACTION_KEY:
            return "Tip: Usa botones sugeridos o escribe una tecla en MAYUSCULAS, por ejemplo PRINT_SCREEN."
        if action == ACTION_COMBO:
            return "Tip: Formato valido MOD+KEY, por ejemplo CTRL+ALT+T o GUI+D."
        if action == ACTION_MACRO:
            return "Tip: Usa Listar macros, Ideas macros, Plantilla recipe y Ayuda macros para automatizar."
        if action == ACTION_NAVIGATE:
            return "Tip: En NAVEGAR usa teclas como UP, PGDOWN o atajos como ALT+TAB y GUI+TAB."
        if action == ACTION_CAMERA:
            return "Tip: En Camara puedes usar captura unica o auto-foto tras navegar."
        return "Tip: Usa /help para ver opciones."

    def _preview_text(self, text: str, max_len: int = 120) -> str:
        if len(text) <= max_len:
            return text
        return f"{text[: max_len - 3]}..."

    def _canonical_input(self, text: str) -> str:
        stripped = text.strip()
        return BUTTON_ALIASES.get(stripped, stripped)

    def _action_menu(self, action: str) -> ReplyKeyboardMarkup:
        if action == ACTION_TEXT:
            return self._text_menu()
        if action == ACTION_KEY:
            return self._key_menu()
        if action == ACTION_COMBO:
            return self._combo_menu()
        if action == ACTION_MACRO:
            return self._macro_menu_hint()
        if action == ACTION_NAVIGATE:
            return self._navigation_menu()
        if action == ACTION_CAMERA:
            return self._camera_menu()
        return self._main_menu()

    def _list_keys_text(self) -> str:
        keys_line = ", ".join(self._key_suggestions())
        return (
            "Teclas sugeridas:\n"
            f"{keys_line}\n\n"
            "Tambien puedes escribir una tecla personalizada segura (A-Z, 0-9, _), por ejemplo PRINT_SCREEN."
        )

    def _key_help_text(self) -> str:
        return (
            "Modo Teclas:\n"
            "- Puedes elegir una tecla sugerida desde los botones.\n"
            "- Tambien puedes escribir una tecla nueva en MAYUSCULAS (ej: PRINT_SCREEN).\n"
            "- Formato permitido para teclas personalizadas: letras, numeros y guion bajo."
        )

    def _combo_help_text(self) -> str:
        return (
            "Modo Combos:\n"
            "- Formato: MOD+KEY o MOD+MOD+KEY\n"
            "- MOD validos: CTRL, SHIFT, ALT, GUI\n"
            "- KEY puede ser TAB, ENTER, ESC, F1..F12 o tokens como PRINT_SCREEN\n"
            "- Para tecla Windows usa GUI (ej: GUI+D, GUI+TAB, GUI+LEFT)\n"
            "- Usa Ejemplos combos y atajos inline para respuestas rapidas."
        )

    def _combo_examples_text(self) -> str:
        examples = "\n".join(f"- {combo}" for combo in COMMON_COMBO_EXAMPLES)
        return (
            f"Ejemplos de combos:\n{examples}\n\n"
            "Combos Windows utiles para navegacion/pantallas:\n"
            "- GUI+D (mostrar escritorio)\n"
            "- GUI+TAB (vista tareas)\n"
            "- GUI+LEFT / GUI+RIGHT (ajustar ventana)\n"
            "- GUI+P (cambiar modo de pantalla)\n\n"
            "Puedes enviar otro combo manualmente."
        )

    def _macro_help_text(self) -> str:
        examples = "\n".join(f"- {macro}" for macro in COMMON_MACRO_EXAMPLES)
        return (
            "Modo Macros:\n"
            "- Usa Listar macros para consultar las disponibles en Raspberry.\n"
            "- Usa Ideas macros para ver recipes listas para automatizar tareas.\n"
            "- Usa Plantilla recipe para copiar una base JSON.\n"
            "- Puedes ejecutar macros remotas o recipes locales prefijadas como LOCAL:nombre.\n"
            "- Para recipes locales, crea/edita el archivo JSON en:\n"
            f"  {self._config.local_recipes_path}\n"
            "- Ejemplos remotos comunes:\n"
            f"{examples}\n"
            "- Ejemplos de recetas: abrir navegador con URL, abrir terminal y ejecutar comando."
        )

    def _macro_ideas_text(self) -> str:
        return (
            "Ideas de automatizacion con macros/recipes:\n"
            "- Abrir navegador + URL:\n"
            "  GUI+R -> text 'chrome https://tu-url' -> ENTER\n"
            "- Abrir terminal + ejecutar comando:\n"
            "  CTRL+ALT+T -> wait -> text 'python3 script.py' -> ENTER\n"
            "- Cambiar ventana y escribir:\n"
            "  ALT+TAB -> wait -> text 'mensaje'\n\n"
            "Para recipes locales:\n"
            f"1) Copia automation_recipes.example.json a {self._config.local_recipes_path.name}\n"
            "2) Edita pasos (key/combo/text/wait)\n"
            "3) Vuelve a entrar a Macros y ejecuta LOCAL:nombre_recipe"
        )

    def _macro_recipe_template_text(self) -> str:
        template = (
            "{\n"
            '  "abrir_navegador_url": [\n'
            '    {"kind": "combo", "value": "GUI+R"},\n'
            '    {"kind": "wait", "ms": 500},\n'
            '    {"kind": "text", "value": "chrome https://tu-url"},\n'
            '    {"kind": "key", "value": "ENTER"}\n'
            "  ],\n"
            '  "abrir_terminal_y_correr": [\n'
            '    {"kind": "combo", "value": "CTRL+ALT+T"},\n'
            '    {"kind": "wait", "ms": 900},\n'
            '    {"kind": "text", "value": "python3 tu_script.py"},\n'
            '    {"kind": "key", "value": "ENTER"}\n'
            "  ]\n"
            "}"
        )
        return (
            "Plantilla base para recipes locales:\n"
            f"- Guarda este contenido en {self._config.local_recipes_path}\n"
            "- Reglas: kind en key/combo/text/wait, wait usa ms.\n\n"
            f"```json\n{template}\n```"
        )

    def _navigation_help_text(self) -> str:
        return (
            "Modo NAVEGAR:\n"
            "- Enfocado a mover foco, ventanas y pantallas.\n"
            "- Puedes enviar teclas directas (UP, DOWN, TAB, HOME, PGUP, PGDOWN).\n"
            "- Tambien atajos (ALT+TAB, ALT+SHIFT+TAB, WIN+TAB, WIN+LEFT, WIN+RIGHT, WIN+P).\n"
            "- Puedes usar WIN+... o GUI+..., el bot normaliza ambos.\n"
            "- Incluye atajos de camara: Tomar foto y auto-foto ON/OFF sin salir de NAVEGAR.\n"
            "- Este modo se mantiene activo para navegar rapido."
        )

    def _navigation_shortcuts_text(self) -> str:
        combos = "\n".join(f"- {combo}" for combo in NAVIGATION_COMBO_EXAMPLES)
        return (
            "Atajos recomendados para navegacion:\n"
            f"{combos}\n\n"
            "Extras utiles:\n"
            "- F6 / SHIFT+TAB para mover foco en apps.\n"
            "- CTRL+L para enfocar barra de direccion (navegadores/exploradores).\n"
            "- GUI+P para gestion de pantallas."
        )

    def _camera_help_text(self) -> str:
        return (
            "Modo Camara:\n"
            "- Tomar foto/Tomar otra: captura unica manual.\n"
            "- Auto tras navegar ON/OFF: habilita captura automatica despues de cada accion en NAVEGAR.\n"
            "- Estado camara: muestra modo actual.\n"
            "- El archivo se envia al chat y luego se elimina del temporal.\n"
            "- Si falla, revisa permisos de camara o si otra app la esta usando."
        )

    def _camera_auto_enabled(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return bool(context.chat_data.get(CHAT_KEY_CAMERA_AUTO, False))

    def _set_camera_auto_enabled(self, context: ContextTypes.DEFAULT_TYPE, enabled: bool) -> None:
        context.chat_data[CHAT_KEY_CAMERA_AUTO] = enabled

    def _camera_auto_status_text(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        mode = "ON" if self._camera_auto_enabled(context) else "OFF"
        return f"Estado auto-foto tras navegar: {mode}"

    def _normalize_navigation_input(self, raw_text: str) -> str:
        normalized = raw_text.strip().upper()
        normalized = normalized.replace("WIN+", "GUI+")
        aliases = {
            "PAGEUP": "PGUP",
            "PAGE DOWN": "PGDOWN",
            "PAGEDOWN": "PGDOWN",
            "PAGE UP": "PGUP",
            "RE PAG": "PGUP",
            "AV PAG": "PGDOWN",
        }
        return aliases.get(normalized, normalized)

    def _controller(self) -> RemoteKeyboardController:
        return RemoteKeyboardController(self._config)

    def _main_menu(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(MAIN_MENU_ROWS, resize_keyboard=True)

    def _text_menu(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(TEXT_SHORTCUT_ROWS, resize_keyboard=True)

    def _key_menu(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(KEY_MENU_ROWS, resize_keyboard=True)

    def _combo_menu(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(COMBO_SUGGESTION_ROWS, resize_keyboard=True)

    def _combo_inline_menu(self) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        for row in INLINE_COMBO_SHORTCUTS:
            buttons = [
                InlineKeyboardButton(label, callback_data=f"combo:{combo}")
                for label, combo in row
            ]
            rows.append(buttons)
        rows.append([InlineKeyboardButton("Ayuda combos", callback_data="combo:help")])
        return InlineKeyboardMarkup(rows)

    def _macro_menu_hint(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(MACRO_MENU_FOOTER, resize_keyboard=True)

    def _navigation_menu(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(NAVIGATION_MENU_ROWS, resize_keyboard=True)

    def _camera_menu(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(CAMERA_MENU_ROWS, resize_keyboard=True)

    def _key_suggestions(self) -> list[str]:
        return list(KEYBOARD_KEYS)

    def _macro_menu(self, macros: list[str]) -> ReplyKeyboardMarkup:
        rows: list[list[str]] = []
        chunk_size = 3
        for index in range(0, len(macros), chunk_size):
            rows.append(macros[index : index + chunk_size])
        rows.extend(MACRO_MENU_FOOTER)
        return ReplyKeyboardMarkup(rows, resize_keyboard=True)
