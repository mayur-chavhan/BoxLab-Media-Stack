# Workflow Documentation

Step-by-step process flows for key BoxLab operations.

## Table of Contents

- [Complete Installation Workflow](#complete-installation-workflow)
- [Service Selection Workflow](#service-selection-workflow)
- [Binary Management Workflow](#binary-management-workflow)
- [Dependency Resolution Workflow](#dependency-resolution-workflow)
- [Configuration Generation Workflow](#configuration-generation-workflow)
- [Error Recovery Workflow](#error-recovery-workflow)

---

## Complete Installation Workflow

The end-to-end process from user launching BoxLab to services running.

```mermaid
graph TD
    A[User runs ./boxlab] --> B{Gum installed?}
    B -->|No| C[Detect Platform]
    B -->|Yes| D{Version OK?}
    C --> E[Download Gum Binary]
    D -->|No| E
    D -->|Yes| F[Display Welcome Banner]
    E --> F
    F --> G{Docker available?}
    G -->|No| H[Show Error: Install Docker]
    G -->|Yes| I[Load Service Catalog]
    H --> Z[Exit]
    I --> J[Group Services by Category]
    J --> K[Display Category Menu]
    K --> L[User Selects Categories]
    L --> M[Display Service Menu]
    M --> N[User Selects Services]
    N --> O[Resolve Dependencies]
    O --> P{Conflicts?}
    P -->|Yes| Q[Show Conflict Warning]
    P -->|No| R[Prompt for Configuration]
    Q --> R
    R --> S[Generate docker-compose.yml]
    S --> T[Set Directory Permissions]
    T --> U[Save Configuration]
    U --> V[docker compose up -d]
    V --> W[Display Success Message]
    W --> X[Show Access URLs]
    X --> Y[Exit]
```

### Step-by-Step Breakdown

#### 1. **Entry Point** (`./boxlab`)

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add bin/ to PATH for Gum binary
bin_dir = Path(__file__).parent / "bin"
sys.path.insert(0, str(Path(__file__).parent))

from lib.setup import ensure_gum_binary, GumSetupError
from lib.cli import run_cli

try:
    ensure_gum_binary()
except GumSetupError as e:
    print(f"Error: {e}")
    sys.exit(1)

run_cli()
```

#### 2. **Binary Setup** (`lib/setup.py`)

- Check if `gum` is in PATH
- If not found or outdated:
  - Detect OS and architecture
  - Fetch latest version from GitHub
  - Download appropriate asset
  - Extract to `~/.cache/boxlab/gum/{version}/`
  - Set executable permissions
- Return path to binary

#### 3. **CLI Workflow** (`lib/cli.py`)

- Display welcome banner with ASCII art
- Check Docker installation
- Load service catalog
- Present service selection
- Collect configuration inputs
- Resolve dependencies
- Generate compose file
- Launch services

---

## Service Selection Workflow

How users select services with dependency resolution.

```mermaid
sequenceDiagram
    participant User
    participant TUI
    participant Catalog
    participant Composer

    User->>TUI: Launch BoxLab
    TUI->>Catalog: Load service catalog
    Catalog-->>TUI: Return services by category
    TUI->>User: Display category menu
    User->>TUI: Select "Media Servers"
    TUI->>User: Display media server services
    User->>TUI: Select "Plex"
    TUI->>Catalog: Resolve dependencies for ["plex"]
    Catalog-->>TUI: Return ["plex"] (no deps)
    TUI->>User: Display "VPN Options" menu
    User->>TUI: Select "Gluetun"
    TUI->>Catalog: Resolve dependencies for ["plex", "gluetun"]
    Catalog-->>TUI: Return ["plex", "gluetun"]
    TUI->>Catalog: Check conflicts
    Catalog-->>TUI: No conflicts
    TUI->>User: Confirm selection
    User->>TUI: Confirm
    TUI->>Composer: Generate compose file
    Composer-->>TUI: docker-compose.yml content
    TUI->>User: Display success
```

### Dependency Resolution Algorithm

```python
def resolve_dependencies(selected: list[str], services: dict) -> list[str]:
    """
    Recursively resolve service dependencies.

    Args:
        selected: User-selected service names
        services: Full service catalog

    Returns:
        Complete list including all dependencies
    """
    resolved = set(selected)
    to_process = list(selected)

    while to_process:
        service = to_process.pop(0)

        if service not in services:
            raise ValueError(f"Unknown service: {service}")

        # Get dependencies
        deps = services[service].get("dependencies", [])

        for dep in deps:
            if dep not in resolved:
                resolved.add(dep)
                to_process.append(dep)

    return sorted(resolved)
```

### Example Flow

**User Input**: `["sonarr", "radarr"]`

**Resolution Process**:

1. Check `sonarr` dependencies → `["prowlarr"]`
2. Add `prowlarr` to list
3. Check `radarr` dependencies → `["prowlarr"]`
4. `prowlarr` already in list, skip
5. Check `prowlarr` dependencies → `[]`

**Final Output**: `["prowlarr", "radarr", "sonarr"]` (sorted alphabetically)

---

## Binary Management Workflow

How Gum binary is installed and managed across platforms.

```mermaid
stateDiagram-v2
    [*] --> CheckInstalled
    CheckInstalled --> CheckVersion: Found in PATH
    CheckInstalled --> DetectPlatform: Not found

    CheckVersion --> GetLatestVersion: Outdated
    CheckVersion --> Ready: Up to date

    DetectPlatform --> GetOSArch
    GetOSArch --> GetLatestVersion

    GetLatestVersion --> QueryGitHub
    QueryGitHub --> DetermineAsset
    DetermineAsset --> DownloadBinary

    DownloadBinary --> ExtractArchive
    ExtractArchive --> SetPermissions
    SetPermissions --> CacheBinary
    CacheBinary --> UpdatePATH
    UpdatePATH --> Ready

    Ready --> [*]
```

### Platform Detection

```python
def get_gum_asset_name(version: str) -> str:
    """
    Determine correct asset name for current platform.

    Supported platforms:
    - linux_x86_64 → gum_{version}_Linux_x86_64.tar.gz
    - linux_arm64 → gum_{version}_Linux_arm64.tar.gz
    - darwin_x86_64 → gum_{version}_Darwin_x86_64.tar.gz
    - darwin_arm64 → gum_{version}_Darwin_arm64.tar.gz
    """
    os_type = get_os()  # "linux" or "darwin"
    arch = get_arch()  # "x86_64" or "arm64"

    os_map = {
        "linux": "Linux",
        "darwin": "Darwin"
    }

    return f"gum_{version}_{os_map[os_type]}_{arch}.tar.gz"
```

### Cache Strategy

**Directory Structure**:

```
~/.cache/boxlab/
└── gum/
    ├── 0.17.0/
    │   └── gum (executable)
    └── 0.18.0/
        └── gum (executable)
```

**Version Management**:

- Multiple versions can coexist
- Latest version used by default
- Old versions cleaned up after 30 days (TODO)

---

## Dependency Resolution Workflow

How service dependencies are resolved and validated.

```mermaid
graph LR
    A[User Selections] --> B[Create Set]
    B --> C[Process Queue]
    C --> D{More services?}
    D -->|Yes| E[Get Service Config]
    D -->|No| I[Check Conflicts]
    E --> F{Has dependencies?}
    F -->|Yes| G[Add to Queue]
    F -->|No| C
    G --> H[Add to Resolved Set]
    H --> C
    I --> J{Conflicts found?}
    J -->|Yes| K[Warn User]
    J -->|No| L[Return Resolved Set]
    K --> M[Allow Override?]
    M -->|Yes| L
    M -->|No| A
```

### Conflict Detection

```python
def check_conflicts(services: list[str], catalog: dict) -> list[tuple[str, str]]:
    """
    Check for conflicting services.

    Args:
        services: List of selected service names
        catalog: Full service catalog

    Returns:
        List of conflict pairs [(service1, service2), ...]
    """
    conflicts = []

    for i, service1 in enumerate(services):
        config1 = catalog[service1]
        conflict_list = config1.get("conflicts", [])

        for service2 in services[i+1:]:
            if service2 in conflict_list:
                conflicts.append((service1, service2))

    return conflicts
```

### Example Conflicts

| Service A   | Service B  | Reason                          |
| ----------- | ---------- | ------------------------------- |
| Gluetun     | Windscribe | Multiple VPN providers conflict |
| Plex        | Jellyfin   | Same port (8096) by default     |
| qBittorrent | Deluge     | Same port (8080) for web UI     |

---

## Configuration Generation Workflow

How configuration is collected and docker-compose.yml is generated.

```mermaid
sequenceDiagram
    participant User
    participant TUI
    participant Config
    participant Composer
    participant FileSystem

    TUI->>User: Prompt for data directory
    User->>TUI: Enter "/mnt/media"

    TUI->>User: Prompt for PUID/PGID
    User->>TUI: Use defaults (current user)

    TUI->>Config: Save configuration
    Config->>FileSystem: Write ~/.config/boxlab/config.yaml

    TUI->>Composer: Generate compose file
    Composer->>Composer: Load service templates
    Composer->>Composer: Substitute variables
    Composer->>Composer: Merge volumes and networks
    Composer->>TUI: Return YAML content

    TUI->>FileSystem: Write docker-compose.yml
    TUI->>User: Show success message
```

### Configuration Template

```yaml
# ~/.config/boxlab/config.yaml
version: 1

directories:
  data_dir: /mnt/media
  config_dir: /mnt/config

user:
  puid: 1000
  pgid: 1000

vpn:
  provider: pia
  username: ${VPN_USERNAME}
  password: ${VPN_PASSWORD}

services:
  - plex
  - sonarr
  - radarr
  - prowlarr
  - gluetun
```

### Compose Generation

```python
def generate_compose(services: list[str], config: dict) -> str:
    """
    Generate docker-compose.yml from templates.

    Args:
        services: List of service names
        config: User configuration

    Returns:
        Complete docker-compose.yml as string
    """
    compose = {
        "version": "3.8",
        "services": {},
        "networks": {},
        "volumes": {}
    }

    for service in services:
        template = load_service_template(service)
        compose["services"][service] = substitute_vars(template, config)

    return yaml.dump(compose)
```

---

## Error Recovery Workflow

How BoxLab handles and recovers from errors.

```mermaid
graph TD
    A[Error Occurs] --> B{Error Type?}

    B -->|GumSetupError| C[Binary installation failed]
    B -->|GumInteractionError| D[User interaction failed]
    B -->|UnsupportedPlatformError| E[Platform not supported]
    B -->|GumNotInstalledError| F[Gum missing]

    C --> G[Show GitHub download instructions]
    G --> H[Exit with code 1]

    D --> I[Fallback to stdin input]
    I --> J[Continue workflow]

    E --> K[List supported platforms]
    K --> H

    F --> L[Attempt auto-install]
    L --> M{Install successful?}
    M -->|Yes| J
    M -->|No| G
```

### Error Message Examples

#### GumSetupError

```
Error: Failed to install Gum binary

BoxLab requires Charm's Gum for interactive menus.

Attempted to:
- Download from: https://github.com/charmbracelet/gum/releases
- Install to: ~/.cache/boxlab/gum/0.17.0/

Error: HTTP 404 - Asset not found for darwin_arm64

Manual installation:
  brew install gum

Then re-run BoxLab.
```

#### GumInteractionError with Fallback

```
Warning: Gum menu failed, using text input fallback

Available services:
  1. Plex Media Server
  2. Sonarr
  3. Radarr
  4. Prowlarr

Enter numbers separated by commas (e.g., 1,2,3): _
```

### Debug Mode

Enable detailed logging:

```bash
BOXLAB_DEBUG=1 ./boxlab
```

**Debug Output**:

```
[DEBUG] Platform: darwin arm64
[DEBUG] Gum version: 0.17.0
[DEBUG] Running: gum choose --no-limit --selected=Plex Plex Sonarr Radarr
[DEBUG] Process exited with code: 0
[DEBUG] Output: Plex
Sonarr
```

---

## State Persistence Workflow

How workflow state is saved and resumed (TODO).

```mermaid
stateDiagram-v2
    [*] --> Initialize
    Initialize --> LoadState
    LoadState --> CheckState: State file exists
    LoadState --> StartNew: No state file

    CheckState --> ResumeStep
    StartNew --> Step1

    Step1 --> SaveState1
    SaveState1 --> Step2
    Step2 --> SaveState2
    SaveState2 --> Step3

    ResumeStep --> Step2: Resume from step 2
    ResumeStep --> Step3: Resume from step 3

    Step3 --> Complete
    Complete --> DeleteState
    DeleteState --> [*]
```

### State File Format

```json
{
  "version": 1,
  "workflow_id": "install_services",
  "current_step": 3,
  "total_steps": 7,
  "completed_steps": [1, 2],
  "state": {
    "selected_services": ["plex", "sonarr", "radarr"],
    "configuration": {
      "data_dir": "/mnt/media",
      "puid": 1000,
      "pgid": 1000
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Location**: `~/.config/boxlab/workflow-state.json`

---

**Next**: See [Architecture Decisions](./decisions/) for ADR records.
