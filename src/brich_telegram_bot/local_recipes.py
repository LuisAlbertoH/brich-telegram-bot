from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Literal

from .security import normalize_macro_name, normalize_simple_key, normalize_combo, sanitize_text_input

RecipeStepKind = Literal["key", "combo", "text", "wait"]


class LocalRecipeError(RuntimeError):
    """Raised when local automation recipes are invalid or cannot run."""


def list_local_recipe_names(recipes_path: Path) -> list[str]:
    recipes = load_local_recipes(recipes_path)
    return sorted(recipes.keys())


def load_local_recipes(recipes_path: Path) -> dict[str, list[dict[str, object]]]:
    if not recipes_path.exists():
        return {}

    try:
        parsed = json.loads(recipes_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LocalRecipeError(f"JSON invalido en {recipes_path}: {exc}") from exc

    if not isinstance(parsed, dict):
        raise LocalRecipeError("El archivo de recipes debe ser un objeto JSON (name -> steps)")

    recipes: dict[str, list[dict[str, object]]] = {}
    for raw_name, raw_steps in parsed.items():
        if not isinstance(raw_name, str):
            raise LocalRecipeError("Cada nombre de recipe debe ser string")
        recipe_name = normalize_macro_name(raw_name)
        if not isinstance(raw_steps, list):
            raise LocalRecipeError(f"Recipe '{recipe_name}' debe ser lista de pasos")
        validated_steps = [_validate_step(recipe_name, raw_step) for raw_step in raw_steps]
        recipes[recipe_name] = validated_steps
    return recipes


def execute_local_recipe(
    recipes_path: Path,
    recipe_name: str,
    controller: object,
) -> int:
    recipes = load_local_recipes(recipes_path)
    normalized_name = normalize_macro_name(recipe_name)
    if normalized_name not in recipes:
        raise LocalRecipeError(f"Recipe local no encontrada: {normalized_name}")

    steps = recipes[normalized_name]
    for step in steps:
        kind = step["kind"]
        if kind == "wait":
            wait_ms = int(step["ms"])
            time.sleep(wait_ms / 1000)
            continue

        value = str(step["value"])
        if kind == "key":
            controller.send_key(value)
        elif kind == "combo":
            controller.send_combo(value)
        elif kind == "text":
            controller.send_text(value)
        else:
            raise LocalRecipeError(f"Tipo de paso no soportado: {kind}")
    return len(steps)


def _validate_step(recipe_name: str, raw_step: object) -> dict[str, object]:
    if not isinstance(raw_step, dict):
        raise LocalRecipeError(f"Recipe '{recipe_name}': cada paso debe ser objeto")

    kind = raw_step.get("kind")
    if kind not in {"key", "combo", "text", "wait"}:
        raise LocalRecipeError(
            f"Recipe '{recipe_name}': kind invalido '{kind}', usa key/combo/text/wait"
        )

    if kind == "wait":
        raw_ms = raw_step.get("ms", 200)
        if not isinstance(raw_ms, int) or raw_ms < 0 or raw_ms > 30000:
            raise LocalRecipeError(
                f"Recipe '{recipe_name}': wait.ms debe ser entero entre 0 y 30000"
            )
        return {"kind": "wait", "ms": raw_ms}

    raw_value = raw_step.get("value")
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise LocalRecipeError(
            f"Recipe '{recipe_name}': pasos '{kind}' requieren campo value (string)"
        )

    if kind == "key":
        normalized = normalize_simple_key(raw_value)
    elif kind == "combo":
        normalized = normalize_combo(raw_value)
    else:
        normalized = sanitize_text_input(raw_value)
    return {"kind": kind, "value": normalized}
