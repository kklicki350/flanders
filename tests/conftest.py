import os
import tempfile
from pathlib import Path

# The workspace (and therefore the database path) must be set before Django loads settings.
_WS = Path(tempfile.mkdtemp(prefix="flanders-test-ws-"))
os.environ.setdefault("FLANDERS_WORKSPACE", str(_WS))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flanders.web.settings")
