"""Runtime configuration and environment handling."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]

#: Default location for cached API responses (git-ignored).
CACHE_DIR = PACKAGE_DIR / "openai_cache"


class MissingUserError(RuntimeError):
    """Raised when the required ``AIDM_USER`` environment variable is unset."""


def get_aidm_user() -> str:
    """Return the ``AIDM_USER`` secret, or raise a helpful error if missing."""
    user = os.environ.get("AIDM_USER")
    if not user:
        raise MissingUserError(
            "Set the AIDM_USER environment variable with your secret user name "
            "from Moodle (e.g. add it to .env and run with --env-file .env)."
        )
    return user
