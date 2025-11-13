# Module Documentation

Detailed documentation for each module in the BoxLab architecture.

## Table of Contents

- [Platform Module (`lib/platform.py`)](#platform-module)
- [Setup Module (`lib/setup.py`)](#setup-module)
- [Gum Module (`lib/gum.py`)](#gum-module)
- [Constants Module (`lib/constants.py`)](#constants-module)
- [TUI Module (`lib/tui.py`)](#tui-module)
- [Catalog Module (`lib/catalog.py`)](#catalog-module)
- [Composer Module (`lib/compose.py`)](#composer-module)
- [Config Module (`lib/config.py`)](#config-module)
- [Permissions Module (`lib/permissions.py`)](#permissions-module)
- [CLI Module (`lib/cli.py`)](#cli-module)
- [Workflow Module (`lib/workflow.py`)](#workflow-module)
- [Knowledge Module (`lib/knowledge.py`)](#knowledge-module)

---

## Platform Module

**File**: `lib/platform.py`  
**Purpose**: OS and architecture detection for cross-platform binary management

### Types

```python
OSType = Literal["linux", "darwin"]
ArchType = Literal["x86_64", "arm64"]
```

### Functions

#### `get_os() -> OSType`

Detects the current operating system.

**Returns**: `"linux"` or `"darwin"` (macOS)  
**Raises**: `UnsupportedPlatformError` if OS is not supported  
**Caching**: Results cached with `@lru_cache` for performance

**Example**:

```python
from lib.platform import get_os
os_type = get_os()  # Returns "darwin" on macOS
```

#### `get_arch() -> ArchType`

Detects the current CPU architecture.

**Returns**: `"x86_64"` or `"arm64"`  
**Raises**: `UnsupportedPlatformError` if architecture is not supported  
**Caching**: Results cached with `@lru_cache`

**Example**:

```python
from lib.platform import get_arch
arch = get_arch()  # Returns "arm64" on Apple Silicon
```

#### `get_gum_asset_name(version: str = "latest") -> str`

Determines the correct Gum binary asset name for GitHub releases.

**Parameters**:

- `version` (str): Version string (e.g., "0.17.0" or "latest")

**Returns**: Asset filename (e.g., `"gum_0.17.0_Darwin_arm64.tar.gz"`)  
**Raises**: `UnsupportedPlatformError` if OS/arch combination not supported

**Example**:

```python
from lib.platform import get_gum_asset_name
asset = get_gum_asset_name("0.17.0")
# Returns: "gum_0.17.0_Darwin_arm64.tar.gz" on macOS ARM64
```

### Error Handling

```python
class UnsupportedPlatformError(Exception):
    """Raised when OS or architecture is not supported"""
    pass
```

---

## Setup Module

**File**: `lib/setup.py`  
**Purpose**: Gum binary download, installation, and cache management

### Functions

#### `ensure_gum_binary() -> Path`

Ensures Gum binary is installed and returns its path.

**Workflow**:

1. Check if Gum is in PATH
2. If not found or outdated:
   - Detect platform
   - Determine latest version from GitHub API
   - Download appropriate asset
   - Extract to cache directory
   - Set executable permissions
3. Return path to binary

**Returns**: `Path` object pointing to Gum executable  
**Raises**:

- `GumSetupError` if installation fails
- `UnsupportedPlatformError` if platform not supported

**Cache Location**: `~/.cache/boxlab/gum/{version}/gum`

**Example**:

```python
from lib.setup import ensure_gum_binary

try:
    gum_path = ensure_gum_binary()
    print(f"Gum binary at: {gum_path}")
except GumSetupError as e:
    print(f"Installation failed: {e}")
```

### Implementation Details

#### GitHub API Integration

- Fetches latest release from `charmbracelet/gum`
- Parses version and asset URLs
- Handles rate limiting gracefully
- Uses personal token if `GITHUB_TOKEN` env var set

#### Download Process

- Streams large files to avoid memory issues
- Shows progress indicator
- Validates content-type
- Retries on network errors (exponential backoff)

#### Extraction

- Supports `.tar.gz` format
- Extracts only `gum` binary (ignores other files)
- Sets permissions to `755` (executable)

#### Cache Management

- Creates directory structure: `~/.cache/boxlab/gum/{version}/`
- Reuses existing installations
- Cleans up old versions (TODO)

### Error Handling

```python
class GumSetupError(Exception):
    """Raised when Gum binary setup fails"""
    pass
```

---

## Gum Module

**File**: `lib/gum.py`  
**Purpose**: Gum version management and validation

### Functions

#### `parse_version(version_str: str) -> tuple[int, int, int]`

Parses semantic version string into tuple.

**Parameters**:

- `version_str` (str): Version like "0.17.0" or "v0.17.0"

**Returns**: Tuple of (major, minor, patch)

**Example**:

```python
from lib.gum import parse_version
version = parse_version("v0.17.0")  # Returns (0, 17, 0)
```

#### `get_gum_version() -> tuple[int, int, int] | None`

Gets the installed Gum version.

**Returns**: Version tuple or `None` if not installed

**Example**:

```python
from lib.gum import get_gum_version
version = get_gum_version()
if version and version >= (0, 17, 0):
    print("Gum is up to date")
```

#### `version_to_str(version: tuple[int, int, int]) -> str`

Converts version tuple to string.

**Parameters**:

- `version` (tuple): (major, minor, patch)

**Returns**: String like "0.17.0"

**Example**:

```python
from lib.gum import version_to_str
print(version_to_str((0, 17, 0)))  # "0.17.0"
```

---

## Constants Module

**File**: `lib/constants.py`  
**Purpose**: Global configuration constants

### Constants

```python
GUM_MIN_VERSION: tuple[int, int, int] = (0, 17, 0)
```

Minimum required Gum version for BoxLab functionality.

---

## TUI Module

**File**: `lib/tui.py`  
**Purpose**: Terminal user interface components using Gum

### Functions

#### `choose_many(prompt: str, choices: list[str], selected: list[str] = None) -> list[str]`

Displays multi-select menu.

**Parameters**:

- `prompt` (str): Message to display
- `choices` (list[str]): Available options
- `selected` (list[str], optional): Pre-selected items

**Returns**: List of selected items  
**Raises**: `GumInteractionError` if interaction fails

**Fallback**: Uses stdin if Gum fails, showing numbered list

**Example**:

```python
from lib.tui import choose_many

services = ["Plex", "Sonarr", "Radarr", "Prowlarr"]
selected = choose_many(
    "Select services to install:",
    services,
    selected=["Plex"]
)
print(f"You selected: {', '.join(selected)}")
```

#### `choose_one(prompt: str, choices: list[str], default: str = None) -> str`

Displays single-select menu.

**Parameters**:

- `prompt` (str): Message to display
- `choices` (list[str]): Available options
- `default` (str, optional): Default selection

**Returns**: Selected item  
**Raises**: `GumInteractionError` if interaction fails

**Fallback**: Uses stdin if Gum fails

**Example**:

```python
from lib.tui import choose_one

theme = choose_one(
    "Select theme:",
    ["dark", "light", "auto"],
    default="auto"
)
```

#### `input_text(prompt: str, placeholder: str = "", default: str = "") -> str`

Prompts for text input.

**Parameters**:

- `prompt` (str): Message to display
- `placeholder` (str, optional): Hint text
- `default` (str, optional): Default value

**Returns**: User input string

**Example**:

```python
from lib.tui import input_text

username = input_text(
    "Enter username:",
    placeholder="admin",
    default="admin"
)
```

#### `confirm(prompt: str, default: bool = True) -> bool`

Displays yes/no confirmation.

**Parameters**:

- `prompt` (str): Question to ask
- `default` (bool, optional): Default answer

**Returns**: True if confirmed, False otherwise

**Example**:

```python
from lib.tui import confirm

if confirm("Install VPN support?", default=False):
    print("Installing VPN...")
```

#### `display_info(title: str, message: str)`

Displays styled info box.

**Parameters**:

- `title` (str): Box title
- `message` (str): Content to display

**Example**:

```python
from lib.tui import display_info

display_info(
    "Installation Complete",
    "Your media server is ready!\nAccess at: http://localhost:8096"
)
```

### Debug Logging

Enable debug output with environment variable:

```bash
BOXLAB_DEBUG=1 ./boxlab
```

Debug logs show:

- Gum command arguments
- Process output
- Stdin fallback triggers
- Version checks

### Error Handling

```python
class GumInteractionError(Exception):
    """Raised when user interaction via Gum fails"""
    pass
```

---

## Catalog Module

**File**: `lib/catalog.py`  
**Purpose**: Service catalog and dependency resolution

### Data Structures

```python
SERVICES = {
    "service_name": {
        "name": "Display Name",
        "description": "Brief description",
        "port": 8080,
        "category": "media|download|indexer|vpn|etc",
        "dependencies": ["other_service"],
        "conflicts": ["incompatible_service"],
        "requires_vpn": False,
        "image": "docker/image:tag",
        "environment": {...},
        "volumes": [...],
    }
}
```

### Functions

#### `get_services_by_category() -> dict[str, list[str]]`

Groups services by category.

**Returns**: Dict mapping category name to list of service names

**Example**:

```python
from lib.catalog import get_services_by_category

categories = get_services_by_category()
for category, services in categories.items():
    print(f"{category}: {', '.join(services)}")
```

#### `resolve_dependencies(selected: list[str]) -> list[str]`

Resolves service dependencies recursively.

**Parameters**:

- `selected` (list[str]): User-selected services

**Returns**: Complete list including dependencies

**Example**:

```python
from lib.catalog import resolve_dependencies

# User selects Sonarr
selected = ["sonarr"]
# Returns: ["sonarr", "prowlarr"] (Prowlarr is dependency)
complete = resolve_dependencies(selected)
```

#### `check_conflicts(services: list[str]) -> list[tuple[str, str]]`

Checks for conflicting services.

**Parameters**:

- `services` (list[str]): Services to check

**Returns**: List of conflict pairs

**Example**:

```python
from lib.catalog import check_conflicts

conflicts = check_conflicts(["vpn_service_a", "vpn_service_b"])
if conflicts:
    print(f"Conflict: {conflicts[0][0]} and {conflicts[0][1]}")
```

---

## Composer Module

**File**: `lib/compose.py`  
**Purpose**: Docker Compose file generation

### Functions

#### `generate_compose(services: list[str], config: dict) -> str`

Generates Docker Compose YAML from selected services.

**Parameters**:

- `services` (list[str]): Services to include
- `config` (dict): Configuration (ports, paths, env vars)

**Returns**: YAML string

**Example**:

```python
from lib.compose import generate_compose

services = ["plex", "sonarr", "radarr"]
config = {
    "data_dir": "/mnt/media",
    "vpn_provider": "pia",
}
yaml_content = generate_compose(services, config)

with open("docker-compose.yml", "w") as f:
    f.write(yaml_content)
```

---

## Config Module

**File**: `lib/config.py`  
**Purpose**: Configuration management (load/save/validate)

### Functions

#### `load_config(path: Path = None) -> dict`

Loads configuration from YAML file.

**Parameters**:

- `path` (Path, optional): Config file path (default: `~/.config/boxlab/config.yaml`)

**Returns**: Configuration dict

#### `save_config(config: dict, path: Path = None)`

Saves configuration to YAML file.

**Parameters**:

- `config` (dict): Configuration to save
- `path` (Path, optional): Destination path

#### `validate_config(config: dict) -> list[str]`

Validates configuration structure.

**Parameters**:

- `config` (dict): Configuration to validate

**Returns**: List of validation errors (empty if valid)

---

## Permissions Module

**File**: `lib/permissions.py`  
**Purpose**: PUID/PGID and file permission handling

### Functions

#### `get_current_user_ids() -> tuple[int, int]`

Gets current user's UID and GID.

**Returns**: Tuple of (PUID, PGID)

#### `set_directory_permissions(path: Path, uid: int, gid: int)`

Sets ownership and permissions on directory.

**Parameters**:

- `path` (Path): Directory to modify
- `uid` (int): User ID
- `gid` (int): Group ID

---

## CLI Module

**File**: `lib/cli.py`  
**Purpose**: Main CLI workflow orchestration

### Functions

#### `run_cli()`

Main entry point for CLI workflow.

**Workflow**:

1. Display welcome banner
2. Check Docker availability
3. Present service selection
4. Configure selected services
5. Resolve dependencies
6. Generate compose file
7. Set permissions
8. Launch services

---

## Workflow Module

**File**: `lib/workflow.py`  
**Purpose**: Step-based workflow orchestration with state persistence

### Classes

#### `WorkflowStep`

Represents a single workflow step.

**Attributes**:

- `id` (str): Unique step identifier
- `name` (str): Display name
- `action` (Callable): Function to execute
- `validation` (Callable, optional): Validation function
- `rollback` (Callable, optional): Rollback function

#### `WorkflowOrchestrator`

Manages workflow execution.

**Methods**:

- `add_step(step: WorkflowStep)`: Add step to workflow
- `run()`: Execute all steps
- `resume()`: Resume from saved state
- `get_progress() -> tuple[int, int]`: Get current step number and total

---

## Knowledge Module

**File**: `lib/knowledge.py`  
**Purpose**: ByteRover MCP integration for pattern storage

### Functions

#### `store_pattern(pattern_type: str, content: str, context: dict = None)`

Stores a reusable pattern.

**Parameters**:

- `pattern_type` (str): Type of pattern (e.g., "error_solution", "architecture")
- `content` (str): Pattern content
- `context` (dict, optional): Additional metadata

#### `retrieve_pattern(query: str, limit: int = 3) -> list[dict]`

Retrieves patterns matching query.

**Parameters**:

- `query` (str): Search query
- `limit` (int): Max results

**Returns**: List of matching patterns

---

**Next**: See [Workflow Documentation](./workflows.md) for step-by-step process flows.
