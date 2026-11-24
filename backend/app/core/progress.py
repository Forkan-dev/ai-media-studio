"""Live progress: long steps call report("Writing draft 1") so the UI can show what is happening."""
from collections.abc import Callable

Report = Callable[[str], None]


def noop(_: str) -> None:
    """Default when nobody listens (CLI, tests)."""
