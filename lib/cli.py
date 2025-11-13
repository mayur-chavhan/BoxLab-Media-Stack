"""
Main CLI workflow orchestration for BoxLab installer.
Coordinates the interactive setup process.
"""
from __future__ import annotations

import getpass
import grp
import os
import pwd
import re
import secrets
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence, Optional

from . import tui
from .catalog import SERVICE_CATEGORIES, Service, expand_dependencies, service_lookup, services_by_category
from .composer import ComposeBuilder
from .config import (
    DEFAULT_TIMEZONE,
    ENV_FILE,
    JellystatSettings,
    SetupContext,
    VPNSettings,
    WizarrSettings,
    context_from_env,
    load_env_preferences,
    load_saved_context,
    save_context,
    save_env_preferences,
)
from .installer import PermissionSetup

VPN_PROVIDERS = [
    ("mullvad", "Mullvad", "Privacy-focused VPN, no account needed"),
    ("protonvpn", "Proton VPN", "Secure VPN with free tier available"),
    ("nordvpn", "NordVPN", "Popular commercial VPN service"),
    ("ivpn", "IVPN", "Privacy-first VPN provider"),
    ("custom", "Custom/Other", "Bring your own provider configuration"),
]

MAIN_MENU = [
    ("initial", "🚀 Initial Setup"),
    ("existing", "🛠 Existing Setup"),
    ("vpn", "🔒 VPN Setup"),
    ("start", "▶️  Start Stack"),
    ("stop", "⏹ Stop Stack"),
    ("uninstall", "🧹 Uninstall Services"),
    ("exit", "Exit"),
]

DOCKER_COMPOSE_CMD: List[str] = ["docker", "compose"]
MENU_LOOKUP = {key: label for key, label in MAIN_MENU}


def run_cli() -> None:
    """Main entry point for the interactive CLI."""
    try:
        tui.ensure_gum_installed()
    except tui.GumNotInstalledError as exc:
        print(exc)
        return

    _configure_docker_runner()

    env_values = load_env_preferences()
    env_context = context_from_env(env_values)
    if env_context:
        _show_env_summary(env_context, str(ENV_FILE))
        if not tui.confirm(
            "Use the values from .env as defaults?",
            affirmative="Use defaults",
            negative="Ignore for now",
            default_yes=True,
        ):
            env_context = None

    current_context = load_saved_context() or env_context

    while True:
        try:
            choice = _prompt_main_menu()
        except tui.UserNavigationBack:
            _announce("Exit", "Exiting BoxLab. See you soon!")
            return
        context: Optional[SetupContext] = None

        if choice == "exit":
            _announce("Exit", "Goodbye! You can re-run ./boxlab anytime.")
            return
        if choice == "initial":
            _announce("Initial Setup", "Starting guided installer.")
            try:
                context = _execute_installer(None)
            except tui.UserNavigationBack:
                _announce("Back", "Returned to main menu.")
                continue
            except KeyboardInterrupt:
                if _handle_keyboard_interrupt():
                    return
                continue
        elif choice == "existing":
            base = current_context or env_context
            if not base:
                tui.error_box("No existing configuration found. Run Initial Setup first.")
                continue
            _announce("Existing Setup", "Updating your saved configuration.")
            try:
                context = _execute_installer(base)
            except tui.UserNavigationBack:
                _announce("Back", "Returned to main menu.")
                continue
            except KeyboardInterrupt:
                if _handle_keyboard_interrupt():
                    return
                continue
        elif choice == "vpn":
            _announce("VPN Setup", "Adjusting VPN configuration.")
            try:
                updated = _handle_vpn_only(current_context or env_context)
            except tui.UserNavigationBack:
                _announce("Back", "Cancelled VPN configuration.")
                continue
            except KeyboardInterrupt:
                if _handle_keyboard_interrupt():
                    return
                continue
            if updated:
                current_context = updated
                env_context = updated
                save_context(updated)
                save_env_preferences(updated)
            continue
        elif choice in {"start", "stop", "uninstall"}:
            _announce(MENU_LOOKUP[choice], "Applying your selection.")
            try:
                updated = _handle_stack_action(choice, current_context or env_context)
            except tui.UserNavigationBack:
                _announce("Back", "Operation cancelled.")
                continue
            except KeyboardInterrupt:
                if _handle_keyboard_interrupt():
                    return
                continue
            if updated:
                current_context = updated
                env_context = updated
                save_context(updated)
                save_env_preferences(updated)
            continue

        if context:
            current_context = context
            env_context = context
            save_context(context)
            save_env_preferences(context)


