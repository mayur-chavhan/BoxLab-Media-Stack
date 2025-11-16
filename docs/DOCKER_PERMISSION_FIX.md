# Docker Permission Fix

## Problem

Users without Docker permissions get a crash with:

```
PermissionError: [Errno 13] Permission denied
Cannot connect to Docker daemon
```

## Solution

Added comprehensive Docker prerequisite checking that:

✅ Checks if Docker is installed
✅ Checks if Docker daemon is running  
✅ Checks if user has permission to access Docker
✅ Supports root users, sudo users, and regular users
✅ Provides clear error messages with remediation steps

## How It Works

### Before Starting the App

The app now checks Docker prerequisites and shows helpful messages:

```
======================================================================
Docker Prerequisites Check
======================================================================

✓ Docker Installed: Yes
✓ Docker Running: Yes
✓ Has Permission: No
  - Running as root: No
  - In docker group: No

❌ Error: Permission denied accessing Docker socket

How to fix:
  Add your user to the docker group:
    sudo usermod -aG docker dietpi
  Then log out and log back in for changes to take effect

  OR run this application with sudo:
    sudo python -m arr_stack_manager

  OR fix socket permissions (temporary):
    sudo chmod 666 /var/run/docker.sock

======================================================================
```

### Solutions Provided

**Option 1: Add User to Docker Group (Recommended)**

```bash
sudo usermod -aG docker $USER
# Log out and log back in
```

**Option 2: Run with Sudo**

```bash
sudo python -m arr_stack_manager
```

**Option 3: Fix Socket Permissions (Temporary)**

```bash
sudo chmod 666 /var/run/docker.sock
```

## Files Created/Modified

- **src/arr_stack_manager/utils/docker_check.py** - New Docker prerequisite checker
- **src/arr_stack_manager/**main**.py** - Added prerequisite check before app starts

## Features

### Comprehensive Checks

- ✅ Docker installation
- ✅ Docker daemon status
- ✅ User permissions
- ✅ Root user detection
- ✅ Docker group membership

### Clear Error Messages

- Shows exactly what's wrong
- Provides step-by-step remediation
- Supports multiple fix options
- Works for all user types

### Safe & Helpful

- Checks prerequisites before crashing
- Exits gracefully with helpful info
- No confusing stack traces for permission issues
- Clear instructions for each scenario

## Testing

Run the app without Docker permissions:

```bash
python -m arr_stack_manager
```

You'll see a clear message explaining the issue and how to fix it, instead of a crash.

After fixing permissions, the app will start normally.
