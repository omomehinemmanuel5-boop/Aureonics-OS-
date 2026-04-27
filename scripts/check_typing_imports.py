#!/usr/bin/env python3
"""Fail if typing symbols are used without explicit typing imports."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REQUIRED_SYMBOLS = ("Literal", "Optional", "Dict", "List", "Union", "Any")
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}


class TypingImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.used: set[str] = set()
        self.imported: set[str] = set()
        self.typing_aliases: set[str] = set()

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "typing":
            for alias in node.names:
                if alias.name == "*":
                    self.imported.update(REQUIRED_SYMBOLS)
                    continue
                imported_name = alias.asname or alias.name
                if alias.name in REQUIRED_SYMBOLS and imported_name == alias.name:
                    self.imported.add(alias.name)
                if alias.name == "typing":
                    self.typing_aliases.add(imported_name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "typing":
                self.typing_aliases.add(alias.asname or "typing")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in REQUIRED_SYMBOLS:
            self.used.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name) and node.value.id in self.typing_aliases:
            if node.attr in REQUIRED_SYMBOLS:
                self.used.add(node.attr)
                self.imported.add(node.attr)
        self.generic_visit(node)


def iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def check_file(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []

    visitor = TypingImportVisitor()
    visitor.visit(tree)

    missing = sorted(symbol for symbol in visitor.used if symbol not in visitor.imported)
    return missing


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    failures: list[tuple[str, list[str]]] = []

    for py_file in iter_python_files(repo_root):
        missing = check_file(py_file)
        if missing:
            failures.append((str(py_file.relative_to(repo_root)), missing))

    if failures:
        print("Missing typing imports detected:")
        for rel_path, symbols in failures:
            print(f" - {rel_path}: {', '.join(symbols)}")
        return 1

    print("Typing import guard passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
