# Task 15 Implementation Summary

## Task: Implement Configuration Wizard screen - Path configuration

### Requirements Addressed

- **3.4**: Prompt for base paths for config and data directories
- **3.5**: Validate each configuration input before allowing progression
- **3.6**: Display error message with correction guidance for invalid input
- **7.2**: Verify that all required paths exist and are accessible

### Implementation Details

#### 1. Added Step 3 to Wizard

- Updated `WizardStep` enum to include `PATH_CONFIGURATION = 3`
- Updated total steps from 2 to 3
- Added step title: "Directory Structure Configuration"

#### 2. Created PathConfigurationStep Widget

A new widget class with the following features:

**Base Path Input:**

- Input field for base path with placeholder `/mnt/storage`
- Browse button (placeholder for future file browser implementation)
- Auto-detection of sensible default paths (checks `/mnt/storage`, `/data`, `/media`, `~/arr-stack`)

**Directory Structure Preview:**

- Visual tree representation showing the generated directory structure:
  ```
  /base/path/
  ├── config/          (Application configurations)
  │   ├── sonarr/
  │   ├── radarr/
  │   ├── prowlarr/
  │   └── ...
  └── data/            (Media and downloads)
      ├── media/       (Final media location)
      │   ├── tv/
      │   └── movies/
      └── downloads/   (Download client output)
  ```
- Updates dynamically as user types in the base path input

**Path Validation:**

- Integrates with `ConfigurationValidator` to validate paths
- Checks:
  - Path existence
  - Read permissions
  - Write permissions
  - Whether path is a directory
- Provides warnings for paths that will be created

**Validation Status Display:**

- Shows checkmarks (✓) for successful validations
- Shows errors (✗) with red color for validation failures
- Shows warnings (⚠) with yellow color for non-critical issues
- Displays informational messages about directory creation

#### 3. Updated Wizard Navigation

- Modified `_render_current_step()` to render PathConfigurationStep
- Updated `_validate_current_step()` to validate path configuration:
  - Ensures base path is not empty
  - Runs full path validation
  - Shows first error if validation fails
- Updated `_save_current_step_data()` to save path configuration:
  - Creates `PathConfig` object from base path
  - Automatically derives config_path and data_path
  - Saves to configuration object
- Updated `_go_to_next_step()` to recognize PATH_CONFIGURATION as the last step

#### 4. Real-time Validation

- Added input change handler for base path input
- Updates directory tree preview as user types
- Validates path and updates status display in real-time
- Clears validation errors when user starts typing

#### 5. CSS Styling

Complete styling for the path configuration step including:

- Section containers with borders
- Form layout with labels and inputs
- Tree view with proper indentation
- Color-coded validation status (success/error/warning)
- Responsive layout

#### 6. Updated Tests

Added comprehensive tests in `tests/test_config_wizard.py`:

- `TestPathConfigurationStep` class with tests for:
  - Initialization with custom base path
  - Default path detection
  - Getting form values
  - Validating existing paths
  - Validating non-existent paths
  - Updating directory tree preview
- Updated existing tests to reflect 3 total steps
- Added PATH_CONFIGURATION to step title tests

### Files Modified

1. `src/arr_stack_manager/screens/config_wizard.py`

   - Added `PathConfigurationStep` class (~250 lines)
   - Updated `WizardStep` enum
   - Updated wizard navigation logic
   - Added event handlers for path input

2. `tests/test_config_wizard.py`
   - Added `TestPathConfigurationStep` test class
   - Updated existing tests for 3-step wizard
   - Added import for `PathConfigurationStep`

### Key Features Implemented

✅ Base path input with file browser button
✅ Directory structure visualization
✅ Real-time path validation
✅ Validation status display with checkmarks/errors
✅ Integration with ConfigurationValidator
✅ Auto-detection of sensible default paths
✅ Dynamic directory tree preview
✅ Proper error handling and user feedback
✅ Comprehensive test coverage

### User Experience

1. User navigates from Step 2 (Base Configuration) to Step 3
2. Sees default base path pre-filled (auto-detected)
3. Can modify the base path in the input field
4. Directory tree preview updates in real-time
5. Validation runs automatically and shows status
6. Clear visual feedback with checkmarks for success, X for errors
7. Cannot proceed if validation fails
8. Path configuration is saved to Configuration object when continuing

### Technical Notes

- Uses Pydantic's `PathConfig` model for data validation
- Integrates with existing `ConfigurationValidator` for path checks
- Follows Textual framework patterns for reactive UI
- Maintains consistency with existing wizard steps
- Properly handles edge cases (empty paths, non-existent directories, permission issues)

### Next Steps

The wizard now has 3 complete steps:

1. Service Selection Confirmation
2. Base Configuration (PUID, PGID, Timezone)
3. Path Configuration (Directory Structure) ✅ NEW

Task 16 will add Step 4 for service-specific settings (ports, custom volumes).
