# Requirements Document

## Introduction

The *arr Stack Manager is a Textual-based Terminal User Interface (TUI) application designed to simplify the deployment and management of media automation stacks. The system enables users to configure, deploy, and manage Docker-based services (Sonarr, Radarr, Prowlarr, Jellyfin, and other *arr ecosystem applications) through an intuitive menu-driven interface while following Trash-Guides best practices for optimal configuration.

## Glossary

- **Stack Manager**: The TUI application that manages \*arr media automation services
- **Service**: An individual containerized application (e.g., Sonarr, Radarr, Jellyfin)
- **Stack**: A collection of configured services deployed together via Docker Compose
- **Trash-Guides**: Community best practices for \*arr application configuration
- **Hardlinking**: File system feature enabling atomic moves without data duplication
- **Docker Compose**: Tool for defining and running multi-container Docker applications
- **TUI**: Terminal User Interface built with the Textual Python framework
- **Configuration Wizard**: Step-by-step interface for service setup
- **Deployment Monitor**: Real-time status display during Docker operations

## Requirements

### Requirement 1

**User Story:** As a homelab administrator, I want to view the current status of all my \*arr services in a dashboard, so that I can quickly assess the health of my media automation stack

#### Acceptance Criteria

1. WHEN the Stack Manager launches, THE Stack Manager SHALL display a main dashboard screen
2. THE Stack Manager SHALL display the operational status of each configured service on the dashboard
3. THE Stack Manager SHALL provide quick action buttons for common operations on the dashboard
4. WHEN a service status changes, THE Stack Manager SHALL update the dashboard display within 2 seconds
5. THE Stack Manager SHALL display resource usage metrics for each running service on the dashboard

### Requirement 2

**User Story:** As a new user, I want to select which \*arr services I need from a comprehensive list, so that I can build a customized media automation stack

#### Acceptance Criteria

1. THE Stack Manager SHALL provide a service selector interface with multi-select capability
2. THE Stack Manager SHALL include the following services in the selector: Sonarr, Radarr, Prowlarr, Jellyfin, Emby, Jellyseerr, Overseerr, Bazarr, Jackett, Autobrr, Recyclarr, Tdarr, and Unpackerr
3. WHEN a user selects a service, THE Stack Manager SHALL mark the service as selected with a visual indicator
4. WHEN a user deselects a service, THE Stack Manager SHALL remove the selection marker
5. THE Stack Manager SHALL allow users to proceed to configuration only after at least one service is selected

### Requirement 3

**User Story:** As a user configuring my stack, I want a guided wizard to set up paths, users, and ports, so that I can avoid configuration errors

#### Acceptance Criteria

1. WHEN a user completes service selection, THE Stack Manager SHALL launch the configuration wizard
2. THE Stack Manager SHALL prompt for PUID and PGID values in the configuration wizard
3. THE Stack Manager SHALL prompt for timezone configuration in the configuration wizard
4. THE Stack Manager SHALL prompt for base paths for config and data directories in the configuration wizard
5. THE Stack Manager SHALL validate each configuration input before allowing progression to the next step
6. WHEN a user provides invalid input, THE Stack Manager SHALL display an error message with correction guidance
7. THE Stack Manager SHALL allow users to navigate backward to previous configuration steps

### Requirement 4

**User Story:** As a user, I want the system to generate Docker Compose configurations following Trash-Guides best practices, so that my services are optimally configured

#### Acceptance Criteria

1. WHEN configuration is complete, THE Stack Manager SHALL generate a Docker Compose v2 configuration file
2. THE Stack Manager SHALL configure volume mounts to support hardlinking between download and media folders
3. THE Stack Manager SHALL create separate /config and /data directory structures in the generated configuration
4. THE Stack Manager SHALL configure atomic move capability between download and media folders
5. THE Stack Manager SHALL apply Trash-Guides recommended settings for each selected service
6. THE Stack Manager SHALL generate an accompanying .env file with user-specified environment variables

### Requirement 5

**User Story:** As a user managing my stack, I want to start, stop, restart, and update individual services, so that I can maintain my media automation infrastructure

#### Acceptance Criteria

