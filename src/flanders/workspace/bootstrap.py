"""Initialize Django and the workspace database for headless use (no web server)."""

from __future__ import annotations

import os

_ready = False


def setup(migrate: bool = True) -> None:
    global _ready
    if _ready:
        return
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flanders.web.settings")
    from flanders.workspace.layout import Workspace

    Workspace.default().ensure()
    import django

    django.setup()
    if migrate:
        from django.core.management import call_command

        call_command("migrate", verbosity=0, interactive=False)
    _ready = True
