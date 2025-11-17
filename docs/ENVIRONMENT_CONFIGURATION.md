# Environment Configuration Guide

This guide explains how to configure the \*arr Stack Manager using environment variables and `.env` files.

## Overview

The \*arr Stack Manager supports configuration through environment variables, allowing you to:

- Set default values for the configuration wizard
- Override saved configuration values
- Automate deployments with predefined settings
- Manage multiple environments (development, production, etc.)

## Supported Environment Variables

### User and Group IDs

#### `PUID` (integer)

**Description:** User ID for container processes. This should match the user that owns your media files.

**Default:** Current user's UID (automatically detected)

**Example:**

```bash
PUID=1000
```

**Notes:**

- Must be a valid system user ID (≥ 0)
- Use `id -u` to find your current user ID
- Ensures containers can read/write your media files

#### `PGID` (integer)

**Description:** Group ID for container processes. This should match the group that owns your media files.

**Default:** Current user's GID (automatically detected)

**Example:**

```bash
PGID=1000
```

**Notes:**

- Must be a valid system group ID (≥ 0)
- Use `id -g` to find your current group ID
- Ensures proper file permissions for shared access

### Timezone Configuration

#### `TZ` (string)

**Description:** Timezone for all services using TZ database format.

**Default:** UTC

**Example:**

```bash
TZ=America/New_York
```

**Valid Values:**