def _execute_installer(previous: SetupContext | None) -> SetupContext | None:
    """Run the interactive workflow once and return the resulting context."""
    tui.show_banner()

    tui.separator("Service Selection")
    services = prompt_services(previous.services if previous else None)
    tui.separator("Installation Directory")
    root_dir = prompt_root_dir(previous.root_dir if previous else None)
    tui.separator("Compose Destination")
    compose_path = prompt_compose_path(root_dir, previous.compose_path if previous else None)
    services = _reconcile_services_with_existing(services, previous, Path(compose_path))
    if services is None:
        return None

    tui.separator("VPN Configuration")
    vpn_settings = configure_vpn(services, previous.vpn if previous else None)
    tui.separator("Timezone")
    timezone = prompt_timezone(previous.timezone if previous else None)
    tui.separator("Plex Claim Token")
    plex_claim = prompt_plex_claim(services, existing=previous.plex_claim if previous else "")
    tui.separator("Wizarr Setup")
    wizarr_settings = prompt_wizarr_settings(services, previous.wizarr if previous else None)
    tui.separator("Jellystat Setup")
    jellystat_settings = prompt_jellystat_settings(services, previous.jellystat if previous else None)

    context = SetupContext(
        timezone=timezone,
        root_dir=root_dir,
        compose_path=compose_path,
        services=services,
        plex_claim=plex_claim,
        vpn=vpn_settings,
        wizarr=wizarr_settings,
        jellystat=jellystat_settings,
    )

    tui.separator("Summary")
    show_summary(context)
    if not tui.confirm(
        "Ready to generate docker-compose.yml?",
        affirmative="✓ Generate",
        negative="✗ Cancel"
    ):
        tui.error_box("Setup cancelled by user")
        return None

    while True:
        try:
            compose_path = generate_compose(context)
            break
        except PermissionError as exc:
            _show_write_permission_error(context.compose_path, exc)
            context.compose_path = prompt_compose_path(context.root_dir, context.compose_path)
    tui.success_box(f"docker-compose.yml written to {compose_path}")

    if tui.confirm(
        "Set up folders, users, and permissions now? (requires sudo)",
        affirmative="✓ Run setup",
        negative="Skip for now",
    ):
        generate_permissions(context)
        tui.success_box("Folder structure and permissions configured")
    else:
        tui.info_box("You can run permissions setup later by re-running this installer")

    tui.style_block(
        "🎉 Setup Complete!",
        "Your BoxLab Media Stack is ready to deploy.\n\n"
        "Next steps:\n"
        "  1. Review docker-compose.yml\n"
        "  2. Run: docker compose up -d\n"
        "  3. Access your services via the configured ports\n\n"
        "Enjoy your self-hosted media automation stack!",
        color="10"
    )

    return context


def _prompt_main_menu() -> str:
    """Display the primary navigation menu."""
    tui.style_block(
        "📋 BoxLab Control Center",
        "Use ↑↓ to move, Enter to select.\n"
        "You can return here at any time by re-running ./boxlab.",
        color="86",
    )
    tui.info_box("Select an action to perform.")
    labels = [label for _, label in MAIN_MENU]
    choice = tui.choose_one(
        "Choose what you would like to do next",
        labels,
        info="Use the arrow keys, press Enter to confirm.",
        height=len(labels) + 2,
    )
    for key, label in MAIN_MENU:
        if label == choice:
            return key
    return "exit"


