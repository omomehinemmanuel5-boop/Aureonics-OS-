from __future__ import annotations

import os


REQUIRED_ENV = [
    "LEX_ENV",
    "JWT_SECRET",
    "STRIPE_WEBHOOK_SECRET",
]


def validate_env() -> list[str]:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    return missing
