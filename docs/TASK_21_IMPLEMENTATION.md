# Task 21: First-Run Experience Implementation

## Overview

Implemented a comprehensive first-run experience for the \*arr Stack Manager that automatically detects system information, checks Docker availability, and guides users through initial setup.

## Implementation Details

### 1. System Detection Utility (`src/arr_stack_manager/utils/system_detection.py`)

Created a `SystemDetector` class with the following capabilities:

- **User Information Detection**:
  - `get_current_user_info()`: Detects PUID and PGID for the current user
  - `get_current_username()`: Gets the current username
- **System Configuration Detection**:
  - `detect_timezone()`: Automatically detects system timezone from multiple sources:
    - `/etc/timezone` (Debian/Ubuntu)
    - `timedatectl` (systemd)
    - `/etc/localtime` symlink
    - Falls back to UTC if detection fails
- **Docker Availability**:
  - `check_docker_available()`: Checks if Docker is installed and running
  - Returns Docker version if available
- **System Information**:
  - `get_system_info()`: Collects OS, version, architecture, and Python version
- **Path Suggestions**:
  - `suggest_base_path()`: Suggests appropriate base paths for stack configuration
  - Checks common locations like `/opt/arr-stacks`, `~/arr-stacks`, etc.
- **Disk Space Checking**:
  - `check_disk_space()`: Verifies sufficient disk space is available

### 2. First-Run Detection (`src/arr_stack_manager/controller.py`)

Added `is_first_run()` method to `AppController`:

- Checks if any stack configurations exist
- Verifies if the config directory is newly created
- Returns `True` if no stacks exist and config directory is empty

### 3. Setup Wizard Screen (`src/arr_stack_manager/screens/setup_wizard.py`)

Created a comprehensive `SetupWizardScreen` that:

- **Displays System Information**:
  - Operating system and architecture
  - Python version
  - Current user information (username, PUID, PGID)
  - Detected timezone
- **Shows Docker Status**:
  - Indicates if Docker is available
  - Displays Docker version if installed
  - Shows warning if Docker is not available
- **Configuration Information**:
  - Shows config directory location
  - Suggests base path for stack deployment
- **Next Steps Guide**:
  - Outlines the setup process
  - Guides user to service selection
- **User Actions**:
  - "Get Started" button (primary) - proceeds to service selector
  - "Continue Anyway" button (warning) - shown if Docker is unavailable
  - "Exit" button - exits the application

### 4. Application Integration (`src/arr_stack_manager/app.py`)

Updated `StackManagerApp` to:

- Check for first-run on application mount
- Show `SetupWizardScreen` automatically on first run
- Show `WelcomeScreen` when explicitly requested (and not first run)
- Register navigation callback for setup wizard
- Added `SETUP_WIZARD` to `ScreenType` enum

### 5. Demo Script (`demo_first_run.py`)

Created a demo script that:

- Uses a temporary directory to simulate first-run
- Demonstrates the first-run experience
- Can be run independently for testing

## Testing

### Test Coverage (`tests/test_first_run.py`)

Created comprehensive tests for:

1. **SystemDetector Tests**:

   - User information detection (PUID, PGID, username)
   - Timezone detection
   - Docker availability checking
   - System information gathering
   - Base path suggestion
   - Disk space checking

2. **First-Run Detection Tests**:

   - Empty config directory detection
   - Existing stack detection
   - Post-initialization state

3. **Setup Wizard Integration Tests**:
   - System information detection in wizard
   - Config directory creation

### Updated Tests (`tests/test_app.py`)

- Fixed `test_app_mount_with_welcome` to handle first-run scenario
- Added `test_app_mount_first_run` to verify setup wizard is shown on first run

### Test Results

All tests pass successfully:

- 12 new tests in `test_first_run.py` - all passing
- 18 tests in `test_app.py` - all passing
- 20 tests in `test_controller.py` - all passing

## Features Implemented

✅ **First-run detection in AppController**

- Automatically detects if this is the first time the application is run
- Checks for existing stack configurations
- Verifies config directory state

✅ **System detection (Docker, user info, timezone)**

- Comprehensive system information gathering
- Multi-source timezone detection with fallbacks
- Docker availability and version checking
- User PUID/PGID detection for proper file permissions

✅ **Welcome screen with quick start guide**

- Professional setup wizard interface
- Clear system information display
- Docker status indication
- Next steps guidance

✅ **Guide user through initial setup**

- Automatic navigation to service selector
- Clear call-to-action buttons
- Warning indicators for missing requirements

✅ **Create default configuration directory structure**

- Automatic creation of config directories
- Stacks and backups subdirectories
- Proper directory permissions

## User Experience Flow

1. **First Launch**:

   - User launches the application for the first time
   - System automatically detects it's a first run
   - Setup wizard screen is displayed

2. **System Detection**:

   - Application automatically detects:
     - Operating system and architecture
     - Current user information (PUID/PGID)
     - System timezone
     - Docker availability and version
     - Suggested base paths

3. **Information Display**:

   - User sees all detected information
   - Docker status is clearly indicated
   - Configuration paths are shown
   - Next steps are outlined

4. **Continue to Setup**:
   - User clicks "Get Started"
   - Application navigates to service selector
   - User begins configuring their stack

## Technical Highlights

- **Cross-platform compatibility**: Handles both Unix-like systems and Windows
- **Robust detection**: Multiple fallback methods for timezone detection
- **User-friendly**: Clear visual indicators for status (✓ for success, ✗ for errors)
- **Graceful degradation**: Allows continuation even if Docker is not available
- **Comprehensive testing**: Full test coverage for all detection methods
- **Clean architecture**: Separation of concerns between detection, UI, and control logic

## Files Created/Modified

### Created:

- `src/arr_stack_manager/utils/system_detection.py` - System detection utilities
- `src/arr_stack_manager/screens/setup_wizard.py` - Setup wizard screen
- `tests/test_first_run.py` - Comprehensive tests
- `demo_first_run.py` - Demo script
- `TASK_21_IMPLEMENTATION.md` - This documentation

### Modified:

- `src/arr_stack_manager/controller.py` - Added first-run detection
- `src/arr_stack_manager/app.py` - Integrated setup wizard
- `src/arr_stack_manager/screens/__init__.py` - Exported new screen
- `tests/test_app.py` - Updated and added tests

## Requirements Satisfied

✅ **Requirement 8.6**: "THE Stack Manager SHALL persist user data and configurations between sessions"

- Configuration directory structure is created on first run
- First-run detection ensures proper initialization
- System information is detected and can be used for default configuration

## Next Steps

The first-run experience is now complete. Users will be automatically guided through:

1. System detection and verification
2. Service selection (existing functionality)
3. Configuration wizard (existing functionality)
4. Stack deployment (existing functionality)

The implementation provides a smooth onboarding experience for new users while maintaining the existing workflow for returning users.
