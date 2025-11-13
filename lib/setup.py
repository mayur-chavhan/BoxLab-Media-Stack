from __future__ import annotations

import json
import os
import shutil
import stat
import tarfile
import tempfile
from pathlib import Path
from typing import Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from .constants import GUM_MIN_VERSION
    from .gum import get_gum_version, version_to_str
    from .platform import UnsupportedPlatformError, get_gum_asset_name
except ImportError:
    from constants import GUM_MIN_VERSION  # type: ignore
    from gum import get_gum_version, version_to_str  # type: ignore
    from platform import UnsupportedPlatformError, get_gum_asset_name  # type: ignore

GITHUB_REPO = "charmbracelet/gum"
USER_AGENT = "BoxLab-Installer"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = PROJECT_ROOT / "bin"


class GumSetupError(RuntimeError):
    """Raised when Gum cannot be downloaded or installed."""
    pass


def _cache_dir() -> Path:
    base = os.environ.get("BOXLAB_CACHE_DIR")
    if base:
        return Path(base).expanduser()
    return Path.home() / ".cache" / "boxlab" / "gum"


def _http_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise GumSetupError(f"Failed to query Gum releases ({exc.code})") from exc
    except URLError as exc:
        raise GumSetupError("Failed to reach GitHub for Gum release info") from exc


def _http_download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=120) as response, open(destination, "wb") as fh:
            shutil.copyfileobj(response, fh)
    except HTTPError as exc:
        raise GumSetupError(f"Failed to download Gum asset ({exc.code})") from exc
    except URLError as exc:
        raise GumSetupError("Network error while downloading Gum asset") from exc


def _normalize_version(tag_name: str) -> str:
    return tag_name.lstrip("v")


def _fetch_release(version: Optional[str]) -> dict:
    if version:
        return _http_json(f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/v{version}")
    return _http_json(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")


def _select_asset(release: dict, asset_name: str) -> dict:
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            return asset
    raise GumSetupError(f"Gum asset '{asset_name}' not found in release")


def _extract_gum(archive_path: Path, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.isfile()]
        gum_member = next((m for m in members if os.path.basename(m.name) == "gum"), None)
        if not gum_member:
            raise GumSetupError("Downloaded archive did not contain gum binary")
        tar.extract(gum_member, destination_dir)
        extracted_path = destination_dir / gum_member.name
        final_path = destination_dir / "gum"
        extracted_path.rename(final_path)
        final_path.chmod(0o755)
        return final_path


def _copy_to_bin(source: Path) -> Path:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    target_path = BIN_DIR / "gum"
    shutil.copy2(source, target_path)
    target_path.chmod(target_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return target_path


def ensure_gum_binary(min_version: Sequence[int] = GUM_MIN_VERSION) -> Path:
    """
    Ensure a compatible Gum binary is available.
    Downloads and caches the correct release when missing or outdated.
    """
    current_version = get_gum_version()
    gum_path = shutil.which("gum")
    if gum_path and current_version and tuple(current_version) >= tuple(min_version):
        return Path(gum_path)

    desired_version = os.environ.get("BOXLAB_GUM_VERSION")
    release = _fetch_release(desired_version)
    release_version = _normalize_version(release.get("tag_name", ""))

    try:
        asset_name = get_gum_asset_name(release_version)
    except UnsupportedPlatformError as exc:
        raise GumSetupError(str(exc)) from exc

    asset = _select_asset(release, asset_name)
    cache_dir = _cache_dir() / release_version
    cached_binary = cache_dir / "gum"
    if not cached_binary.exists():
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / asset_name
            _http_download(asset["browser_download_url"], archive_path)
            extracted = _extract_gum(archive_path, cache_dir)
            cached_binary = extracted

    installed_path = _copy_to_bin(cached_binary)
    # Verify installation
    refreshed_version = get_gum_version()
    if not refreshed_version or refreshed_version < tuple(min_version):
        raise GumSetupError(
            "Gum installation did not succeed; required version "
            f"{version_to_str(min_version)} not detected."
        )
    return installed_path
