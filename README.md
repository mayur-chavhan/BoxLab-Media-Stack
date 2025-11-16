# \*arr Stack Manager

A Terminal User Interface (TUI) application for deploying and managing Docker-based media automation stacks.

## Overview

The *arr Stack Manager simplifies the deployment and management of media automation services (Sonarr, Radarr, Prowlarr, Jellyfin, and other *arr ecosystem applications) through an intuitive menu-driven interface. It automatically applies Trash-Guides best practices and handles Docker Compose configuration generation.

## Features

- **Interactive TUI**: Clean, intuitive terminal interface built with Textual
- **Service Selection**: Choose from a comprehensive list of media automation services
- **Configuration Wizard**: Step-by-step setup for paths, users, ports, and service-specific settings
- **Best Practices**: Automatic application of Trash-Guides recommendations
- **Docker Management**: Start, stop, restart, update, and monitor services
- **Real-time Monitoring**: View service status, resource usage, and logs
- **Validation**: Pre-deployment validation to catch configuration errors early

## Supported Services

### Media Management

- Sonarr (TV shows)
- Radarr (Movies)
- Prowlarr (Indexer management)
- Bazarr (Subtitles)
- Recyclarr (TRaSH-Guides sync)

### Media Servers

- Jellyfin
- Emby
- Plex

### Request Management

- Jellyseerr
- Overseerr

### Download Clients & Indexers

- Jackett
- Autobrr

### Media Processing

- Tdarr (Transcoding)
- Unpackerr (Archive extraction)

## Requirements

- Python 3.11 or higher
- Docker and Docker Compose
- Linux-based system (tested on Ubuntu, Debian, Arch)

## Installation

### Using uv (recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install arr-stack-manager
uv tool install arr-stack-manager
```

### From source

```bash
# Clone the repository
git clone https://github.com/yourusername/arr-stack-manager.git
cd arr-stack-manager

# Install with uv
uv sync

# Run the application
uv run arr-stack-manager
```

## Quick Start

1. Launch the application:

   ```bash
   arr-stack-manager
   ```

2. Select the services you want to deploy

3. Follow the configuration wizard to set up:

   - User permissions (PUID/PGID)
   - Timezone
   - Directory structure
   - Service-specific settings

4. Review and deploy your stack

5. Manage services from the dashboard

## Command-Line Options

```bash
arr-stack-manager [OPTIONS]

Options:
  --version                Show version and exit
  --config-dir PATH        Custom configuration directory (default: ~/.config/arr-stack-manager)
  --template-dir PATH      Custom template directory (default: built-in templates)
  --stack-name NAME        Name of the stack to load on startup
  --welcome                Show welcome screen on startup
  --verbose, -v            Enable verbose (DEBUG) logging
  --log-file PATH          Write logs to specified file
  --no-docker-check        Skip Docker availability check on startup (for testing)
  -h, --help               Show help message and exit
```

### Examples

```bash
# Start with default configuration
arr-stack-manager

# Load a specific stack
arr-stack-manager --stack-name media-automation

# Use custom configuration directory
arr-stack-manager --config-dir /path/to/config

# Show welcome screen on startup
arr-stack-manager --welcome

# Enable verbose logging
arr-stack-manager --verbose

# Save logs to a file
arr-stack-manager --log-file /var/log/arr-stack-manager.log
```

## Keyboard Shortcuts

### Global Shortcuts

- `q` - Quit application
- `h` or `?` - Show help screen
- `d` - Go to Dashboard
- `s` - Go to Service Selector
- `c` - Go to Configuration Wizard
- `m` - Go to Stack Manager
- `r` - Refresh current screen

### Screen-Specific Shortcuts

See the help screen (`h` or `?`) for detailed information about keyboard shortcuts for each screen.

## Configuration

The application stores configuration in `~/.config/arr-stack-manager/`:

- `config.json`: User preferences and stack configurations
- `stacks/`: Generated Docker Compose files for each stack

## Development

### Setup

```bash
# Install development dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run type checker
uv run mypy src/
```

### Project Structure

```
arr-stack-manager/
├── src/
│   └── arr_stack_manager/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── controller.py
│       ├── core/
│       ├── models/
│       ├── screens/
│       ├── components/
│       ├── utils/
│       └── templates/
├── tests/
├── pyproject.toml
└── README.md
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [Trash-Guides](https://trash-guides.info/) for best practices documentation
- [Textual](https://textual.textualize.io/) for the excellent TUI framework
- The \*arr community for creating amazing media automation tools