- Any valid TZ database timezone (e.g., `America/Los_Angeles`, `Europe/London`, `Asia/Tokyo`)
- See [List of TZ database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

#### `TIMEZONE` (string)

**Description:** Alternative to `TZ` for timezone configuration.

**Default:** UTC

**Example:**

```bash
TIMEZONE=Europe/London
```

**Notes:**

- If both `TZ` and `TIMEZONE` are set, `TZ` takes precedence
- Use the same format as `TZ`

### Path Configuration

#### `BASE_PATH` (string)

**Description:** Root directory for all stack data (config and media).

**Default:** None (must be set in wizard or environment)

**Example:**

```bash
BASE_PATH=/mnt/storage
```

**Notes:**

- **Required** when using `Configuration.from_env()`
- Must be an absolute path
- Directory must exist and be writable
- All other paths are derived from this if not explicitly set

#### `CONFIG_PATH` (string)

**Description:** Directory for service configurations.

**Default:** `{BASE_PATH}/config`

**Example:**

```bash
CONFIG_PATH=/mnt/storage/config
```

**Notes:**

- Overrides the default derived from `BASE_PATH`
- Must be an absolute path
- Directory will be created if it doesn't exist

#### `DATA_PATH` (string)

**Description:** Directory for media and downloads.

**Default:** `{BASE_PATH}/data`

**Example:**

```bash
DATA_PATH=/mnt/storage/data
```

**Notes:**

- Overrides the default derived from `BASE_PATH`
- Must be an absolute path
- Should support hardlinks for optimal performance

### Docker Compose Configuration

#### `COMPOSE_FILE_PATH` (string)

**Description:** Location to save generated `docker-compose.yml` file.

**Default:** `./stacks/{STACK_NAME}/docker-compose.yml`

**Example:**

```bash
COMPOSE_FILE_PATH=/opt/arr-stack/docker-compose.yml
```

**Notes:**

- Must be an absolute path
- Parent directory must exist or be creatable

#### `STACK_NAME` (string)

**Description:** Name for this stack configuration.

**Default:** `default`

**Example:**

```bash
STACK_NAME=media-automation
```

**Notes:**

- Used for organizing multiple stack configurations
- Alphanumeric characters and hyphens recommended

## Using .env Files

### File Locations

The \*arr Stack Manager searches for `.env` files in the following locations (in priority order):

1. **User config directory** (lowest priority)

   - `~/.config/arr-stack-manager/.env`
   - Good for user-wide defaults

2. **Project root** (medium priority)

   - Where `pyproject.toml` is located
   - Good for development settings

3. **Current working directory** (highest priority)
   - `./env`
   - Good for deployment-specific settings

### Priority Order

When the same variable is defined in multiple locations:

1. **System environment variables** (highest priority)

   - Set with `export VAR=value`
   - Takes precedence over all `.env` files

2. **Current directory `.env`**

   - Overrides project root and user config

3. **Project root `.env`**

   - Overrides user config

4. **User config `.env`** (lowest priority)

   - Provides defaults for all stacks

5. **Saved configuration**
   - Used if no environment variable is set

### Creating a .env File

1. Generate an example file:

   ```bash
   arr-stack-manager --generate-env-example
   ```

2. Copy the example to `.env`:

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your values:
   ```bash
   nano .env
   ```

### Example .env File

```bash
# arr Stack Manager Environment Configuration

# User and Group IDs
PUID=1000
PGID=1000

# Timezone
TZ=America/New_York

# Base Path
BASE_PATH=/mnt/storage

# Optional: Override derived paths
# CONFIG_PATH=/mnt/storage/config
# DATA_PATH=/mnt/storage/data

# Stack Configuration
STACK_NAME=media-automation

# Optional: Custom compose file location
# COMPOSE_FILE_PATH=/opt/arr-stack/docker-compose.yml
```

## Integration with Configuration Wizard

### Pre-filling Wizard Values

When environment variables are set, the configuration wizard will:

1. **Pre-fill form fields** with environment values
2. **Show an indicator** that values come from environment
3. **Allow overrides** - you can still change values in the wizard
4. **Validate** environment values before using them

### Example Workflow

```bash
# Set environment variables
export PUID=1000
export PGID=1000
export TZ=America/New_York
export BASE_PATH=/mnt/storage

# Launch the application
arr-stack-manager

# The wizard will show:
# PUID: [1000] (from environment)
# PGID: [1000] (from environment)
# Timezone: [America/New_York] (from environment)
# Base Path: [/mnt/storage] (from environment)
```

## Validation

All environment variables are validated before use:

### PUID/PGID Validation

- Must be valid integers ≥ 0
- Checked against system user/group database
- Warning if user/group doesn't exist

### Timezone Validation

- Must be a valid TZ database timezone
- Validated against system timezone data
- Falls back to UTC if invalid

### Path Validation

- Must be absolute paths
- Checked for existence
- Checked for write permissions
- Parent directories must exist

### Port Validation

- Must be integers between 1 and 65535
- Checked for conflicts with other services
- Checked if already in use on the system

## Security Considerations

### .env File Security

⚠️ **Important Security Notes:**

1. **Never commit `.env` files to version control**

   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Set appropriate file permissions**

   ```bash
   chmod 600 .env
   ```

3. **Don't share `.env` files**

   - They may contain sensitive paths or configuration
   - Use `.env.example` for sharing templates

4. **Use different `.env` files for different environments**
   - Development: `.env.dev`
   - Production: `.env.prod`
   - Load with: `cp .env.prod .env`

### Environment Variable Security

1. **Avoid sensitive data in environment variables**

   - Don't store passwords or API keys
   - Use Docker secrets for sensitive data

2. **Be careful with shell history**

   ```bash
   # Avoid:
   export API_KEY=secret123

   # Better: Use .env file
   echo "API_KEY=secret123" >> .env
   ```

3. **Limit access to environment**
   - Only trusted users should access the system
   - Use proper user permissions

## Troubleshooting

### Environment Variables Not Loading

**Problem:** Environment variables are not being recognized.

**Solutions:**

1. **Check variable names**

   ```bash
   # Correct
   export PUID=1000

   # Incorrect (wrong name)
   export PUID_VALUE=1000
   ```

2. **Verify .env file location**

   ```bash
   # Check current directory
   ls -la .env

   # Check user config
   ls -la ~/.config/arr-stack-manager/.env
   ```

3. **Check .env file syntax**

   ```bash
   # Correct
   PUID=1000

   # Incorrect (spaces around =)
   PUID = 1000
   ```

4. **Verify file is being loaded**
   ```bash
   # Enable verbose logging
   arr-stack-manager --verbose
   ```

### Type Conversion Errors

**Problem:** Environment variable has wrong type.

**Solutions:**

1. **Check integer values**

   ```bash
   # Correct
   PUID=1000

   # Incorrect (not a number)
   PUID=user1000
   ```

2. **Check boolean values** (if applicable)

   ```bash
   # Correct
   ENABLED=true
   ENABLED=false

   # Incorrect
   ENABLED=yes  # Use 'true' instead
   ```

### Path Permission Errors

**Problem:** Cannot write to configured paths.

**Solutions:**

1. **Check path ownership**

   ```bash
   ls -ld /mnt/storage
   # Should show your user as owner
   ```

2. **Fix ownership**

   ```bash
   sudo chown -R $USER:$USER /mnt/storage
   ```

3. **Check permissions**
   ```bash
   # Ensure write permission
   chmod u+w /mnt/storage
   ```

### Timezone Not Recognized

**Problem:** Invalid timezone value.

**Solutions:**

1. **Use correct TZ database format**

   ```bash
   # Correct
   TZ=America/New_York

   # Incorrect
   TZ=EST
   TZ=Eastern
   ```

2. **List available timezones**

   ```bash
   timedatectl list-timezones
   ```

3. **Use system timezone**
   ```bash
   # Get current timezone
   timedatectl show --property=Timezone --value
   ```

### Priority Confusion

**Problem:** Wrong value is being used.

**Solutions:**

1. **Check priority order**

   - System environment > Current dir .env > Project .env > User config .env

2. **Verify system environment**

   ```bash
   # Check if set in system
   echo $PUID

   # Unset if needed
   unset PUID
   ```

3. **Check all .env locations**

   ```bash
   # Current directory
   cat .env

   # User config
   cat ~/.config/arr-stack-manager/.env
   ```

4. **Use verbose logging**
   ```bash
   arr-stack-manager --verbose
   # Will show which values are loaded from where
   ```

### Configuration Not Persisting

**Problem:** Changes in wizard don't save.

**Solutions:**

1. **Environment variables override saved config**

   - If `PUID` is set in environment, it always overrides saved value
   - Unset environment variable to use saved config:
     ```bash
     unset PUID
     ```

2. **Check config file location**

   ```bash
   ls -la ~/.config/arr-stack-manager/config.json
   ```

3. **Verify write permissions**
   ```bash
   ls -ld ~/.config/arr-stack-manager/
   ```

## Advanced Usage

### Multiple Environments

Manage different configurations for different environments:

```bash
# Development
cp .env.dev .env
arr-stack-manager --stack-name dev

# Production
cp .env.prod .env
arr-stack-manager --stack-name prod
```

### Automated Deployment

Use environment variables for automated deployments:

```bash
#!/bin/bash
# deploy.sh

export PUID=1000
export PGID=1000
export TZ=America/New_York
export BASE_PATH=/mnt/storage
export STACK_NAME=media-automation

# Run deployment
arr-stack-manager --no-wizard --deploy
```

### Docker Compose Integration

Use environment variables in your Docker Compose workflow:

```bash
# Load environment
source .env

# Generate compose file
arr-stack-manager --generate-only

# Deploy with docker-compose
docker-compose -f stacks/$STACK_NAME/docker-compose.yml up -d
```

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Deploy Stack

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up environment
        run: |
          echo "PUID=1000" >> .env
          echo "PGID=1000" >> .env
          echo "TZ=America/New_York" >> .env
          echo "BASE_PATH=/mnt/storage" >> .env

      - name: Deploy stack
        run: |
          arr-stack-manager --deploy
```

## Best Practices

1. **Use .env files for local development**

   - Keep sensitive values out of version control
   - Easy to switch between configurations

2. **Use system environment for production**

   - More secure than files
   - Better integration with orchestration tools

3. **Document your environment variables**

   - Keep .env.example up to date
   - Add comments explaining each variable

4. **Validate before deployment**

   - Test configuration in development first
   - Use `--validate-only` flag to check config

5. **Use consistent naming**

   - Follow the established variable names
   - Don't create custom variables that won't be recognized

6. **Keep .env files simple**

   - Only set variables you need to override
   - Let defaults handle the rest

7. **Regular backups**
   - Back up your .env files
   - Store securely (encrypted if possible)

## Reference

### Complete Variable List

| Variable            | Type    | Default              | Required | Description                     |
| ------------------- | ------- | -------------------- | -------- | ------------------------------- |
| `PUID`              | integer | Current UID          | No       | User ID for containers          |
| `PGID`              | integer | Current GID          | No       | Group ID for containers         |
| `TZ`                | string  | UTC                  | No       | Timezone (TZ database format)   |
| `TIMEZONE`          | string  | UTC                  | No       | Alternative timezone variable   |
| `BASE_PATH`         | string  | None                 | Yes\*    | Root directory for stack data   |
| `CONFIG_PATH`       | string  | `{BASE_PATH}/config` | No       | Service configuration directory |
| `DATA_PATH`         | string  | `{BASE_PATH}/data`   | No       | Media and downloads directory   |
| `COMPOSE_FILE_PATH` | string  | Auto-generated       | No       | Docker Compose file location    |
| `STACK_NAME`        | string  | default              | No       | Stack configuration name        |

\* Required when using `Configuration.from_env()`, optional when using wizard

### Related Documentation

- [Main README](../README.md) - Project overview and quick start
- [Config Wizard Fixes](./CONFIG_WIZARD_FIXES.md) - Configuration wizard documentation
- [Docker Permission Fix](./DOCKER_PERMISSION_FIX.md) - Docker setup and permissions
- [Environment Variables Quick Reference](./ENV_QUICK_REFERENCE.md) - Quick reference card

## Getting Help

If you encounter issues with environment configuration:

1. **Check the logs**

   ```bash
   arr-stack-manager --verbose --log-file debug.log
   ```

2. **Validate your configuration**

   ```bash
   arr-stack-manager --validate-only
   ```

3. **Review this guide**

   - Check the troubleshooting section
   - Verify variable names and types

4. **Ask for help**
   - GitHub Issues: [Report a bug](https://github.com/yourusername/arr-stack-manager/issues)
   - Discussions: [Ask a question](https://github.com/yourusername/arr-stack-manager/discussions)
