"""Імпортує кожен модуль усіх сервісів.

Навіщо: поки тестів немає, це найпростіший спосіб переконатися,
що в каркасі немає помилок у шляхах імпорту, синтаксисі чи циклічних залежностях.
Запуск: uv run python scripts/check_imports.py
"""

import importlib
import pkgutil
import sys

PACKAGES = ["contracts", "ingest_service", "writer_service", "query_service"]


def main() -> int:
    failed = 0
    for package_name in PACKAGES:
        package = importlib.import_module(package_name)
        for module in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
            try:
                importlib.import_module(module.name)
            except Exception as exc:  # noqa: BLE001 — хочемо побачити будь-яку помилку
                failed += 1
                print(f"FAIL {module.name}: {exc!r}")
    print("OK" if not failed else f"Помилок: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
