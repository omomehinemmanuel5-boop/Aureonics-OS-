from __future__ import annotations

import os

REQUIRED_ENV = [
    "LEX_ENV",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "STRIPE_WEBHOOK_SECRET",
]


def validate_env() -> list[str]:
    missing = [key for key in REQUIRED_ENV if not os.getenv(key)]
    return missing
