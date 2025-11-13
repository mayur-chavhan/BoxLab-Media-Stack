"""
Beautiful Terminal User Interface using Charm's Gum.
Provides elegant, interactive components for the BoxLab installer.
"""
from __future__ import annotations

import errno
import os
import pty
import re
import select
import shutil
import subprocess
import sys
from typing import Iterable, List, Optional

try:
    from .constants import GUM_MIN_VERSION
    from .gum import get_gum_version, version_to_str
except ImportError:
    from constants import GUM_MIN_VERSION  # type: ignore
    from gum import get_gum_version, version_to_str  # type: ignore


class GumNotInstalledError(RuntimeError):
    """Raised when Gum binary is not found or incompatible."""
    pass


class GumInteractionError(RuntimeError):
    """Raised when a Gum command fails to execute properly."""
    pass


class UserNavigationBack(RuntimeError):
    """Raised when the user requests to navigate back/up a menu."""
    pass


_ANSI_RE = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")

# Emojis with variation selectors can render double-width on some terminals which
# makes Gum miscalculate borders. Stick to the text variant for consistent boxes.
INFO_ICON = "ℹ"
_INPUT_PROMPT_PREFIXES = ("› ", "> ", "❯ ", "▸ ", "» ", "• ")
_MENU_CURSOR_COLOR = "212"
_MENU_SELECTED_COLOR = "82"
_MENU_ITEM_COLOR = "252"
_PANEL_WIDTH = 76


def _debug(message: str) -> None:
    """Emit debug logging when BOXLAB_DEBUG is enabled."""
    if os.environ.get("BOXLAB_DEBUG"):
        print(f"[boxlab:tui] {message}", file=sys.stderr)


