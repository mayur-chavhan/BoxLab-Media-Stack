from __future__ import annotations

import os
import sys
from functools import lru_cache
from typing import Literal


class UnsupportedPlatformError(RuntimeError):
    """Raised when the host OS or architecture is not supported."""
    pass


OSType = Literal["darwin", "linux"]
ArchType = Literal["x86_64", "arm64", "armv7", "armv6", "i686"]

_ARCH_NORMALIZATION = {
    "x86_64": "x86_64",
    "amd64": "x86_64",
    "arm64": "arm64",
    "aarch64": "arm64",
    "armv8": "arm64",
    "armv7l": "armv7",
    "armv7": "armv7",
    "armv6l": "armv6",
    "armv6": "armv6",
    "i686": "i686",
    "i386": "i686",
}


@lru_cache()
def get_os() -> OSType:
    """Return the current operating system in lowercase ("darwin" or "linux")."""
    system = sys.platform
    normalized = "darwin" if system.startswith("darwin") or system == "mac" else (
        "linux" if system.startswith("linux") else None
    )
    if not normalized:
        raise UnsupportedPlatformError(f"Unsupported OS: {system}")
    return normalized  # type: ignore[return-value]


@lru_cache()
def get_arch() -> ArchType:
    """Return the normalized CPU architecture."""
    machine = os.uname().machine.lower()
    normalized = _ARCH_NORMALIZATION.get(machine)
    if not normalized:
        raise UnsupportedPlatformError(f"Unsupported architecture: {machine}")
    return normalized  # type: ignore[return-value]


def get_gum_asset_name(version: str, os_name: OSType | None = None, arch: ArchType | None = None) -> str:
    """
    Build the Gum release asset name for the detected platform.
    
    Examples:
        gum_0.17.0_Darwin_arm64.tar.gz
        gum_0.17.0_Linux_x86_64.tar.gz
    """
    os_value = (os_name or get_os()).capitalize()
    arch_value = arch or get_arch()
    return f"gum_{version}_{os_value}_{arch_value}.tar.gz"
