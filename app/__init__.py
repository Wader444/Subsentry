"""SubSentry package init — loads `.env` before anything reads credentials.

Why this exists: `python-dotenv` is in requirements.txt but nothing in the
starter ever called it, so `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` in
`.env` were silently ignored and `get_client()` fell back to the mock
client — the app would look like it was on the sandbox while running the
mock. This loader is stdlib-only (works before `pip install -r
requirements.txt`) and walks up from this file to find `.env` at the
project root, the same pattern as the CartPilot `.env` fix on 2026-11-06.
It never overwrites a variable already set in the real environment, and
it never prints a value.
"""
import os

_ENV_LOADED = False


def _load_env():
    """Load KEY=VALUE lines from the nearest `.env` above this file."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    here = os.path.dirname(os.path.abspath(__file__))
    directory = here
    while True:
        candidate = os.path.join(directory, ".env")
        if os.path.isfile(candidate):
            _parse_env_file(candidate)
            return
        parent = os.path.dirname(directory)
        if parent == directory:
            return
        directory = parent


def _parse_env_file(path):
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value


_load_env()
