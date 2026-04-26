from pathlib import Path

from app.core_lock import AUREONICS_CORE_LOCK, CORE_LOCK_MANIFEST, assert_core_lock


def test_core_lock_enabled():
    assert AUREONICS_CORE_LOCK is True


def test_core_lock_manifest_targets_exist():
    root = Path(__file__).resolve().parents[1]
    for rel_path in CORE_LOCK_MANIFEST:
        assert (root / rel_path).exists()


def test_core_lock_assertion_passes_current_repo_state():
    root = Path(__file__).resolve().parents[1]
    assert_core_lock(root)
