# Automatic Sudo Support

## Feature

The app now automatically offers to restart with `sudo` when Docker permission issues are detected.

## How It Works

### 1. Permission Check

When you start the app without Docker permissions:

```
======================================================================
Docker Prerequisites Check
======================================================================

✓ Docker Installed: Yes
✓ Docker Running: Yes
✓ Has Permission: No

❌ Error: Permission denied accessing Docker socket

How to fix:
  Add your user to the docker group:
    sudo usermod -aG docker dietpi
  Then log out and log back in

  OR run with sudo:
    sudo python -m arr_stack_manager
======================================================================

======================================================================
QUICK FIX: Restart with sudo
======================================================================

Would you like to restart this application with sudo?
This will give the app temporary access to Docker.

Options:
  [Y] Yes - Restart with sudo now
  [N] No  - Exit and fix permissions manually
======================================================================

Your choice [Y/n]:
```

### 2. Automatic Restart

If you choose **Yes**:

- App automatically restarts with `sudo`
- You'll be prompted for your password (if needed)
- App runs with Docker access
- No manual commands needed!

If you choose **No**:

- App exits gracefully
- Shows manual fix instructions
- You can fix permissions and restart

## Usage Examples

### Scenario 1: Quick Start (Recommended)

```bash
# Run normally
python -m arr_stack_manager

# When prompted, press Y
# Enter your password
# App restarts with sudo automatically!
```

### Scenario 2: Manual Sudo

```bash
# Run with sudo from the start
sudo python -m arr_stack_manager
```

### Scenario 3: Fix Permissions Permanently

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in
# Then run normally
python -m arr_stack_manager
```

## Benefits

✅ **No manual sudo needed** - App offers to restart automatically
✅ **User-friendly** - Simple Y/N prompt
✅ **Safe** - Only restarts if user confirms
✅ **Flexible** - Works for all user types
✅ **Clear** - Shows exactly what will happen

## Technical Details

### How Restart Works

1. **Detect Permission Issue**

   ```python
   if not docker_check.has_permission and not docker_check.is_root:
       if offer_sudo_restart():
           sys.exit(0)
   ```

2. **Prompt User**

   - Shows clear explanation
   - Offers Y/N choice
   - Handles Ctrl+C gracefully

3. **Execute Restart**

   ```python
   sudo_cmd = ["sudo"] + sys.argv
   os.execvp("sudo", sudo_cmd)
   ```

4. **Seamless Transition**
   - Same command-line arguments preserved
   - Same configuration used
   - User just enters password

### Security Considerations

- ✅ User must explicitly confirm
- ✅ System prompts for password
- ✅ Only runs with user's permission
- ✅ No password stored or cached
- ✅ Standard sudo security applies

## Supported Platforms

- ✅ Linux (all distributions)
- ✅ macOS
- ✅ Any Unix-like system with sudo

## Fallback Options

If automatic restart doesn't work:

1. **Manual sudo**: `sudo python -m arr_stack_manager`
2. **Add to docker group**: `sudo usermod -aG docker $USER`
3. **Fix socket permissions**: `sudo chmod 666 /var/run/docker.sock`

## Files Modified

- **src/arr_stack_manager/**main**.py** - Added sudo restart offer
- **src/arr_stack_manager/utils/docker_check.py** - Added `offer_sudo_restart()` function

## Example Session

```bash
$ python -m arr_stack_manager
2024-11-16 13:00:00 - INFO - Starting arr Stack Manager v0.1.0

======================================================================
Docker Prerequisites Check
======================================================================

✓ Docker Installed: Yes
✓ Docker Running: Yes
✓ Has Permission: No

❌ Error: Permission denied accessing Docker socket
[... remediation steps ...]

======================================================================
QUICK FIX: Restart with sudo
======================================================================

Would you like to restart this application with sudo?
This will give the app temporary access to Docker.

Options:
  [Y] Yes - Restart with sudo now
  [N] No  - Exit and fix permissions manually
======================================================================

Your choice [Y/n]: y

Restarting with sudo...
You may be prompted for your password.

[sudo] password for dietpi:
2024-11-16 13:00:05 - INFO - Starting arr Stack Manager v0.1.0
2024-11-16 13:00:05 - INFO - Docker prerequisites check passed
2024-11-16 13:00:05 - WARNING - Running as root user

[App starts successfully]
```

## Best Practices

### For Quick Testing

Use the automatic sudo restart - fastest way to get started.

### For Development

Add your user to the docker group for permanent access.

### For Production

Run as a service with proper Docker permissions configured.

## Troubleshooting

### "sudo: command not found"

Install sudo: `apt-get install sudo` (as root)

### "User is not in the sudoers file"

Add user to sudoers: `usermod -aG sudo username` (as root)

### Restart doesn't work

Fall back to manual: `sudo python -m arr_stack_manager`

## Summary

The app now intelligently handles Docker permission issues by:

1. Detecting the problem early
2. Offering an automatic fix
3. Restarting with sudo if user agrees
4. Providing fallback options if needed

No more manual sudo commands or confusing error messages!
