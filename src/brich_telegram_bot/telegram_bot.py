from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .config import AppConfig, is_valid_host, load_config, write_env_file
from .constants import (
    AUTH_MODE_ROWS,
    KEY_MENU_ROWS,
    LOG_LEVEL_ROWS,
    MACRO_MENU_FOOTER,
    MAIN_MENU_ROWS,
    SETUP_CONFIRM_ROWS,
    SETUP_RESET_CONFIRM_ROWS,
)
from .remote_control import RemoteControlError, RemoteKeyboardController
from .security import normalize_macro_name, validate_project_path

logger = logging.getLogger(__name__)

CHAT_KEY_PENDING_ACTION = "pending_action"
CHAT_KEY_SETUP = "setup_state"
CHAT_KEY_MACRO_OPTIONS = "macro_options"

ACTION_TEXT = "text"
ACTION_KEY = "key"
ACTION_COMBO = "combo"
ACTION_MACRO = "macro"

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
            "- Estado\n"
            "- Ajustes"
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

        setup_state = context.chat_data.get(CHAT_KEY_SETUP)
        if isinstance(setup_state, dict) and setup_state.get("active"):
            await self._handle_setup_step(update, context, text)
            return

        if not await self._ensure_authorized(update):
            return

        pending_action = context.chat_data.get(CHAT_KEY_PENDING_ACTION)
        if isinstance(pending_action, str):
            await self._handle_pending_action(update, context, pending_action, text)
            return

        if text == "Texto":
            context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_TEXT
            await self._reply(update, "Escribe el texto a enviar (max 500 chars):")
            return
        if text == "Teclas":
            context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_KEY
            await self._reply(update, "Selecciona o escribe una tecla:", reply_markup=self._key_menu())
            return
        if text == "Combos":
            context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_COMBO
            await self._reply(update, "Escribe un combo, ejemplo: CTRL+ALT+T")
            return
        if text == "Macros":
            await self._begin_macro_flow(update, context)
            return
        if text == "Estado":
            await self._send_status(update)
            return
        if text == "Ajustes":
            await self._send_settings(update)
            return
        if text.lower() == "cancelar":
            await self.handle_cancel(update, context)
            return

        await self._reply(
            update,
            "No reconozco esa opcion. Usa /help o el menu principal.",
            reply_markup=self._main_menu(),
        )

    async def _handle_pending_action(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        action: str,
        text: str,
    ) -> None:
        if text.lower() == "cancelar":
            await self.handle_cancel(update, context)
            return

        if not self._config.remote_ready:
            context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            await self._reply(update, "Configuracion remota incompleta. Usa /setup.")
            return

        try:
            if action == ACTION_TEXT:
                sent_text = await asyncio.to_thread(self._controller().send_text, text)
                await self._reply(
                    update,
                    f"Texto enviado: {sent_text!r}",
                    reply_markup=self._main_menu(),
                )
                context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            elif action == ACTION_KEY:
                sent_key = await asyncio.to_thread(self._controller().send_key, text)
                await self._reply(update, f"Tecla enviada: {sent_key}", reply_markup=self._main_menu())
                context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            elif action == ACTION_COMBO:
                sent_combo = await asyncio.to_thread(self._controller().send_combo, text)
                await self._reply(update, f"Combo enviado: {sent_combo}", reply_markup=self._main_menu())
                context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            elif action == ACTION_MACRO:
                if text == "Listar macros":
                    await self._begin_macro_flow(update, context)
                    return
                macro_name = await asyncio.to_thread(self._controller().run_macro, text)
                await self._reply(
                    update,
                    f"Macro ejecutada: {macro_name}",
                    reply_markup=self._main_menu(),
                )
                context.chat_data.pop(CHAT_KEY_PENDING_ACTION, None)
            else:
                await self._reply(update, "Estado interno invalido. Usa /cancel.")
                return
        except (ValueError, RemoteControlError) as exc:
            await self._reply(update, f"Error: {exc}")
            return

    async def _begin_macro_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._config.remote_ready:
            await self._reply(update, "Configuracion remota incompleta. Usa /setup.")
            return
        context.chat_data[CHAT_KEY_PENDING_ACTION] = ACTION_MACRO
        macros: list[str] = []
        try:
            macros = await asyncio.to_thread(self._controller().list_macros)
        except RemoteControlError as exc:
            await self._reply(update, f"No se pudieron listar macros: {exc}")
        context.chat_data[CHAT_KEY_MACRO_OPTIONS] = macros
        if macros:
            await self._reply(
                update,
                "Selecciona una macro o escribe el nombre manualmente:",
                reply_markup=self._macro_menu(macros),
            )
            return
        await self._reply(
            update,
            "No se detectaron macros automaticamente. Escribe el nombre de la macro:",
            reply_markup=ReplyKeyboardMarkup(MACRO_MENU_FOOTER, resize_keyboard=True),
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
        ble_json = json.dumps(ble, ensure_ascii=True, indent=2) if ble else "{}"
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
            f"LOG_LEVEL={payload.get('LOG_LEVEL')}"
        )

    async def _reply(self, update: Update, text: str, reply_markup: Any | None = None) -> None:
        if not update.message:
            return
        await update.message.reply_text(text, reply_markup=reply_markup)

    def _controller(self) -> RemoteKeyboardController:
        return RemoteKeyboardController(self._config)

    def _main_menu(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(MAIN_MENU_ROWS, resize_keyboard=True)

    def _key_menu(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(KEY_MENU_ROWS, resize_keyboard=True)

    def _macro_menu(self, macros: list[str]) -> ReplyKeyboardMarkup:
        rows: list[list[str]] = []
        chunk_size = 3
        for index in range(0, len(macros), chunk_size):
            rows.append(macros[index : index + chunk_size])
        rows.extend(MACRO_MENU_FOOTER)
        return ReplyKeyboardMarkup(rows, resize_keyboard=True)
