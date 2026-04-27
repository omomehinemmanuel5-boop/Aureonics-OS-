"""Safe runtime bootstrap helpers for optional dependencies."""

from __future__ import annotations

import importlib
from typing import Any


class SafeBootResult(dict):
    """Small typed-ish mapping for bootstrap outcomes."""


def load_kernel_safely() -> SafeBootResult:
    """Attempt to load the sovereign kernel without crashing app startup."""
    try:
        kernel_mod = importlib.import_module("sovereign_kernel_v2")
        kernel = kernel_mod.SovereignKernel()
        return SafeBootResult(ok=True, kernel=kernel, error=None)
    except Exception as exc:  # pragma: no cover - defensive bootstrap guard
        return SafeBootResult(ok=False, kernel=None, error=f"kernel init failed: {exc}")


def load_router_safely(module_path: str, attr_name: str = "router") -> SafeBootResult:
    """Import routers defensively so optional modules never break deployment."""
    try:
        module = importlib.import_module(module_path)
        router: Any = getattr(module, attr_name)
        return SafeBootResult(ok=True, router=router, error=None)
    except Exception as exc:  # pragma: no cover - defensive bootstrap guard
        return SafeBootResult(ok=False, router=None, error=f"router load failed ({module_path}): {exc}")
