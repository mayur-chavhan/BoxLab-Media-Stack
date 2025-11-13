"""
Configuration models, defaults, and persistence helpers for BoxLab setup.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict, fields
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar

DEFAULT_TIMEZONE = "Europe/Amsterdam"
_STATE_DIR = Path.home() / ".config" / "boxlab"
_STATE_FILE = _STATE_DIR / "installer-state.json"
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = _PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE = _PROJECT_ROOT / ".env.example"
_T = TypeVar("_T")


@dataclass
class VPNSettings:
    """Configuration for VPN (Gluetun) setup."""
    enabled: bool = False
    provider: str = "mullvad"
    vpn_type: str = "wireguard"
    wireguard_private_key: str = ""
    wireguard_addresses: str = "10.64.0.2/32,4.0.0.2/32"
    server_cities: str = ""
    wireguard_mtu: str = "1280"
    public_ip_api: str = ""
    public_ip_token: str = ""


@dataclass
class WizarrSettings:
    """Configuration for Wizarr invitation system."""
    app_url: str = ""
    disable_builtin_auth: bool = False


@dataclass
class JellystatSettings:
    """Configuration for Jellystat analytics."""
    db_name: str = "jfstat"
    db_user: str = "jfstat"
    db_password: str = "change-me"
    jwt_secret: str = "change-me"


@dataclass
class SetupContext:
    """Complete setup configuration for BoxLab stack."""
    timezone: str
    root_dir: str
    compose_path: str
    services: List[str]
    plex_claim: str = ""
    vpn: VPNSettings = field(default_factory=VPNSettings)
    wizarr: Optional[WizarrSettings] = None
    jellystat: Optional[JellystatSettings] = None

    def env_overrides(self) -> Dict[str, str]:
        """Export commonly reused values for installers."""
        overrides = {"TZ": self.timezone}
        if self.plex_claim:
            overrides["PLEX_CLAIM"] = self.plex_claim
        return overrides


def _normalize_dict(data: Optional[Dict[str, object]], cls: Type[_T]) -> _T:
    """Create a dataclass instance from persisted data."""
    if not data:
        return cls()  # type: ignore[arg-type]
    allowed = {f.name for f in fields(cls)}
    filtered = {key: value for key, value in data.items() if key in allowed}
    return cls(**filtered)  # type: ignore[arg-type]


def load_saved_context() -> Optional[SetupContext]:
    """Load the most recent installer context from disk."""
    if not _STATE_FILE.exists():
        return None
    try:
        with _STATE_FILE.open("r") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None

    try:
        services = [str(entry) for entry in raw.get("services", [])]
        root_dir = raw.get("root_dir", str((Path.home() / "boxlab").resolve()))
        compose_path = raw.get("compose_path") or str(Path(root_dir) / "docker-compose.yml")
        return SetupContext(
            timezone=raw.get("timezone", DEFAULT_TIMEZONE),
            root_dir=root_dir,
            compose_path=compose_path,
            services=services,
            plex_claim=raw.get("plex_claim", ""),
            vpn=_normalize_dict(raw.get("vpn"), VPNSettings),
            wizarr=_normalize_dict(raw.get("wizarr"), WizarrSettings) if raw.get("wizarr") else None,
            jellystat=_normalize_dict(raw.get("jellystat"), JellystatSettings) if raw.get("jellystat") else None,
        )
    except Exception:
        return None


def save_context(context: SetupContext) -> None:
    """Persist the current installer context for future runs."""
    data = asdict(context)
    data["saved_at"] = datetime.utcnow().isoformat()
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = _STATE_FILE.with_suffix(".tmp")
    with temp_file.open("w") as handle:
        json.dump(data, handle, indent=2)
    temp_file.replace(_STATE_FILE)


def _parse_env_lines(lines: List[str]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def ensure_env_example() -> None:
    """Ensure the repository ships with a sample .env describing supported keys."""
    if ENV_EXAMPLE_FILE.exists():
        return
    content = """# BoxLab configuration example