def _color(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def separator(label: str = "") -> None:
    """Print a horizontal separator with optional centered label."""
    line = "─" * _PANEL_WIDTH
    if label:
        label_display = f" {label} "
        mid = len(line) // 2
        start = max(0, mid - len(label_display) // 2)
        line = line[:start] + label_display + line[start + len(label_display):]
    if _use_plain_mode():
        print(_color(line, "90"))
    else:
        subprocess.run(
            [
                "gum",
                "style",
                "--foreground", "90",
                "--padding", "0 0",
            ],
            input=line,
            text=True,
            check=False,
        )


def _render_panel(title: str, body: str, color: str = "86") -> None:
    """Render a bordered panel for plain-mode output."""
    lines = [title] + body.splitlines()
    width = min(_PANEL_WIDTH, max(len(line) for line in lines) + 4)
    top = "┌" + "─" * (width - 2) + "┐"
    bottom = "└" + "─" * (width - 2) + "┘"
    print(_color(top, color))
    for line in lines:
        padded = line.ljust(width - 4)
        print(_color(f"│ {padded} │", color))
    print(_color(bottom, color))


def _bool_env(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in ("1", "true", "yes", "on")


def _use_plain_mode() -> bool:
    if _bool_env("BOXLAB_FORCE_TUI"):
        return False
    if _bool_env("BOXLAB_FORCE_PLAIN") or _bool_env("BOXLAB_PLAIN_TUI"):
        return True
    return not (sys.stdin.isatty() and sys.stdout.isatty())


def _run_gum(
    args: List[str],
    text_input: Optional[str] = None,
    env: Optional[dict] = None,
    *,
    interactive: bool = False,
) -> str:
    """Execute a gum command with optional input and environment."""
    command = ["gum"] + args
    _debug(f"Running gum command: {' '.join(command)} (interactive={interactive})")
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    if not interactive:
        result = subprocess.run(
            command,
            input=text_input,
            capture_output=True,
            text=True,
            env=proc_env,
            check=True,
        )
        return result.stdout.strip()
    return _run_gum_interactive(command, text_input=text_input, env=proc_env)


def _run_gum_interactive(command: List[str], text_input: Optional[str], env: dict) -> str:
    """Run a gum command attached to a pseudo-terminal so the UI renders."""
    master_fd, slave_fd = pty.openpty()
    stdin_pipe = subprocess.PIPE if text_input is not None else None
    proc = subprocess.Popen(
        command,
        stdin=stdin_pipe,
        stdout=slave_fd,
        stderr=slave_fd,
        env=env,
        text=True,
    )
    os.close(slave_fd)

    if text_input is not None and proc.stdin:
        proc.stdin.write(text_input)
        proc.stdin.close()

    output_chunks: List[str] = []
    try:
        while True:
            rlist, _, _ = select.select([master_fd], [], [], 0.1)
            if master_fd in rlist:
                try:
                    data = os.read(master_fd, 1024)
                except OSError as exc:
                    if exc.errno == errno.EIO:
                        _debug("PTY reported EIO (likely closed). Stopping read loop.")
                        break
                    raise
                if not data:
                    break
                decoded = data.decode(errors="ignore")
                output_chunks.append(decoded)
                if sys.stdout is not None and sys.stdout.isatty():
                    os.write(sys.stdout.fileno(), data)
            if proc.poll() is not None:
                # Drain any remaining data
                if not rlist:
                    break
    finally:
        os.close(master_fd)

    rc = proc.wait()
    if rc != 0:
        if rc in (130, 255):
            raise UserNavigationBack("User cancelled selection")
        raise subprocess.CalledProcessError(rc, command)
    return _strip_ansi("".join(output_chunks).strip())


def ensure_gum_installed() -> None:
    """Check if Gum is available, compatible, and raise error if not."""
    gum_path = shutil.which("gum")
    if gum_path is None:
        raise GumNotInstalledError(
            "\n❌ Charm Gum is required for this installer.\n\n"
            "Install it via:\n"
            "  • Re-run ./boxlab to trigger the auto-installer\n"
            "  • macOS: brew install gum\n"
            "  • Manual: https://github.com/charmbracelet/gum\n"
        )
    _debug(f"Using Gum binary at {gum_path}")
    version = get_gum_version()
    _debug(f"Detected Gum version: {version}")
    if version and version < GUM_MIN_VERSION:
        raise GumNotInstalledError(
            f"\n❌ Detected Gum {version_to_str(version)} but "
            f"BoxLab requires at least {version_to_str(GUM_MIN_VERSION)}\n"
            "Please upgrade Gum and retry.\n"
        )


def show_banner() -> None:
    """Display the welcome banner."""
    banner_text = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║              🎬 BoxLab Media Server Stack 🎬             ║
║                                                          ║
║     Your Ultimate Self-Hosted Media Automation Stack     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Welcome! This guided installer will help you set up a complete
media automation stack with just a few questions.

Features:
  ✓ Interactive service selection
  ✓ Optional VPN configuration
  ✓ Automatic permission setup
  ✓ Docker Compose generation
"""
    subprocess.run(
        [
            "gum",
            "style",
            "--border", "rounded",
            "--padding", "1 2",
            "--foreground", "212",
            "--border-foreground", "99",
        ],
        input=banner_text.strip(),
        text=True,
    )
    print()


def style_block(title: str, body: str, color: str = "212") -> None:
    """Display a styled block with title and body."""
    text = f"{title}\n\n{body}"
    subprocess.run(
        [
            "gum",
            "style",
            "--border", "double",
            "--align", "center",
            "--width", "72",
            "--padding", "1 2",
            "--foreground", color,
        ],
        input=text,
        text=True,
        check=True,
    )
    print()


def info_box(message: str) -> None:
    """Display an informational message."""
    subprocess.run(
        [
            "gum",
            "style",
            "--border", "rounded",
            "--padding", "0 1",
            "--foreground", "86",
            "--border-foreground", "86",
        ],
        input=f"{INFO_ICON}  {message}",
        text=True,
    )
    print()


def success_box(message: str) -> None:
    """Display a success message."""
    subprocess.run(
        [
            "gum",
            "style",
            "--border", "rounded",
            "--padding", "0 1",
            "--foreground", "10",
            "--border-foreground", "10",
        ],
        input=f"✓ {message}",
        text=True,
    )
    print()


def error_box(message: str) -> None:
    """Display an error message."""
    subprocess.run(
        [
            "gum",
            "style",
            "--border", "rounded",
            "--padding", "0 1",
            "--foreground", "9",
            "--border-foreground", "9",
        ],
        input=f"✗ {message}",
        text=True,
    )
    print()


def spinner(title: str, command: List[str]) -> subprocess.CompletedProcess:
    """Run a command with a spinner animation."""
    return subprocess.run(
        ["gum", "spin", "--spinner", "dot", "--title", title, "--"] + command,
        capture_output=False,
        text=True,
    )


def confirm(prompt: str, affirmative: str = "Yes", negative: str = "No", default_yes: bool = True) -> bool:
    """Ask a yes/no question and return the answer."""
    if _use_plain_mode():
        return _plain_confirm(prompt, default_yes)
    args = ["confirm", prompt]
    if affirmative:
        args.extend(["--affirmative", affirmative])
    if negative:
        args.extend(["--negative", negative])
    if not default_yes:
        args.append("--default=no")
    try:
        _run_gum(args, interactive=True)
        return True
    except UserNavigationBack:
        raise
    except subprocess.CalledProcessError:
        return False


def input_text(prompt: str, placeholder: str = "", default: str = "", password: bool = False) -> str:
    """Get text input from the user."""
    if _use_plain_mode():
        return _plain_input(prompt, default=default, password=password)
    env = {
        "GUM_INPUT_HEADER": prompt,
        "GUM_INPUT_PLACEHOLDER": placeholder,
        "GUM_INPUT_PROMPT": "› ",
        "GUM_INPUT_CURSOR.FOREGROUND": "212",
    }
    args = ["input", "--width", "60"]
    if default:
        env["GUM_INPUT_VALUE"] = default
    if password:
        args.append("--password")
    raw = _run_gum(args, env=env, interactive=True)
    return _extract_input_value(raw)


def choose_many(
    prompt: str,
    options: Iterable[str],
    info: str = "",
    height: int = 15,
    preselected: Optional[Iterable[str]] = None,
) -> List[str]:
    """Allow the user to select multiple options from a list."""
    opts = list(options)
    if not opts:
        _debug("choose_many invoked with empty options list")
        return []
    if _use_plain_mode():
        return _plain_choose_many(prompt, opts, info, preselected=preselected)

    preselected_set = set(preselected or [])
    selected_labels = [opt for opt in opts if opt in preselected_set]
    env = {
        "GUM_CHOOSE_HEADER": prompt,
        "GUM_CHOOSE_CURSOR": "› ",
        "GUM_CHOOSE_SELECTED_PREFIX": "✓ ",
        "GUM_CHOOSE_UNSELECTED_PREFIX": "  ",
        "GUM_CHOOSE_CURSOR.FOREGROUND": _MENU_CURSOR_COLOR,
        "GUM_CHOOSE_SELECTED.FOREGROUND": _MENU_SELECTED_COLOR,
        "GUM_CHOOSE_ITEM.FOREGROUND": _MENU_ITEM_COLOR,
    }
    if info:
        env["GUM_CHOOSE_HEADER.FOREGROUND"] = "86"
        full_prompt = f"{prompt}\n\n{info}"
        env["GUM_CHOOSE_HEADER"] = full_prompt
    cmd = ["choose", "--no-limit", "--height", str(height)]
    if selected_labels:
        cmd.append("--selected=" + ",".join(selected_labels))
    _debug(f"choose_many prompt='{prompt}' options={len(opts)} height={height}")
    try:
        output = _run_gum(cmd + opts, env=env, interactive=True)
        selections = _filter_selections(output, opts)
        if selections:
            return selections
        _debug("Gum choose_many produced no matching selections; falling back to plain mode.")
    except UserNavigationBack:
        raise
    except subprocess.CalledProcessError as err:
        _debug(f"Gum choose failed: {err}. Falling back to plain selection.")
        return _plain_choose_many(prompt, opts, info, preselected=preselected)
    return _plain_choose_many(prompt, opts, info, preselected=preselected)


def choose_one(prompt: str, options: Iterable[str], info: str = "", height: int = 10) -> str:
    """Allow the user to select one option from a list."""
    opts = list(options)
    if not opts:
        raise ValueError("No options supplied")
    if _use_plain_mode():
        return _plain_choose_one(prompt, opts, info)

    env = {
        "GUM_CHOOSE_HEADER": prompt,
        "GUM_CHOOSE_CURSOR": "› ",
        "GUM_CHOOSE_CURSOR.FOREGROUND": _MENU_CURSOR_COLOR,
        "GUM_CHOOSE_SELECTED.FOREGROUND": _MENU_SELECTED_COLOR,
        "GUM_CHOOSE_ITEM.FOREGROUND": _MENU_ITEM_COLOR,
    }
    if info:
        full_prompt = f"{prompt}\n\n{info}"
        env["GUM_CHOOSE_HEADER"] = full_prompt
        env["GUM_CHOOSE_HEADER.FOREGROUND"] = "86"
    cmd = ["choose", "--height", str(height)]
    try:
        output = _run_gum(cmd + opts, env=env, interactive=True)
        selections = _filter_selections(output, opts)
        if selections:
            return selections[0]
        _debug("Gum choose_one produced no matching selection; falling back to plain mode.")
    except UserNavigationBack:
        raise
    except subprocess.CalledProcessError as err:
        _debug(f"Gum choose_one failed: {err}. Falling back to plain selection.")
        return _plain_choose_one(prompt, opts, info)
    return _plain_choose_one(prompt, opts, info)


def progress_bar(title: str, total: int, current: int) -> None:
    """Show a simple progress indicator."""
    percentage = int((current / total) * 100)
    bar_width = 40
    filled = int((bar_width * current) // total)
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"\r{title}: {bar} {percentage}%", end="", flush=True)
    if current == total:
        print()  # New line when complete


def _plain_header(prompt: str, info: str) -> None:
    print()
    body = info if info else ""
    _render_panel(prompt, body)
    print()


def _plain_choose_many(
    prompt: str,
    options: List[str],
    info: str,
    *,
    preselected: Optional[Iterable[str]] = None,
) -> List[str]:
    _plain_header(prompt, info)
    for idx, option in enumerate(options, start=1):
        print(f"{idx:>2}. {option}")
    print()
    default_indices: List[int] = []
    if preselected:
        preselected_set = set(preselected)
        default_indices = [idx + 1 for idx, option in enumerate(options) if option in preselected_set]
        if default_indices:
            default_str = ", ".join(str(i) for i in default_indices)
            print(f"Press Enter to keep previous selections ({default_str}).")
    print(_color("Type 'b' to go back or 'q' to cancel. Press Esc to cancel.", "90"))
    while True:
        try:
            selection = input("Enter numbers (comma separated): ").strip()
        except KeyboardInterrupt:
            raise UserNavigationBack()
        if "\x1b" in selection or selection.lower() in {"b", "back", "q", "quit"}:
            raise UserNavigationBack()
        if not selection:
            if default_indices:
                return [options[i - 1] for i in default_indices]
            return []
        try:
            indices = {
                int(piece)
                for piece in selection.replace(" ", "").split(",")
                if piece
            }
        except ValueError:
            print("Invalid selection. Use numbers like 1,3,5.")
            continue
        picked = [
            options[i - 1]
            for i in sorted(indices)
            if 1 <= i <= len(options)
        ]
        if not picked:
            print("Select at least one valid entry.")
            continue
        return picked


def _plain_choose_one(prompt: str, options: List[str], info: str) -> str:
    _plain_header(prompt, info)
    for idx, option in enumerate(options, start=1):
        print(f"{idx:>2}. {option}")
    print()
    print(_color("Type 'b' to go back or 'q' to cancel. Press Esc to cancel.", "90"))
    while True:
        try:
            selection = input("Enter choice number: ").strip()
        except KeyboardInterrupt:
            raise UserNavigationBack()
        if "\x1b" in selection or selection.lower() in {"b", "back", "q", "quit"}:
            raise UserNavigationBack()
        if not selection:
            print("Please enter a number.")
            continue
        try:
            index = int(selection)
        except ValueError:
            print("Invalid number. Try again.")
            continue
        if 1 <= index <= len(options):
            return options[index - 1]
        print("Selection out of range. Try again.")


def _plain_confirm(prompt: str, default_yes: bool) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    while True:
        answer = input(f"{prompt} {suffix} ").strip().lower()
        if not answer:
            return default_yes
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def _plain_input(prompt: str, default: str = "", password: bool = False) -> str:
    try:
        if password:
            value = input(f"{prompt} (input hidden not supported, type manually): ")
        else:
            value = input(f"{prompt}: ")
    except KeyboardInterrupt:
        raise UserNavigationBack()
    if "\x1b" in value or value.strip().lower() in {"b", "back", "q", "quit"}:
        raise UserNavigationBack()
    if not value and default:
        return default
    return value


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _extract_input_value(raw: str) -> str:
    """Normalize Gum input output to the typed value."""
    if not raw:
        return ""
    cleaned = _strip_ansi(raw).replace("\r", "\n")
    lines = [line for line in cleaned.split("\n") if line.strip()]
    if not lines:
        return ""
    value = lines[-1].strip()
    for prefix in _INPUT_PROMPT_PREFIXES:
        if value.startswith(prefix):
            value = value[len(prefix):].lstrip()
            break
    return value


def _filter_selections(raw_output: str, options: List[str]) -> List[str]:
    clean = _strip_ansi(raw_output)
    values = [line.replace("\r", "") for line in clean.splitlines()]
    return [line for line in values if line in options]
