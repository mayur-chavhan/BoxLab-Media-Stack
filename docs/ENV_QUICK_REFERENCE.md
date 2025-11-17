# Environment Variables Quick Reference

Quick reference card for \*arr Stack Manager environment variables.

## Quick Setup

```bash
# 1. Generate example file
arr-stack-manager --generate-env-example

# 2. Copy and edit
cp .env.example .env
nano .env

# 3. Run application
arr-stack-manager
```

## Essential Variables

```bash
# Minimum configuration
PUID=1000                    # Your user ID (run: id -u)
PGID=1000                    # Your group ID (run: id -g)
TZ=America/New_York          # Your timezone
BASE_PATH=/mnt/storage       # Where to store everything
```

## All Variables

| Variable            | Type   | Default              | Example                  |
| ------------------- | ------ | -------------------- | ------------------------ |
| `PUID`              | int    | Current user         | `1000`                   |
| `PGID`              | int    | Current group        | `1000`                   |
| `TZ`                | string | UTC                  | `America/New_York`       |
| `TIMEZONE`          | string | UTC                  | `Europe/London`          |
| `BASE_PATH`         | string | None                 | `/mnt/storage`           |
| `CONFIG_PATH`       | string | `{BASE_PATH}/config` | `/mnt/storage/config`    |
| `DATA_PATH`         | string | `{BASE_PATH}/data`   | `/mnt/storage/data`      |
| `COMPOSE_FILE_PATH` | string | Auto                 | `/opt/stack/compose.yml` |
| `STACK_NAME`        | string | default              | `media-automation`       |

## Priority Order

1. **System environment** (highest)
2. **Current directory .env**
3. **Project root .env**
4. **User config .env** (`~/.config/arr-stack-manager/.env`)
5. **Saved configuration** (lowest)

## Common Commands

```bash
# Check your user/group IDs
id -u && id -g

# List available timezones
timedatectl list-timezones

# Get current timezone
timedatectl show --property=Timezone --value

# Check if variable is set
echo $PUID

# Unset a variable
unset PUID

# Load .env file manually
source .env
```

## File Locations

```bash
# Current directory (highest priority)
./env

# Project root
/path/to/arr-stack-manager/.env

# User config (lowest priority)
~/.config/arr-stack-manager/.env
```

## Security Checklist

- [ ] Add `.env` to `.gitignore`
- [ ] Set file permissions: `chmod 600 .env`
- [ ] Don't commit `.env` to version control
- [ ] Use `.env.example` for templates
- [ ] Keep different `.env` files for dev/prod

## Troubleshooting

### Variable not loading?

```bash
# Check file exists
ls -la .env

# Check syntax (no spaces around =)
cat .env

# Enable verbose logging
arr-stack-manager --verbose
```

### Wrong value being used?

```bash
# Check system environment
echo $PUID

# Unset if needed
unset PUID

# Check all .env locations
cat .env
cat ~/.config/arr-stack-manager/.env
```

### Permission errors?

```bash
# Check ownership
ls -ld /mnt/storage

# Fix ownership
sudo chown -R $USER:$USER /mnt/storage

# Check permissions
chmod u+w /mnt/storage
```

## Example .env File

```bash
# User Configuration
PUID=1000
PGID=1000

# Timezone
TZ=America/New_York

# Paths
BASE_PATH=/mnt/storage

# Stack Name
STACK_NAME=media-automation
```

## More Information

See [Environment Configuration Guide](ENVIRONMENT_CONFIGURATION.md) for complete documentation.