# Copy this file to .env and adjust values as needed.
BOXLAB_ROOT_DIR=/home/boxlab
BOXLAB_COMPOSE_PATH=/home/boxlab/docker-compose.yml
BOXLAB_TIMEZONE=Europe/Amsterdam
BOXLAB_SERVICES=plex,sonarr,radarr
BOXLAB_VPN_ENABLED=false
BOXLAB_VPN_PROVIDER=mullvad
BOXLAB_VPN_TYPE=wireguard
"""
    ENV_EXAMPLE_FILE.write_text(content.strip() + "\n", encoding="utf-8")


def load_env_preferences() -> Dict[str, str]:
    """Load values from .env if present."""
    ensure_env_example()
    if not ENV_FILE.exists():
        return {}
    with ENV_FILE.open("r", encoding="utf-8") as handle:
        return _parse_env_lines(handle.readlines())


def context_from_env(values: Dict[str, str]) -> Optional[SetupContext]:
    """Convert .env key-values into a SetupContext."""
    if not values:
        return None
    root_dir = values.get("BOXLAB_ROOT_DIR", str((Path.home() / "boxlab").resolve()))
    compose_path = values.get("BOXLAB_COMPOSE_PATH") or str(Path(root_dir) / "docker-compose.yml")
    services = [
        entry.strip()
        for entry in values.get("BOXLAB_SERVICES", "").split(",")
        if entry.strip()
    ]
    vpn_enabled = values.get("BOXLAB_VPN_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    vpn = VPNSettings(
        enabled=vpn_enabled,
        provider=values.get("BOXLAB_VPN_PROVIDER", "mullvad"),
        vpn_type=values.get("BOXLAB_VPN_TYPE", "wireguard"),
        wireguard_private_key=values.get("BOXLAB_WIREGUARD_PRIVATE_KEY", ""),
        wireguard_addresses=values.get("BOXLAB_WIREGUARD_ADDRESSES", "10.64.0.2/32,4.0.0.2/32"),
        server_cities=values.get("BOXLAB_VPN_CITIES", ""),
        wireguard_mtu=values.get("BOXLAB_VPN_MTU", "1280"),
        public_ip_api=values.get("BOXLAB_PUBLIC_IP_API", ""),
        public_ip_token=values.get("BOXLAB_PUBLIC_IP_TOKEN", ""),
    )
    wizarr = None
    if values.get("BOXLAB_WIZARR_URL"):
        wizarr = WizarrSettings(
            app_url=values.get("BOXLAB_WIZARR_URL", ""),
            disable_builtin_auth=values.get("BOXLAB_WIZARR_DISABLE_AUTH", "false").lower()
            in {"1", "true", "yes", "on"},
        )
    jellystat = None
    if values.get("BOXLAB_JELLYSTAT_DB"):
        jellystat = JellystatSettings(
            db_name=values.get("BOXLAB_JELLYSTAT_DB", "jfstat"),
            db_user=values.get("BOXLAB_JELLYSTAT_USER", "jfstat"),
            db_password=values.get("BOXLAB_JELLYSTAT_PASSWORD", "change-me"),
            jwt_secret=values.get("BOXLAB_JELLYSTAT_JWT", "change-me"),
        )

    return SetupContext(
        timezone=values.get("BOXLAB_TIMEZONE", DEFAULT_TIMEZONE),
        root_dir=root_dir,
        compose_path=compose_path,
        services=services,
        plex_claim=values.get("BOXLAB_PLEX_CLAIM", ""),
        vpn=vpn,
        wizarr=wizarr,
        jellystat=jellystat,
    )


def save_env_preferences(context: SetupContext) -> None:
    """Persist key configuration fields to .env for manual edits between runs."""
    values = load_env_preferences()
    values.update(
        {
            "BOXLAB_ROOT_DIR": context.root_dir,
            "BOXLAB_COMPOSE_PATH": context.compose_path,
            "BOXLAB_TIMEZONE": context.timezone,
            "BOXLAB_SERVICES": ",".join(context.services),
            "BOXLAB_PLEX_CLAIM": context.plex_claim or "",
            "BOXLAB_VPN_ENABLED": "true" if context.vpn.enabled else "false",
            "BOXLAB_VPN_PROVIDER": context.vpn.provider,
            "BOXLAB_VPN_TYPE": context.vpn.vpn_type,
            "BOXLAB_WIZARR_URL": context.wizarr.app_url if context.wizarr else "",
            "BOXLAB_WIZARR_DISABLE_AUTH": "true" if (context.wizarr and context.wizarr.disable_builtin_auth) else "false",
            "BOXLAB_JELLYSTAT_DB": context.jellystat.db_name if context.jellystat else "",
            "BOXLAB_JELLYSTAT_USER": context.jellystat.db_user if context.jellystat else "",
            "BOXLAB_JELLYSTAT_PASSWORD": context.jellystat.db_password if context.jellystat else "",
            "BOXLAB_JELLYSTAT_JWT": context.jellystat.jwt_secret if context.jellystat else "",
        }
    )
    ordered = [
        "BOXLAB_ROOT_DIR",
        "BOXLAB_COMPOSE_PATH",
        "BOXLAB_TIMEZONE",
        "BOXLAB_SERVICES",
        "BOXLAB_PLEX_CLAIM",
        "BOXLAB_VPN_ENABLED",
        "BOXLAB_VPN_PROVIDER",
        "BOXLAB_VPN_TYPE",
        "BOXLAB_WIZARR_URL",
        "BOXLAB_WIZARR_DISABLE_AUTH",
        "BOXLAB_JELLYSTAT_DB",
        "BOXLAB_JELLYSTAT_USER",
        "BOXLAB_JELLYSTAT_PASSWORD",
        "BOXLAB_JELLYSTAT_JWT",
    ]
    seen = set()
    lines = []
    for key in ordered:
        if key in values:
            lines.append(f"{key}={values[key]}")
            seen.add(key)
    for key, value in values.items():
        if key in seen:
            continue
        lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
