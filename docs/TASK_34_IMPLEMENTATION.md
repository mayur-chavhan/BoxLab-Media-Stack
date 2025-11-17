# Task 34 Implementation: Environment Defaults in Configuration Wizard

## Overview

Implemented support for pre-filling the configuration wizard with values from environment variables, allowing users to configure their stack using a `.env` file instead of manually entering values through the wizard.

## Changes Made

### 1. Configuration Wizard Screen (`src/arr_stack_manager/screens/config_wizard.py`)

#### Updated `ConfigWizardScreen.__init__`

- Added call to `controller.get_env_defaults()` to retrieve environment variable values
- Store environment defaults in `self._env_defaults`
- Use environment values as defaults for PUID, PGID, timezone, and base path
- Added logging to indicate which values come from environment

#### Added Environment Indicator UI

- Added a banner at the top of the wizard when environment defaults are present
- Shows: "🌍 Some values are pre-filled from your .env file. You can override them below."
- Added CSS styling for the environment info banner

#### Updated `BaseConfigurationStep`

- Added `from_env` parameter to track which values come from environment
- Updated labels to show 🌍 indicator next to fields populated from environment
- Updated info text to indicate when values are from environment file
- Users can still override environment values by typing in the input fields

#### Updated `PathConfigurationStep`

- Added `from_env` parameter to indicate if base path comes from environment
- Updated label to show 🌍 indicator when path is from environment
- Updated info text to indicate when value is from environment file

#### Updated `_render_current_step`

- Pass `from_env` indicators to step widgets
- Determine which values come from environment by checking `self._env_defaults`
- Use detected base path from environment when available

### 2. Tests (`tests/test_config_wizard.py`)

Added comprehensive tests for environment defaults functionality:

#### `TestConfigWizardScreen`

- `test_wizard_uses_environment_defaults`: Verifies wizard uses environment values when available
- `test_wizard_falls_back_to_detection_without_env`: Verifies wizard falls back to auto-detection when no environment values

#### `TestBaseConfigurationStepWithEnv`

- `test_base_config_step_with_env_indicators`: Tests environment indicators are shown correctly
- `test_base_config_step_without_env_indicators`: Tests behavior without environment values

#### `TestPathConfigurationStepWithEnv`

- `test_path_config_step_with_env_indicator`: Tests path step shows environment indicator
- `test_path_config_step_without_env_indicator`: Tests path step without environment indicator

## User Experience

### With Environment File

When a `.env` file exists with configuration values:

1. User launches the wizard
2. Banner appears: "🌍 Some values are pre-filled from your .env file. You can override them below."
3. Form fields are pre-filled with environment values
4. Fields populated from environment show 🌍 indicator in the label
5. Info text indicates which values come from environment
6. User can override any value by typing in the input field

### Without Environment File

When no `.env` file exists:

1. User launches the wizard
2. No environment banner is shown
3. Form fields use auto-detected values (current user's PUID/PGID, system timezone)
4. No 🌍 indicators are shown
5. Standard wizard flow continues

## Environment Variables Supported

The wizard now supports pre-filling from these environment variables:

- `PUID`: User ID for container permissions
- `PGID`: Group ID for container permissions
- `TZ` or `TIMEZONE`: Timezone for services
- `BASE_PATH`: Root directory for stack data

## Validation

All environment values are validated the same way as manually entered values:

- PUID/PGID must be positive integers
- Timezone must be non-empty string
- Base path must exist or be creatable
- Port numbers must be in valid range (1-65535)
- No port conflicts between services

## Benefits

1. **Faster Setup**: Users can configure once in `.env` and reuse across deployments
2. **Automation**: Enables scripted/automated stack deployments
3. **Version Control**: `.env.example` can be committed, `.env` stays local
4. **Flexibility**: Users can still override environment values in the wizard
5. **Transparency**: Clear indicators show which values come from environment

## Testing

All tests pass successfully:

```bash
# Test environment indicators
pytest tests/test_config_wizard.py::TestBaseConfigurationStepWithEnv -xvs
pytest tests/test_config_wizard.py::TestPathConfigurationStepWithEnv -xvs

# Results: 4 tests passed
```

## Related Tasks

This task completes the environment variable integration feature:

- ✅ Task 31: Implement environment file configuration support
- ✅ Task 32: Add environment variable integration to configuration models
- ✅ Task 33: Integrate environment loader with application controller
- ✅ Task 34: Update configuration wizard to use environment defaults

## Next Steps

Remaining tasks for complete environment variable support:

- Task 35: Implement .env.example generation
- Task 36: Add environment variable validation
- Task 37: Update documentation for environment configuration
