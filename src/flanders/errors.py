"""Exception hierarchy. Each class carries the CLI exit code it maps to (FR39)."""


class FlandersError(Exception):
    exit_code = 1


class ConfigError(FlandersError):
    exit_code = 2


class DependencyRejectedError(FlandersError):
    """A dependency rejected the parameters FLANDERS passed through (FR40)."""

    exit_code = 3

    def __init__(self, tool: str, section: str, detail: str):
        self.tool, self.section, self.detail = tool, section, detail
        super().__init__(
            f"{tool} rejected its parameters (from `{section}:` in the config): {detail}"
        )


class UpstreamDriftError(FlandersError):
    """Dependency output could not be parsed; the whole run halts (FR41)."""

    exit_code = 4


class RunLockedError(FlandersError):
    exit_code = 5


class ReferenceDataError(FlandersError):
    exit_code = 6


class RunCancelled(FlandersError):
    exit_code = 130


class TaskFailure(FlandersError):
    """A per-tag failure. Caught by the engine, recorded, never raised past it."""

    def __init__(self, reason: str, detail: str = ""):
        self.reason, self.detail = reason, detail
        super().__init__(f"{reason}: {detail}" if detail else reason)
