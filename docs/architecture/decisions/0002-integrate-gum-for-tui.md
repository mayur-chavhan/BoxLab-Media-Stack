# ADR-0002: Integrate Charm's Gum for TUI

**Status**: Accepted

**Date**: 2024-01-15

## Context

BoxLab CLI needed an interactive terminal user interface for:

- Service selection (multi-select menus)
- Configuration input (text input, confirmations)
- Styled output (info boxes, success messages)
- User-friendly experience

Original implementation used basic Python `input()` which provided poor UX:

- No visual selection feedback
- No keyboard navigation
- No styling or colors
- Plain text only

Requirements:

1. Interactive menus with keyboard navigation
2. Multi-select capability with `--no-limit` flag
3. Styled output with colors and borders
4. Cross-platform support
5. Minimal dependencies
6. Graceful fallback when TUI unavailable

## Decision

Integrate [Charm's Gum](https://github.com/charmbracelet/gum) as the TUI framework:

1. **Binary Management**: Download appropriate Gum binary at runtime
2. **Version Requirement**: Minimum version 0.17.0 (for `--no-limit` support)
3. **Cross-Platform**: Support Linux and macOS, both x86_64 and ARM64
4. **Cache Strategy**: Cache binaries at `~/.cache/boxlab/gum/{version}/`
5. **Fallback Mechanism**: Use stdin input when Gum interaction fails
6. **Wrapper Module**: Create `lib/tui.py` to abstract Gum commands

### API Design

```python
# lib/tui.py

def choose_many(prompt: str, choices: list[str], selected: list[str] = None) -> list[str]:
    """Multi-select menu with fallback"""
    try:
        # Try Gum first
        return _gum_choose_many(prompt, choices, selected)
    except GumInteractionError:
        # Fall back to stdin
        return _stdin_choose_many(prompt, choices)

def choose_one(prompt: str, choices: list[str], default: str = None) -> str:
    """Single-select menu with fallback"""
    # Similar pattern

def input_text(prompt: str, placeholder: str = "", default: str = "") -> str:
    """Text input"""

def confirm(prompt: str, default: bool = True) -> bool:
    """Yes/no confirmation"""

def display_info(title: str, message: str):
    """Styled info box"""
```

## Consequences

### Positive

- **Professional UX**: Beautiful terminal UI with colors and styling
- **Keyboard Navigation**: Arrow keys, vim bindings, search
- **Multi-Select**: Easy service selection with visual feedback
- **Composable**: Gum commands can be piped and combined
- **Active Development**: Charm maintains Gum regularly
- **Community**: Large user base, good documentation
- **Minimal Footprint**: Single binary (~10MB), no language runtime
- **Graceful Degradation**: Falls back to stdin when needed

### Negative

- **Binary Dependency**: Must download external binary
- **Network Required**: First run needs internet for download
- **Cache Management**: Must manage binary versions
- **Platform Limitations**: Only supports Linux/macOS (no Windows native)
- **Version Compatibility**: Breaking changes between Gum versions possible
- **Debug Complexity**: Harder to debug subprocess calls vs native Python

## Alternatives Considered

### Alternative 1: Python Prompt Toolkit

**Description**: Use [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) Python library

**Pros**:

- Pure Python, no binary download
- Excellent features (auto-completion, validation, etc.)
- Well-documented and maintained
- Type hints and IDE support

**Cons**:

- External dependency (requires pip install)
- Larger footprint than single binary
- More complex API
- Performance overhead for large lists

**Why not chosen**: BoxLab aims for zero Python dependencies. While prompt_toolkit is excellent, requiring users to `pip install` dependencies complicates installation. Gum binary can be auto-downloaded and cached.

### Alternative 2: Textual

**Description**: Use [Textual](https://textual.textualize.io/) TUI framework

**Pros**:

- Modern, feature-rich TUI framework
- Widget-based architecture
- Excellent documentation
- Same company as Gum (Charm)

**Cons**:

- Python dependency (pip install required)
- Overkill for simple menus
- Higher complexity
- Steeper learning curve

**Why not chosen**: Textual is designed for complex TUIs (dashboards, editors). BoxLab only needs simple menus and inputs. Gum's simplicity better matches our needs.

### Alternative 3: Rich + Inquirer

**Description**: Combine [Rich](https://rich.readthedocs.io/) for styling and [Inquirer](https://github.com/magmax/python-inquirer) for menus

**Pros**:

- Pure Python
- Rich has excellent styling
- Inquirer provides menu functionality
- Good community support

**Cons**:

- Two dependencies (Rich + Inquirer)
- pip install required
- Inquirer less maintained than Gum
- Rich is large (many features we don't need)

**Why not chosen**: Same reason as Alternative 1 - we want to avoid Python dependencies. Also, using two libraries adds complexity.

### Alternative 4: FZF

**Description**: Use [fzf](https://github.com/junegunn/fzf) fuzzy finder

**Pros**:

- Popular, widely installed
- Excellent fuzzy search
- Fast performance
- Single binary

**Cons**:

- Limited to selection (no styled output)
- Different UX paradigm (fuzzy search vs menu)
- Less composable for our use case
- Would need additional tools for styling

**Why not chosen**: FZF is optimized for fuzzy searching large lists. BoxLab's service catalog is small (~30 services), so fuzzy search is overkill. Gum provides better UX for our specific needs (styled menus, inputs, confirmations).

### Alternative 5: Plain Python input()

**Description**: Continue with basic `input()` and print statements

**Pros**:

- No dependencies
- Maximum portability
- Simple to understand
- Always works

**Cons**:

- Poor UX (no visual feedback)
- Hard to select multiple items
- No styling or colors
- Looks unprofessional

**Why not chosen**: User experience is critical for CLI tools. Modern users expect keyboard navigation, colors, and visual feedback. The improved UX justifies the small overhead of managing a binary.

## Implementation Notes

### Binary Download Strategy

```python
# lib/setup.py
def ensure_gum_binary() -> Path:
    """
    Download Gum binary if needed.

    Steps:
    1. Check if gum in PATH and version >= 0.17.0
    2. If not, detect platform (OS + arch)
    3. Query GitHub API for latest release
    4. Download appropriate asset
    5. Extract to ~/.cache/boxlab/gum/{version}/
    6. Set executable permissions
    7. Return path
    """
```

### Fallback Strategy

When Gum fails (e.g., terminal not interactive, CI/CD environment):

```python
def _stdin_choose_many(prompt: str, choices: list[str]) -> list[str]:
    """
    Fallback to stdin input.

    Shows numbered list:
    1. Plex Media Server
    2. Sonarr
    3. Radarr

    Enter numbers separated by commas (e.g., 1,3,4): _
    """
```

### Debug Mode

Enable verbose logging:

```bash
BOXLAB_DEBUG=1 ./boxlab
```

Shows:

- Gum command arguments
- Process output
- Fallback triggers
- Version checks

## References

- [Charm's Gum Repository](https://github.com/charmbracelet/gum)
- [Gum Documentation](https://github.com/charmbracelet/gum#readme)
- [OpenSpec Design Document](../../../openspec/changes/fix-cli-workflow-and-architecture/design.md)
- [TUI Module Source](../../../lib/tui.py)