def _show_env_summary(context: SetupContext, env_path: str) -> None:
    """Render a styled block describing the detected .env configuration."""
    services = ", ".join(context.services) if context.services else "None selected yet"
    summary = (
        f".env location: {env_path}\n"
        f"Install Path:  {context.root_dir}\n"
        f"Compose File:  {context.compose_path}\n"
        f"Timezone:      {context.timezone}\n"
        f"Services:      {services}\n"
    )
    tui.style_block("Detected existing configuration", summary, color="86")


def _render_service_menu_intro(catalog: Dict[str, List[Service]]) -> None:
    """Render a stylized overview of service categories before selection."""
    lines: List[str] = []
    for key, label in SERVICE_CATEGORIES.items():
        services = catalog.get(key, [])
        if not services:
            continue
        lines.append(f"{label}: {len(services)} apps")
    lines.append("")
    lines.append("Controls: ↑↓ move • Space toggle • Enter confirm")
    tui.style_block("📦 Select Applications", "\n".join(lines), color="86")


def _show_write_permission_error(path: str, error: Exception) -> None:
    """Display guidance when compose generation fails due to permissions."""
    tui.error_box(
        f"Cannot write to {path}: {error}\n"
        "Pick a different location or adjust permissions, e.g.:\n"
        f"  sudo chown -R {getpass.getuser()} {Path(path).parent}"
    )


def _announce(title: str, message: str) -> None:
    """Display a separator and message for navigation feedback."""
    tui.separator(title)
    tui.info_box(message)


def _configure_docker_runner() -> None:
    """Ensure the current user can run docker compose commands."""
    if shutil.which("docker") is None:
        tui.error_box(
            "Docker CLI not found in PATH. Install Docker before running BoxLab."
        )
        raise SystemExit(1)

    global DOCKER_COMPOSE_CMD
    if os.geteuid() == 0:
        DOCKER_COMPOSE_CMD = ["docker", "compose"]
        return

    if _user_in_group("docker"):
        DOCKER_COMPOSE_CMD = ["docker", "compose"]
        return

    if _has_sudo_privileges():
        DOCKER_COMPOSE_CMD = ["sudo", "docker", "compose"]
        tui.info_box("Docker commands will run with sudo privileges.")
        return

    _show_privilege_error()
    raise SystemExit(1)


def _user_in_group(group_name: str) -> bool:
    """Check whether the current user belongs to a given group."""
    try:
        group = grp.getgrnam(group_name)
    except KeyError:
        return False
    user = pwd.getpwuid(os.getuid()).pw_name
    if user in group.gr_mem:
        return True
    return group.gr_gid in os.getgroups()


