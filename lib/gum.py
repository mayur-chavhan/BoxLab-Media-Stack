from __future__ import annotations

import re
import shutil
import subprocess
from typing import Optional, Sequence, Tuple


def parse_version(raw: str) -> Optional[Tuple[int, int, int]]:
    """Extract a semantic version tuple from gum --version output."""
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", raw)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def version_to_str(version: Sequence[int]) -> str:
    """Convert a version tuple back into dotted string form."""
    return ".".join(str(part) for part in version)


def get_gum_version() -> Optional[Tuple[int, int, int]]:
    """Return the installed Gum version, if available."""
    if shutil.which("gum") is None:
        return None
    try:
        result = subprocess.run(
            ["gum", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return parse_version(result.stdout) or parse_version(result.stderr)
