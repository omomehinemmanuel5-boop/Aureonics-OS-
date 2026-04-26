from __future__ import annotations

import hashlib
from pathlib import Path

AUREONICS_CORE_LOCK = True

# Frozen core logic surface (governor, CBF, triad kernel, semantic bridge harness).
CORE_LOCK_MANIFEST: dict[str, str] = {
    "app/services/governor_service.py": "9a50c5712fb3e72625b88f1bf5aebb60ecfde629877d4b173310371c4e03dcfa",
    "app/services/cbf_service.py": "0291c2cbdc3fe2a5a7672e4636e8011fe3432158cbe25ff3b4bd567664963a83",
    "sovereign_kernel_v2.py": "5d78c5d93e473c9be90d0fecf46e8de936e290ae6207eba7b99c9990afa20d83",
    "scripts/run_semantic_bridge_ab.py": "9600d00e0830c4a3924140595283e0f433190a7eaf1051f7d7eb38c1d58ea73c",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_core_lock(repo_root: Path | None = None) -> None:
    if not AUREONICS_CORE_LOCK:
        return

    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    mismatches: list[str] = []

    for rel_path, expected_hash in CORE_LOCK_MANIFEST.items():
        target = root / rel_path
        if not target.exists():
            mismatches.append(f"missing:{rel_path}")
            continue

        actual_hash = _sha256(target)
        if actual_hash != expected_hash:
            mismatches.append(rel_path)

    assert not mismatches, (
        "AUREONICS_CORE_LOCK violation: structural edits detected in frozen core files: "
        + ", ".join(mismatches)
    )