1. THE Stack Manager SHALL provide a stack management interface listing all configured services
2. WHEN a user selects a service, THE Stack Manager SHALL display available lifecycle actions
3. THE Stack Manager SHALL execute start operations when the user selects the start action
4. THE Stack Manager SHALL execute stop operations when the user selects the stop action
5. THE Stack Manager SHALL execute restart operations when the user selects the restart action
6. THE Stack Manager SHALL execute update operations when the user selects the update action
7. THE Stack Manager SHALL execute remove operations when the user selects the remove action
8. WHEN a lifecycle operation completes, THE Stack Manager SHALL display the operation result

### Requirement 6

**User Story:** As a user deploying my stack, I want to see real-time status updates during Docker operations, so that I can monitor deployment progress and identify issues

#### Acceptance Criteria

1. WHEN a Docker operation begins, THE Stack Manager SHALL display the deployment monitor screen
2. THE Stack Manager SHALL stream Docker Compose output to the deployment monitor in real-time
3. THE Stack Manager SHALL display the current operation status in the deployment monitor
4. WHEN a Docker operation completes successfully, THE Stack Manager SHALL display a success message
5. WHEN a Docker operation fails, THE Stack Manager SHALL display error details with troubleshooting guidance
6. THE Stack Manager SHALL allow users to cancel in-progress operations from the deployment monitor

### Requirement 7

**User Story:** As a user, I want the system to validate my configuration before deployment, so that I can catch errors early and avoid failed deployments

#### Acceptance Criteria

1. WHEN a user initiates deployment, THE Stack Manager SHALL validate the configuration before executing Docker commands
2. THE Stack Manager SHALL verify that all required paths exist and are accessible
3. THE Stack Manager SHALL verify that specified ports are available and not in use
4. THE Stack Manager SHALL verify that PUID and PGID values are valid system identifiers
5. WHEN validation fails, THE Stack Manager SHALL display specific validation errors with remediation steps
6. THE Stack Manager SHALL prevent deployment when validation errors are present

### Requirement 8

**User Story:** As a user on a headless Linux server, I want the application to have minimal dependencies and run efficiently in a terminal, so that I can manage my stack without a graphical interface

#### Acceptance Criteria

1. THE Stack Manager SHALL require only Python and Docker as system dependencies
2. THE Stack Manager SHALL use the uv package manager for dependency resolution
3. THE Stack Manager SHALL start within 3 seconds on a typical headless server
4. THE Stack Manager SHALL consume less than 100MB of memory during normal operation
5. THE Stack Manager SHALL persist user data and configurations between sessions

### Requirement 9

**User Story:** As a user, I want to view container logs for troubleshooting, so that I can diagnose issues with my services

#### Acceptance Criteria

1. THE Stack Manager SHALL provide a log viewer interface in the stack management screen
2. WHEN a user selects a service, THE Stack Manager SHALL display an option to view logs
3. WHEN a user requests logs, THE Stack Manager SHALL display the most recent 100 lines of container logs
4. THE Stack Manager SHALL support scrolling through log history
5. THE Stack Manager SHALL support real-time log streaming with auto-scroll capability
6. THE Stack Manager SHALL allow users to filter logs by severity level

### Requirement 10

**User Story:** As a user, I want to customize service-specific settings beyond the basic configuration, so that I can fine-tune each service for my needs

#### Acceptance Criteria

1. THE Stack Manager SHALL provide service-specific configuration options in the configuration wizard
2. WHERE a service requires custom port mappings, THE Stack Manager SHALL prompt for port configuration
3. WHERE a service supports additional volume mounts, THE Stack Manager SHALL allow users to specify custom mount points
4. THE Stack Manager SHALL provide default values for all service-specific settings
5. THE Stack Manager SHALL validate service-specific settings against known constraints
6. THE Stack Manager SHALL persist service-specific configurations in the generated Docker Compose file

### Requirement 11

**User Story:** As a user, I want to provide configuration values through an environment file, so that I can easily customize settings without going through the wizard each time

#### Acceptance Criteria

1. THE Stack Manager SHALL support loading configuration from a .env.example file in the project root
2. THE Stack Manager SHALL read environment variables for PUID, PGID, timezone, base path, and compose file path
3. WHEN an environment variable is set, THE Stack Manager SHALL use the environment value as the default in the configuration wizard
4. WHEN an environment variable is set, THE Stack Manager SHALL override saved configuration values with environment values
5. THE Stack Manager SHALL validate all environment variable values before using them
6. THE Stack Manager SHALL generate a .env.example file with all supported configuration variables and descriptions
7. THE Stack Manager SHALL document each environment variable with inline comments in the .env.example file