def _has_sudo_privileges() -> bool:
    """Detect whether sudo is available for the current user."""
    if not shutil.which("sudo"):
        return False
    if _user_in_group("sudo") or _user_in_group("wheel"):
        return True
    try:
        subprocess.run(
            ["sudo", "-n", "true"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _show_privilege_error() -> None:
    """Explain how to obtain sufficient permissions for Docker."""
    message = (
        "BoxLab needs permission to control Docker containers.\n"
        "Run as root, use sudo, or join the docker group:\n"
        "  sudo usermod -aG docker $USER\n"
        "Then log out and back in, or re-run this installer with sudo."
    )
    tui.error_box(message)


def _handle_keyboard_interrupt() -> bool:
    """Gracefully handle Ctrl+C presses. Returns True if we should exit."""
    print()
    if tui.confirm(
        "Detected Ctrl+C. Exit the installer?",
        affirmative="Exit now",
        negative="Resume setup",
        default_yes=False,
    ):
        tui.error_box("Setup cancelled by user")
        return True
    tui.info_box("Resuming installer...")
    return False


def _handle_vpn_only(context: SetupContext | None) -> Optional[SetupContext]:
    """Run just the VPN wizard for existing installs."""
    if not context:
        tui.error_box("Run the initial setup first so we know where your stack lives.")
        return None
    services = list(context.services)
    vpn_settings = configure_vpn(services, context.vpn)
    context.vpn = vpn_settings
    context.services = _dedupe_preserve_order(services)
    tui.success_box("VPN settings updated.")
    return context


def _handle_stack_action(action: str, context: SetupContext | None) -> Optional[SetupContext]:
    """Start, stop, or uninstall services using docker compose."""
    if not context:
        tui.error_box("No configuration available yet. Run Initial Setup first.")
        return None
    compose_path = Path(context.compose_path)
    if not compose_path.exists():
        tui.error_box(f"No docker-compose.yml found at {compose_path}.")
        return context
    services = _parse_compose_services(compose_path)
    if not services:
        tui.error_box("Could not detect services in docker-compose.yml.")
        return context

    selected = _select_services_for_action(services, action)
    if not selected:
        target = services
    else:
        target = selected

    if action == "start":
        if _run_compose_command(compose_path, ["up", "-d", *target]):
            tui.success_box("Stack started successfully.")
        return context
    if action == "stop":
        if _run_compose_command(compose_path, ["stop", *target]):
            tui.success_box("Stack stopped.")
        return context

    # uninstall path
    remove_all = not selected or set(target) == set(services)
    if not tui.confirm(
        "This will remove selected containers. Continue?",
        affirmative="Remove",
        negative="Cancel",
        default_yes=False,
    ):
        return context

    if remove_all:
        cmd = ["down", "--remove-orphans", "--volumes"]
    else:
        cmd = ["rm", "-sf", *target]
    if _run_compose_command(compose_path, cmd):
        tui.success_box("Selected services removed.")
        if remove_all:
            context.services = []
        else:
            context.services = [svc for svc in context.services if svc not in target]
    return context


def _select_services_for_action(services: List[str], action: str) -> List[str]:
    """Prompt the user for which services to target."""
    lookup = service_lookup()
    labels: List[str] = []
    mapping: Dict[str, str] = {}
    for key in services:
        svc = lookup.get(key)
        label = f"{svc.name} ({key})" if svc else key
        labels.append(label)
        mapping[label] = key
    if not labels:
        return []
    choice = tui.choose_many(
        f"Select services to {action}",
        labels,
        info="Press Enter without selecting to target all services.",
        preselected=labels,
    )
    if not choice:
        return []
    return [mapping[label] for label in choice]


def _run_compose_command(compose_path: Path, args: List[str]) -> bool:
    """Execute a docker compose command and return success."""
    if not shutil.which("docker"):
        tui.error_box("Docker CLI was not found in PATH.")
        return False
    cmd = DOCKER_COMPOSE_CMD + ["-f", str(compose_path)] + args
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        tui.error_box(f"Docker command failed (exit code {exc.returncode}).")
        return False


def _ensure_writable_directory(path: Path, description: str) -> bool:
    """Ensure a directory exists and is writable by the current user."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        tui.error_box(
            f"Cannot access {description} at {path} ({exc}).\n"
            "Choose a directory you own or run 'sudo chown -R $(whoami) "
            f"{path}' and retry."
        )
        return False
    if not os.access(path, os.W_OK):
        tui.error_box(
            f"{description} at {path} is not writable by {getpass.getuser()}.\n"
            "Adjust permissions (chmod/chown) or pick another location."
        )
        return False
    return True


def prompt_services(previous: Sequence[str] | None = None) -> List[str]:
    """Interactive service selection with category grouping."""
    catalog_by_category = services_by_category()
    option_map: Dict[str, str] = {}
    
    # Build options with category labels
    for category_key, services in catalog_by_category.items():
        category_label = SERVICE_CATEGORIES.get(category_key, category_key)
        for svc in services:
            label = f"{svc.name:20} - {svc.description}"
            option_map[label] = svc.key

    if not option_map:
        raise RuntimeError("No services defined in catalog")

    preselected_keys = set(previous or [])
    _render_service_menu_intro(catalog_by_category)

    while True:
        preselected_labels = [
            label for label, key in option_map.items() if key in preselected_keys
        ]
        try:
            selection_labels = tui.choose_many(
                "📦 Select Applications",
                option_map.keys(),
                info="Use ↑↓ arrows, Space to select, Enter when done",
                height=20,
                preselected=preselected_labels,
            )
        except tui.UserNavigationBack:
            raise
        except tui.GumInteractionError as exc:
            tui.error_box(str(exc))
            raise
        
        if not selection_labels:
            tui.error_box("Please select at least one application")
            continue
        
        # Resolve dependencies
        direct_keys = [option_map[label] for label in selection_labels]
        expanded = expand_dependencies(direct_keys)
        extras = [svc for svc in expanded if svc not in direct_keys]
        
        if extras:
            lookup = service_lookup()
            names = ", ".join(lookup[svc].name for svc in extras)
            tui.info_box(f"Added dependencies: {names}")
        
        return _dedupe_preserve_order(expanded)


def configure_vpn(selected: List[str], previous: VPNSettings | None = None) -> VPNSettings:
    """Configure VPN settings with enhanced wizard."""
    vpn_enabled = "gluetun" in selected or (previous.enabled if previous else False)
    
    if not vpn_enabled:
        tui.info_box(
            "VPN Configuration (Optional)\n\n"
            "Gluetun can route your download clients and indexers through a VPN\n"
            "for enhanced privacy and security."
        )
        vpn_enabled = tui.confirm(
            "Do you want to enable VPN support (Gluetun)?",
            default_yes=False,
            affirmative="✓ Enable VPN",
            negative="Skip VPN",
        )
        if vpn_enabled:
            selected.append("gluetun")

    base_settings = previous if previous else VPNSettings()
    settings = VPNSettings(**vars(base_settings))
    settings.enabled = vpn_enabled
    if not vpn_enabled:
        return settings

    # VPN Configuration Wizard
    tui.style_block(
        "🔒 VPN Configuration Wizard",
        "Let's configure your VPN connection.\n"
        "You'll need credentials from your VPN provider.",
        color="86"
    )

    # Provider selection
    provider_options = [f"{label:20} - {desc}" for _, label, desc in VPN_PROVIDERS]
    provider_map = {f"{label:20} - {desc}": slug for slug, label, desc in VPN_PROVIDERS}
    
    provider_choice = tui.choose_one(
        "Select your VPN provider",
        provider_options,
        info="Choose your VPN service or select Custom for manual configuration"
    )
    settings.provider = provider_map[provider_choice]

    # VPN type
    vpn_type_choice = tui.choose_one(
        "Select VPN protocol",
        ["wireguard (recommended)", "openvpn"],
        info="WireGuard is faster and more modern"
    )
    settings.vpn_type = vpn_type_choice.split()[0]

    # WireGuard-specific settings
    if settings.vpn_type == "wireguard":
        tui.info_box(
            "WireGuard Configuration\n\n"
            "You'll need your WireGuard private key and addresses from your VPN provider.\n"
            f"For {settings.provider}, check their dashboard or configuration files."
        )
        
        settings.wireguard_private_key = tui.input_text(
            "🔑 WireGuard Private Key",
            placeholder="Your private key from VPN provider",
            default=settings.wireguard_private_key,
            password=True
        )
        
        settings.wireguard_addresses = tui.input_text(
            "📍 WireGuard IP Addresses",
            placeholder="e.g., 10.64.0.2/32,fc00::1/128",
            default=settings.wireguard_addresses,
        ) or settings.wireguard_addresses
        
        settings.wireguard_mtu = tui.input_text(
            "⚙️  MTU Setting",
            placeholder="1280 (recommended)",
            default=settings.wireguard_mtu,
        ) or settings.wireguard_mtu

    # Server location preference
    settings.server_cities = tui.input_text(
        "🌍 Preferred Server Cities (optional)",
        placeholder="e.g., Amsterdam,Stockholm,London",
        default=settings.server_cities,
    )

    # Optional: Public IP API
    if tui.confirm(
        "Configure public IP verification? (optional)",
        default_yes=False,
        affirmative="Configure",
        negative="Skip"
    ):
        settings.public_ip_api = tui.input_text(
            "Public IP API Endpoint",
            placeholder="https://api.ipify.org",
            default=settings.public_ip_api,
        )
        settings.public_ip_token = tui.input_text(
            "API Token (if required)",
            placeholder="Leave blank if not needed",
            default=settings.public_ip_token,
            password=True
        )

    tui.success_box(f"VPN configured with {settings.provider} via {settings.vpn_type}")
    return settings


def prompt_timezone(existing: str | None = None) -> str:
    """Prompt for system timezone."""
    default = existing or detect_timezone() or DEFAULT_TIMEZONE
    tui.info_box(
        "Timezone Configuration\n\n"
        "This sets the timezone for all containers (e.g., Europe/Amsterdam, America/New_York)"
    )
    tz = tui.input_text(
        "🕐 Enter your timezone (IANA format)",
        placeholder=DEFAULT_TIMEZONE,
        default=default,
    )
    return tz or default


def prompt_root_dir(existing: str | None = None) -> str:
    """Prompt for root installation directory."""
    env_default = os.getenv("ROOT_DIR", "")
    default = existing or env_default or str((Path.home() / "boxlab").resolve())
    
    tui.info_box(
        "Installation Directory\n\n"
        "All configurations and data will be stored here.\n"
        "This should be on a filesystem that supports hardlinks for optimal performance."
    )
    
    while True:
        answer = tui.input_text(
            "📁 Installation directory",
            placeholder=default,
            default=default,
        )
        answer = answer.strip()
        if not answer:
            answer = default
        if not answer.startswith("/"):
            tui.error_box("Please provide an absolute path (starting with /)")
            continue
        target = Path(answer).expanduser()
        if not _ensure_writable_directory(target, "Installation directory"):
            continue
        return str(target.resolve())


def prompt_compose_path(root_dir: str, existing: str | None = None) -> str:
    """Allow the user to decide where docker-compose.yml should be stored."""
    install_default = (Path(root_dir).expanduser().resolve()) / "docker-compose.yml"
    current = Path(existing).expanduser().resolve() if existing else install_default
    while True:
        options = [
            ("default", f"Installation directory (uses {install_default})"),
        ]
        if existing and current != install_default:
            options.append(("keep", f"Keep previously configured path ({current})"))
        options.append(("custom", "Choose a different directory"))

        labels = [label for _, label in options]
        choice = tui.choose_one(
            "Where should we store docker-compose.yml?",
            labels,
            info="Default is inside your installation directory.",
        )
        action = next((key for key, label in options if label == choice), "default")
        if action in {"default", "keep"}:
            chosen = install_default if action == "default" else current
            if _ensure_writable_directory(chosen.parent, "Compose directory"):
                return str(chosen)
            continue

        directory = tui.input_text(
            "Enter directory for docker-compose.yml",
            placeholder=str(current.parent),
            default=str(current.parent),
        ).strip()
        if not directory:
            directory = str(current.parent)
        directory = os.path.expanduser(directory)
        if not directory.startswith("/"):
            tui.error_box("Please provide an absolute path (starting with /)")
            continue
        target_dir = Path(directory).expanduser().resolve()
        if not _ensure_writable_directory(target_dir, "Compose directory"):
            continue
        return str(target_dir / "docker-compose.yml")


def prompt_plex_claim(services: Sequence[str], existing: str = "") -> str:
    """Prompt for Plex claim token if Plex is selected."""
    if "plex" not in services:
        return ""
    
    tui.info_box(
        "Plex Configuration\n\n"
        "Get your claim token from: https://www.plex.tv/claim\n"
        "This links your Plex server to your account (valid for 4 minutes)."
    )
    
    return tui.input_text(
        "🎬 Plex Claim Token (optional)",
        placeholder="claim-XXXXXXXXXXXX",
        default=existing,
    ).strip()


def prompt_wizarr_settings(
    services: Sequence[str],
    existing: WizarrSettings | None = None
) -> WizarrSettings | None:
    """Prompt for Wizarr settings if selected."""
    if "wizarr" not in services:
        return None
    
    tui.info_box(
        "Wizarr Configuration\n\n"
        "Wizarr creates one-click invitation links for your media server.\n"
        "Configure the external URL where Wizarr will be accessible."
    )
    
    base = WizarrSettings(**vars(existing)) if existing else WizarrSettings()
    
    app_url = tui.input_text(
        "🌐 External Wizarr URL",
        placeholder="https://invite.yourdomain.com",
        default=base.app_url,
    ).strip()
    
    disable_auth = tui.confirm(
        "Disable Wizarr built-in authentication?",
        affirmative="Disable (use reverse proxy auth)",
        negative="Keep enabled",
        default_yes=base.disable_builtin_auth,
    )
    
    return WizarrSettings(app_url=app_url, disable_builtin_auth=disable_auth)


def prompt_jellystat_settings(
    services: Sequence[str],
    existing: JellystatSettings | None = None
) -> JellystatSettings | None:
    """Prompt for Jellystat database and JWT settings."""
    if "jellystat" not in services:
        return None
    
    tui.info_box(
        "Jellystat Configuration\n\n"
        "Jellystat requires a PostgreSQL database and JWT secret.\n"
        "We can auto-generate secure credentials for you."
    )
    
    base = JellystatSettings(**vars(existing)) if existing else JellystatSettings()
    
    db_user = tui.input_text(
        "📊 Database User",
        placeholder="jfstat",
        default=base.db_user
    ) or base.db_user
    
    db_name = tui.input_text(
        "📊 Database Name",
        placeholder="jfstat",
        default=base.db_name
    ) or base.db_name
    
    db_password = tui.input_text(
        "🔐 Database Password (blank to auto-generate)",
        placeholder="Leave blank for auto-generation",
        default=base.db_password,
        password=True
    ).strip()
    
    if not db_password:
        db_password = secrets.token_hex(16)
        tui.success_box(f"Generated secure database password: {db_password[:8]}...")
    
    jwt_secret = tui.input_text(
        "🔑 JWT Secret (blank to auto-generate)",
        placeholder="Leave blank for auto-generation",
        default=base.jwt_secret,
        password=True
    ).strip()
    
    if not jwt_secret:
        jwt_secret = secrets.token_hex(32)
        tui.success_box("Generated secure JWT secret")
    
    return JellystatSettings(
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        jwt_secret=jwt_secret,
    )


def show_summary(context: SetupContext) -> None:
    """Display configuration summary before generation."""
    lookup = service_lookup()
    service_names = [lookup[key].name if key in lookup else key for key in context.services]
    
    summary_lines = [
        f"Timezone: {context.timezone}",
        f"Install Path: {context.root_dir}",
        f"Compose File: {context.compose_path}",
        f"VPN: {'Enabled (' + context.vpn.provider + ')' if context.vpn.enabled else 'Disabled'}",
    ]
    
    if context.plex_claim:
        summary_lines.append("Plex: Claim token provided")
    if context.wizarr:
        summary_lines.append("Wizarr: Invitations configured")
    if context.jellystat:
        summary_lines.append("Jellystat: Analytics + PostgreSQL enabled")
    
    services_block = "\n".join(f"  • {name}" for name in service_names) or "  • None selected"
    summary_lines.append(f"Services ({len(service_names)}):\n{services_block}")
    
    tui.style_block("📋 Configuration Summary", "\n".join(summary_lines), color="212")


def detect_timezone() -> str | None:
    """Attempt to detect the system timezone."""
    tz_path = "/etc/localtime"
    if os.path.exists(tz_path) and os.path.islink(tz_path):
        tz = os.readlink(tz_path)
        return tz.split("zoneinfo/")[-1]
    return None


def generate_compose(context: SetupContext) -> Path:
    """Generate docker-compose.yml from context."""
    # Prepare settings dictionaries
    gluetun_settings = None
    if context.vpn.enabled:
        gluetun_settings = {
            "VPN_SERVICE_PROVIDER": context.vpn.provider,
            "VPN_TYPE": context.vpn.vpn_type,
            "WIREGUARD_PRIVATE_KEY": context.vpn.wireguard_private_key,
            "WIREGUARD_ADDRESSES": context.vpn.wireguard_addresses,
            "SERVER_CITIES": context.vpn.server_cities,
            "WIREGUARD_MTU": context.vpn.wireguard_mtu,
            "PUBLICIP_API": context.vpn.public_ip_api,
            "PUBLICIP_API_TOKEN": context.vpn.public_ip_token,
        }
    
    wizarr_settings = None
    if context.wizarr:
        wizarr_settings = {
            "APP_URL": context.wizarr.app_url,
            "DISABLE_BUILTIN_AUTH": "true" if context.wizarr.disable_builtin_auth else "false",
        }
    
    jellystat_settings = None
    if context.jellystat:
        jellystat_settings = {
            "db_name": context.jellystat.db_name,
            "db_user": context.jellystat.db_user,
            "db_password": context.jellystat.db_password,
            "jwt_secret": context.jellystat.jwt_secret,
        }

    # Build compose file
    builder = ComposeBuilder(
        context.root_dir,
        context.timezone,
        plex_claim=context.plex_claim,
        gluetun_settings=gluetun_settings,
        wizarr_settings=wizarr_settings,
        jellystat_settings=jellystat_settings,
    )
    
    compose_path = Path(context.compose_path)
    compose_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# ------------------------------------------------------------\n"
        "# BoxLab Media Server Stack Installer\n"
        f"# Generated on {datetime.utcnow().isoformat()}Z\n"
        "# Author: BoxLab / Selfhost Apps\n"
        "# Repo: https://github.com/selfhost-apps/boxlab-media-server-stack\n"
        "# Tip: Re-run ./boxlab to add or remove services. Manual edits may be overwritten.\n"
        "# ------------------------------------------------------------\n\n"
    )
    with compose_path.open("w") as handle:
        handle.write(header)
        handle.write("---\nservices:\n")
        for service_key in context.services:
            generator = getattr(builder, service_key, None)
            if not callable(generator):
                continue
            handle.write(generator())
    
    return compose_path


def generate_permissions(context: SetupContext) -> None:
    """Set up filesystem permissions and users."""
    setup = PermissionSetup(root_dir=context.root_dir)
    total = len(context.services)
    
    for idx, service_key in enumerate(context.services, 1):
        tui.progress_bar(f"Setting up {service_key}", total, idx)
        handler = getattr(setup, service_key, None)
        if callable(handler):
            handler()
    
    print()  # New line after progress


def _reconcile_services_with_existing(
    selected: List[str],
    previous: SetupContext | None,
    compose_path: Path
) -> List[str] | None:
    """Handle scenarios where a docker-compose file already exists."""
    cleaned_selection = _dedupe_preserve_order(selected)
    if not compose_path.exists():
        return cleaned_selection

    options = [
        ("replace", "Replace existing stack (overwrite docker-compose.yml)"),
        ("extend", "Add these services to the existing stack"),
        ("cancel", "Cancel (keep current stack)"),
    ]
    labels = [label for _, label in options]
    choice = tui.choose_one(
        "A docker-compose.yml already exists. What would you like to do?",
        labels,
        info="Replacing overwrites the file. Adding keeps current services and appends new ones.",
    )
    action = next((key for key, label in options if label == choice), "replace")

    if action == "cancel":
        tui.info_box("Existing stack left untouched.")
        return None
    if action == "extend":
        existing = previous.services if (previous and previous.services) else _parse_compose_services(compose_path)
        merged = _dedupe_preserve_order([*existing, *cleaned_selection])
        added = [svc for svc in merged if svc not in existing]
        if added:
            lookup = service_lookup()
            human = ", ".join(lookup[svc].name for svc in added if svc in lookup)
            tui.info_box(f"Keeping current stack and adding: {human}")
        return merged
    return cleaned_selection


def _parse_compose_services(path: Path) -> List[str]:
    """Extract service keys from an existing docker-compose.yml."""
    pattern = re.compile(r"^\s{2}([a-z0-9_-]+):\s*$")
    services: List[str] = []
    try:
        with path.open("r") as handle:
            for line in handle:
                match = pattern.match(line)
                if match:
                    services.append(match.group(1))
    except OSError:
        return []
    return services


def _dedupe_preserve_order(items: Sequence[str]) -> List[str]:
    """Remove duplicates while keeping the first occurrence order."""
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered
