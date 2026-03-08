from __future__ import annotations

from pathlib import Path

from brich_telegram_bot.local_recipes import execute_local_recipe, list_local_recipe_names


class DummyController:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def send_key(self, value: str) -> None:
        self.calls.append(("key", value))

    def send_combo(self, value: str) -> None:
        self.calls.append(("combo", value))

    def send_text(self, value: str) -> None:
        self.calls.append(("text", value))


def test_list_local_recipe_names_returns_sorted(tmp_path: Path) -> None:
    recipes = tmp_path / "recipes.json"
    recipes.write_text(
        '{"zeta":[{"kind":"key","value":"ENTER"}],"alpha":[{"kind":"combo","value":"CTRL+L"}]}',
        encoding="utf-8",
    )
    assert list_local_recipe_names(recipes) == ["alpha", "zeta"]


def test_execute_local_recipe_runs_steps(tmp_path: Path) -> None:
    recipes = tmp_path / "recipes.json"
    recipes.write_text(
        (
            "{"
            '"demo":['
            '{"kind":"combo","value":"CTRL+L"},'
            '{"kind":"text","value":"https://example.com"},'
            '{"kind":"key","value":"ENTER"}'
            "]"
            "}"
        ),
        encoding="utf-8",
    )
    controller = DummyController()
    steps = execute_local_recipe(recipes, "demo", controller)
    assert steps == 3
    assert controller.calls == [
        ("combo", "CTRL+L"),
        ("text", "https://example.com"),
        ("key", "ENTER"),
    ]
