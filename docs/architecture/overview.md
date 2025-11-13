# System Architecture Overview

BoxLab Media Server Stack is a Python-based CLI tool for managing self-hosted media automation services using Docker Compose.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         BoxLab CLI                          │
│                       (Entry Point)                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Workflow Layer                         │
│  • State Management     • Step Orchestration                │
│  • Progress Tracking    • Resume Capability                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  UI Layer    │  │  Core Logic  │  │  Knowledge   │
│              │  │              │  │  Management  │
│ • TUI (Gum)  │  │ • Catalog    │  │              │
│ • Menus      │  │ • Composer   │  │ • ByteRover  │
│ • Input      │  │ • Config     │  │ • Patterns   │
│ • Display    │  │ • Perms      │  │ • Solutions  │
└──────┬───────┘  └──────┬───────┘  └──────────────┘
       │                 │
       │                 ▼
       │          ┌──────────────┐
       │          │  Data Layer  │
       │          │              │
       │          │ • YAML Parse │
       │          │ • Templates  │
       │          │ • Validation │
       │          └──────┬───────┘
       │                 │
       ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Platform Layer                           │
│  • OS Detection     • Binary Management                     │
│  • Arch Detection   • Cache Management                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Systems                          │
│  • Docker Engine    • GitHub API     • Gum Binary           │
└─────────────────────────────────────────────────────────────┘
```

## Core Principles

### 1. **Cross-Platform First**

- Pure Python implementation (no bash dependencies)
- Platform-agnostic binary management
- OS/architecture detection at runtime
- Supports: Linux (x86_64, ARM64), macOS (x86_64, ARM64)

### 2. **Graceful Degradation**

- TUI with stdin fallback when Gum fails
- Debug logging for troubleshooting
- Clear error messages with actionable steps

### 3. **Modular Design**

- Clear separation of concerns
- Independent, testable modules
- Minimal inter-module dependencies
- Easy to extend and maintain

### 4. **State Management**

- Workflow state persistence
- Resume capability for interrupted operations
- Configuration caching
- Binary version management

## Module Layers

### **Entry Layer** (`/boxlab`)

- Main executable entry point
- PATH configuration for Gum binary
- Graceful error handling
- Ensures dependencies before launching CLI

### **UI Layer** (`lib/tui.py`)

- Terminal user interface using Gum
- Menu selection (single/multiple)
- Input collection and validation
- Styled output and formatting
- Stdin fallback for compatibility

### **Core Logic Layer**

- **`lib/catalog.py`** - Service catalog and dependency resolution
- **`lib/compose.py`** - Docker Compose file generation
- **`lib/config.py`** - Configuration management (YAML parsing)
- **`lib/permissions.py`** - PUID/PGID and permission handling
- **`lib/cli.py`** - Main CLI workflow orchestration

### **Platform Layer**

- **`lib/platform.py`** - OS and architecture detection
- **`lib/setup.py`** - Gum binary download and installation
- **`lib/gum.py`** - Version parsing and validation
- **`lib/constants.py`** - Global configuration constants

### **Workflow Layer** (`lib/workflow.py`)

- Step-based workflow orchestration
- Progress tracking and state persistence
- Resume capability for interrupted flows
- Validation and rollback support

### **Knowledge Layer** (`lib/knowledge.py`)

- Integration with ByteRover MCP
- Pattern and solution storage
- Architecture decision recording
- Knowledge retrieval helpers

## Data Flow

### Service Selection Flow

```
User Launch
    │
    ▼
Ensure Gum Binary (lib/setup.py)
    │
    ▼
Display Service Catalog (lib/catalog.py)
    │
    ▼
User Selects Services (lib/tui.py)
    │
    ▼
Resolve Dependencies (lib/catalog.py)
    │
    ▼
Generate Config (lib/config.py)
    │
    ▼
Generate Compose File (lib/compose.py)
    │
    ▼
Set Permissions (lib/permissions.py)
    │
    ▼
Launch Services (docker compose up)
```

### Binary Management Flow

```
Application Start
    │
    ▼
Check Gum Installation (lib/gum.py)
    │
    ├─ Installed? ─> Check Version ─> OK? ─> Continue
    │                      │
    │                      └─ Outdated? ─> Download New
    │
    └─ Not Installed? ─> Detect Platform (lib/platform.py)
                              │
                              ▼
                        Download from GitHub (lib/setup.py)
                              │
                              ▼
                        Cache at ~/.cache/boxlab/gum/{version}/
                              │
                              ▼
                        Extract and Set Permissions
                              │
                              ▼
                        Add to PATH
```

## Configuration Management

### File Locations

- **User Config**: `~/.config/boxlab/config.yaml`
- **Workflow State**: `~/.config/boxlab/workflow-state.json`
- **Binary Cache**: `~/.cache/boxlab/gum/{version}/`
- **Docker Compose**: `./docker-compose.yml`

### Configuration Hierarchy

1. Command-line arguments (highest priority)
2. Environment variables
3. User config file (`~/.config/boxlab/config.yaml`)
4. Default values (lowest priority)

## Error Handling

### Exception Hierarchy

```
Exception
│
├─ GumSetupError (Binary installation failed)
│
├─ UnsupportedPlatformError (OS/arch not supported)
│
├─ GumNotInstalledError (Gum missing when required)
│
└─ GumInteractionError (User interaction failed)
```

### Error Recovery

- **Automatic**: Retry with exponential backoff for network errors
- **Fallback**: Use stdin when Gum interaction fails
- **User Guidance**: Clear error messages with resolution steps
- **Debug Mode**: Enable with `BOXLAB_DEBUG=1` for detailed logging

## Performance Considerations

### Optimization Strategies

- **Caching**: Platform detection cached with `@lru_cache`
- **Lazy Loading**: Modules imported only when needed
- **Binary Reuse**: Gum binary cached and reused across runs
- **Minimal API Calls**: GitHub API rate limiting handled gracefully

### Resource Management

- **Memory**: Streaming large files during download
- **Disk**: Old binary versions cleaned up automatically
- **Network**: Progress indicators for downloads
- **CPU**: Minimal processing, delegating to Docker

## Security

### Threat Model

- **Binary Verification**: SHA256 checksums validated (TODO)
- **Permissions**: Minimal file permissions (755 for binaries)
- **API Access**: GitHub API uses personal token when available
- **Docker Socket**: Requires user in `docker` group

### Best Practices

- No hardcoded credentials
- Secrets via environment variables
- Docker socket permissions verified
- Binary downloads over HTTPS only

## Extensibility

### Adding New Services

1. Add entry to `lib/catalog.py` `SERVICES` dict
2. Define dependencies (if any)
3. Add configuration template
4. Update documentation

### Adding New Platform Support

1. Add OS/arch enum to `lib/platform.py`
2. Update `get_gum_asset_name()` mapping
3. Test binary download and execution
4. Update documentation

### Adding New UI Components

1. Add function to `lib/tui.py`
2. Implement Gum integration with stdin fallback
3. Add error handling and debug logging
4. Document usage and examples

## Future Architecture Enhancements

### Planned Improvements

- **Plugin System**: Load external service definitions
- **Multi-Stack Support**: Manage multiple compose files
- **Backup/Restore**: Automated config and data backup
- **Health Monitoring**: Service status dashboard
- **Update Notifications**: Check for new service versions

### Scalability Considerations

- Currently designed for single-host deployments
- Future: Multi-host orchestration with Docker Swarm
- Future: Kubernetes deployment templates

---

**Next**: See [Module Documentation](./modules.md) for detailed module API docs.
