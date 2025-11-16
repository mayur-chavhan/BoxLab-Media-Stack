# Task 23: Update Management Implementation

## Overview

Implemented comprehensive update management functionality for the \*arr Stack Manager, allowing users to check for and apply updates to their services while preserving data volumes.

## Changes Made

### 1. DockerManager (`src/arr_stack_manager/core/docker_manager.py`)

#### New Method: `check_for_updates()`

- Checks if a newer image version is available for a service
- Pulls the latest image and compares image IDs
- Returns `True` if an update is available, `False` otherwise
- Handles errors gracefully without disrupting service

#### Enhanced Method: `get_service_status()`

- Added optional `check_updates` parameter (default: `False`)
- When enabled, checks for available updates during status query
- Returns update availability in `ServiceInfo` object

#### Enhanced Method: `update_service()`

- Added explicit comment about volume preservation
- Uses `v=False` when removing containers to preserve volumes
- Ensures data safety during updates

### 2. ServiceInfo Model (`src/arr_stack_manager/models/service.py`)

#### New Field: `update_available`

- Boolean field indicating if an update is available
- Defaults to `False`
- Displayed in UI when `True`

### 3. AppController (`src/arr_stack_manager/controller.py`)

#### New Methods:

- `check_service_updates(service_name)` - Check if update available for a service
- `update_service(service_name)` - Update a single service
- `update_all_services()` - Update all services in current stack
- `start_service(service_name)` - Start a service container
- `stop_service(service_name)` - Stop a service container
- `restart_service(service_name)` - Restart a service container

### 4. Dashboard Screen (`src/arr_stack_manager/screens/dashboard.py`)

#### Enhanced Refresh Functionality:

- `_refresh_status()` now accepts `check_updates` parameter
- Manual refresh checks for updates automatically
- Update availability shown in service cards

#### Implemented Button Handlers:

- **Start All** - Starts all services in the stack
- **Stop All** - Stops all services in the stack
- **Restart All** - Restarts all services in the stack
- **Update All** - Updates all services to latest images
- All handlers log results to activity log
- All handlers refresh status after completion

### 5. ServiceCard Component (`src/arr_stack_manager/components/service_card.py`)

#### Update Indicator:

- Shows "🔄 Update" badge when update is available
- Displays "New version available" in service details
- Visual indicator in header for quick identification

### 6. Tests

#### New Docker Manager Tests (`tests/test_docker_manager.py`):

- `test_check_for_updates_nonexistent()` - Test update check on nonexistent service
- `test_get_service_status_with_update_check()` - Test status with update checking
- `test_get_service_status_without_update_check()` - Test status without update checking

#### New Controller Tests (`tests/test_controller.py`):

- `test_check_service_updates()` - Test checking for updates
- `test_update_service()` - Test updating single service
- `test_update_all_services()` - Test updating all services
- `test_update_all_services_no_stack()` - Test update all without stack
- `test_start_service()` - Test starting a service
- `test_stop_service()` - Test stopping a service
- `test_restart_service()` - Test restarting a service

## Features Implemented

### ✅ Check for Image Updates

- Non-intrusive update checking
- Compares current and latest image IDs
- Handles network and API errors gracefully

### ✅ Pull and Recreate Workflow

- Pulls latest image
- Stops and removes old container
- Recreates with same configuration
- Starts new container

### ✅ Show Update Availability in Dashboard

- Visual indicator in service cards
- Update badge in header
- Detail row showing update availability
- Manual refresh checks for updates

### ✅ Update All Functionality

- Updates all services in current stack
- Reports success/failure for each service
- Logs results to activity log
- Refreshes status after completion

### ✅ Preserve Data Volumes

- Explicitly uses `v=False` when removing containers
- Volumes remain intact during updates
- Configuration and data preserved
- Safe update process

## Usage

### Check for Updates

```python
# Via controller
has_update = controller.check_service_updates("sonarr")

# Via docker manager
has_update = docker_manager.check_for_updates("sonarr")
```

### Update Single Service

```python
result = controller.update_service("sonarr")
if result.success:
    print("Service updated successfully")
```

### Update All Services

```python
results = controller.update_all_services()
for service, result in results.items():
    print(f"{service}: {result.message}")
```

### Dashboard Actions

- Click "Refresh" button to check for updates
- Click "Update All" to update all services
- Update indicators appear automatically
- Activity log shows progress

## Testing

All tests pass successfully:

```bash
pytest tests/test_docker_manager.py tests/test_controller.py -v
# 45 passed in 0.44s
```

## Requirements Satisfied

✅ **Requirement 5.6**: Update operations

- Check for image updates
- Pull and recreate workflow
- Show update availability
- Update all functionality
- Preserve data volumes

## Notes

- Update checking is optional to avoid performance impact
- Manual refresh in dashboard checks for updates
- Auto-refresh does not check updates (performance)
- All data volumes are preserved during updates
- Update process is atomic and safe
- Errors are handled gracefully
- Activity log provides user feedback
