from __future__ import annotations

import hashlib
from pathlib import Path

AUREONICS_CORE_LOCK = True
AUREONICS_CORE_VERSION = "v1.1"

# Frozen core logic surface (governor, CBF, triad kernel, semantic bridge harness).
CORE_MANIFEST_V1_0: dict[str, str] = {
    "app/services/governor_service.py": "9a50c5712fb3e72625b88f1bf5aebb60ecfde629877d4b173310371c4e03dcfa",
    "app/services/cbf_service.py": "0291c2cbdc3fe2a5a7672e4636e8011fe3432158cbe25ff3b4bd567664963a83",
    "sovereign_kernel_v2.py": "5d78c5d93e473c9be90d0fecf46e8de936e290ae6207eba7b99c9990afa20d83",
    "scripts/run_semantic_bridge_ab.py": "9600d00e0830c4a3924140595283e0f433190a7eaf1051f7d7eb38c1d58ea73c",
}

CORE_MANIFEST_V1_1: dict[str, str] = {
    "app/services/governor_service.py": "9a50c5712fb3e72625b88f1bf5aebb60ecfde629877d4b173310371c4e03dcfa",
    "app/services/cbf_service.py": "0291c2cbdc3fe2a5a7672e4636e8011fe3432158cbe25ff3b4bd567664963a83",
    "sovereign_kernel_v2.py": "2c0410c69b80555da01df674c358a44af1b3c303caf8afb18746a267609a37d0",
    "scripts/run_semantic_bridge_ab.py": "9600d00e0830c4a3924140595283e0f433190a7eaf1051f7d7eb38c1d58ea73c",
}

ACTIVE_MANIFEST: dict[str, str] = CORE_MANIFEST_V1_1


def compute_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_core_lock(repo_root: Path | None = None) -> None:
    if not AUREONICS_CORE_LOCK:
        return

    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()

    for file, expected_hash in ACTIVE_MANIFEST.items():
        target = root / file
        assert target.exists(), f"AUREONICS_CORE_LOCK violation: {file}"
        actual_hash = compute_hash(target)
        assert actual_hash == expected_hash, f"AUREONICS_CORE_LOCK violation: {file}"
