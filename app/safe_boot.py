"""Safe boot helpers for runtime dependencies.

This module isolates optional imports so the API can boot even when
certain subsystems (kernel, routers, external services) are unavailable.
"""

from __future__ import annotations

import importlib
from typing import Any


def safe_import(module_name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(module_name), None
    except Exception as exc:  # pragma: no cover - defensive startup path
        return None, f"{module_name} import failed: {exc}"


def safe_build_kernel() -> tuple[Any | None, str | None]:
    module, err = safe_import("sovereign_kernel_v2")
    if err:
        return None, err
    try:
        return module.SovereignKernel(), None
    except Exception as exc:  # pragma: no cover - defensive startup path
        return None, f"kernel init failed: {exc}"


def safe_supabase_client(url: str, key: str) -> tuple[Any | None, str | None]:
    module, err = safe_import("supabase")
    if err:
        return None, err
    try:
        return module.create_client(url, key), None
    except Exception as exc:  # pragma: no cover - defensive startup path
        return None, f"supabase init failed: {exc}"


def safe_router(module_name: str, attr_name: str = "router") -> tuple[Any | None, str | None]:
    module, err = safe_import(module_name)
    if err:
        return None, err
    router = getattr(module, attr_name, None)
    if router is None:
        return None, f"{module_name}.{attr_name} missing"
    return router, None
