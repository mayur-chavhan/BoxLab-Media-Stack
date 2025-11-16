# Implementation Plan

This plan breaks down the \*arr Stack Manager implementation into discrete, actionable tasks. Each task builds incrementally on previous work, with all code properly integrated.

## Task List

- [x] 1. Initialize project structure and dependencies

  - Set up project with uv package manager
  - Create folder structure (src/, tests/, templates/)
  - Configure pyproject.toml with dependencies (textual, docker, jinja2, pydantic, pyyaml)
  - Set up development tools (ruff, mypy, pytest)
  - Create basic README with project description
  - _Requirements: 8.2, 8.3_

- [x] 2. Implement core data models

  - Create models/configuration.py with Configuration, ServiceConfig, and PathConfig classes using Pydantic
  - Create models/service.py with ServiceStatus enum, ServiceInfo, and ResourceMetrics classes
  - Create models/stack.py with StackConfig and StackStatus classes
  - Create models/validation.py with ValidationResult and OperationResult classes
  - Add type hints and validation rules to all models
  - _Requirements: 3.5, 7.1_

- [x] 3. Create service definitions and templates

  - Create utils/services.py with SUPPORTED_SERVICES dictionary containing all service metadata
  - Create templates/base.yml.j2 with Docker Compose base structure
  - Create templates/services/sonarr.yml.j2 with Trash-Guides compliant configuration
  - Create templates/services/radarr.yml.j2 with Trash-Guides compliant configuration
  - Create templates/services/prowlarr.yml.j2 with configuration
  - Create templates/services/jellyfin.yml.j2 with configuration
  - Create templates/services/jellyseerr.yml.j2 with configuration
  - Create templates/services/ for remaining services (bazarr, recyclarr, tdarr, unpackerr, etc.)
  - Create templates/snippets/common_env.j2 for shared environment variables
  - _Requirements: 2.2, 4.5, 10.6_

- [x] 4. Implement configuration storage and persistence

  - Create core/config_store.py with ConfigRepository class
  - Implement save() method to persist configuration as JSON
  - Implement load() method to read configuration from disk
  - Implement get_config_dir() to determine user config directory (~/.config/arr-stack-manager)
  - Add methods to manage multiple stack configurations
  - Create directory structure on first run
  - _Requirements: 8.6_

- [x] 5. Implement configuration validator

  - Create core/validator.py with ConfigurationValidator class
  - Implement validate_paths() to check path existence and permissions
  - Implement validate_ports() to detect port conflicts
  - Implement validate_permissions() to verify PUID/PGID validity
  - Implement validate_docker() to check Docker daemon availability
  - Implement validate_service_config() for service-specific validation
  - Implement validate_complete_stack() for full stack validation
  - Add detailed error messages with remediation steps
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 6. Implement Docker Compose generator

  - Create core/generator.py with ComposeGenerator class
  - Implement generate_compose() to render Jinja2 templates into docker-compose.yml
  - Implement generate_env_file() to create .env with user variables
  - Implement configure_volumes() to set up hardlink-compatible volume mounts
  - Implement apply_trash_guides_settings() to apply best practices per service
  - Implement save_to_disk() to write generated files to output directory
  - Ensure proper volume structure for atomic moves (/data mount point)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 7. Implement Docker manager for container operations

  - Create core/docker_manager.py with DockerManager class
  - Initialize Docker client and handle connection errors
  - Implement start_service() to start individual containers
  - Implement stop_service() to stop containers gracefully
  - Implement restart_service() to restart containers
  - Implement remove_service() to remove containers and optionally volumes
  - Implement get_service_status() to query container state
  - Implement get_resource_usage() to collect CPU/memory metrics
  - Add error handling for Docker API failures
  - _Requirements: 5.3, 5.4, 5.5, 5.7, 5.8_

- [x] 8. Add Docker log streaming and monitoring

  - Extend DockerManager with get_service_logs() to retrieve container logs
  - Implement stream_logs() to stream logs in real-time using Docker API
  - Implement deploy_stack() to execute docker-compose up with progress tracking
  - Add update_service() to pull new images and recreate containers
  - Implement resource monitoring with periodic polling
  - _Requirements: 5.6, 9.2, 9.3, 9.4, 9.5_

- [x] 9. Create error handling system

  - Create utils/errors.py with ErrorHandler class
  - Define ERROR_MESSAGES dictionary with user-friendly error templates
  - Implement handle_error() to generate ErrorDisplay objects
  - Create custom exception classes for different error types
  - Add error logging functionality
  - _Requirements: 7.5, 7.6_

- [x] 10. Implement application controller

  - Create controller.py with AppController class
  - Implement initialize() to set up application state
  - Implement navigate_to() for screen navigation
  - Implement load_configuration() to load saved configs
  - Implement save_configuration() to persist user settings
  - Implement get_stack_status() to aggregate service statuses
  - Wire together validator, generator, and docker_manager
  - _Requirements: 1.1, 8.6_

- [x] 11. Create reusable UI components

  - Create components/service_card.py with ServiceCard widget to display service status
  - Create components/log_viewer.py with LogViewer widget for scrollable log display
  - Create components/progress_bar.py with enhanced progress display
  - Create components/service_list.py with selectable service list widget
  - Add styling using Textual CSS
  - _Requirements: 1.2, 1.3, 9.3_

- [x] 12. Implement Dashboard screen

  - Create screens/dashboard.py with DashboardScreen class
  - Display stack status overview with running/stopped service counts
  - Render list of services with status indicators and resource metrics
  - Add quick action buttons (Start All, Stop All, Restart All, Update All)
  - Implement real-time status updates using reactive properties
  - Add recent activity log display
  - Implement keyboard shortcuts for navigation
  - Wire up button actions to AppController methods
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 13. Implement Service Selector screen

  - Create screens/service_selector.py with ServiceSelectorScreen class
  - Display categorized service list (Media Management, Media Servers, etc.)
  - Implement multi-select checkboxes for service selection
  - Show service descriptions and requirements
  - Display selected service count
  - Implement validation to require at least one service
  - Add Continue button to proceed to configuration wizard
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 14. Implement Configuration Wizard screen - Base configuration

  - Create screens/config_wizard.py with ConfigWizardScreen class
  - Implement multi-step wizard navigation
  - Create Step 1: Service selection confirmation
  - Create Step 2: Base configuration (PUID, PGID, timezone)
  - Add auto-detection for current user PUID/PGID
  - Add timezone detection and selection
  - Implement input validation with real-time feedback
  - Add Back/Continue navigation buttons
  - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.7_

- [x] 15. Implement Configuration Wizard screen - Path configuration

  - Add Step 3: Directory structure configuration
  - Implement base path input with file browser
  - Display generated directory structure preview
  - Validate path existence and write permissions
  - Show validation status with checkmarks/errors
  - Create directory structure visualization
  - _Requirements: 3.4, 3.5, 3.6, 7.2_

- [x] 16. Implement Configuration Wizard screen - Service-specific settings

  - Add Step 4: Service-specific configuration
  - Implement port configuration for each selected service
  - Add custom volume mount configuration
  - Provide default values for all settings
  - Implement service-specific validation
  - Show configuration summary before completion
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 17. Implement Stack Management screen

  - Create screens/stack_manager.py with StackManagerScreen class
  - Display detailed service information (status, container ID, image, uptime)
  - Show resource usage with visual indicators (CPU/memory graphs)
  - Display volume mounts and port mappings
  - Add action buttons (Stop, Restart, Update, View Logs, Remove)
  - Implement recent logs preview section
  - Wire actions to DockerManager methods
  - Add confirmation dialogs for destructive actions
  - _Requirements: 5.1, 5.2, 5.8, 9.1_

- [x] 18. Implement Deployment Monitor screen

  - Create screens/deployment_monitor.py with DeploymentMonitorScreen class
  - Display deployment progress with step-by-step checklist
  - Show overall progress bar
  - Stream Docker Compose output in real-time
  - Display current operation status
  - Implement success/failure messaging
  - Add cancel operation functionality
  - Show elapsed time counter
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 19. Implement log viewer functionality

  - Extend Stack Management screen with full log viewer
  - Implement scrollable log display with syntax highlighting
  - Add real-time log streaming with auto-scroll toggle
  - Implement log filtering by severity level
  - Add search functionality within logs
  - Show log timestamps
  - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 20. Create main application and entry point

  - Create app.py with StackManagerApp class extending Textual App
  - Implement application initialization and screen registration
  - Set up CSS styling for consistent UI theme
  - Implement global keyboard shortcuts
  - Add help screen with keyboard shortcuts and usage guide
  - Create **main**.py as CLI entry point
  - Add command-line argument parsing (--config-dir, --stack-name, etc.)
  - _Requirements: 8.1, 8.4_

- [x] 21. Implement first-run experience

  - Add first-run detection in AppController
  - Create welcome screen with quick start guide
  - Implement system detection (Docker, user info, timezone)
  - Guide user through initial setup
  - Create default configuration directory structure
  - _Requirements: 8.6_

- [x] 22. Add deployment workflow integration

  - Wire Configuration Wizard completion to Compose Generator
  - Trigger validation before deployment
  - Launch Deployment Monitor with generated compose file
  - Handle deployment success/failure states
  - Navigate to Dashboard after successful deployment
  - Persist stack configuration after deployment
  - _Requirements: 4.1, 6.1, 7.1, 7.6_

- [x] 23. Implement update management

  - Add check for image updates in DockerManager
  - Implement pull and recreate workflow for updates
  - Show update availability in Dashboard
  - Add Update All functionality
  - Preserve data volumes during updates
  - _Requirements: 5.6_

- [x] 24. Write unit tests for core components

  - Write tests for Configuration models and validation
  - Write tests for ConfigurationValidator methods
  - Write tests for ComposeGenerator template rendering
  - Write tests for ConfigRepository persistence
  - Write tests for error handling
  - Achieve 80%+ code coverage for core/ modules
  - _Requirements: All_

- [ ] 25. Write integration tests for Docker operations

  - Write tests for DockerManager lifecycle operations using test containers
  - Write tests for complete deployment workflow
  - Write tests for log streaming
  - Write tests for resource monitoring
  - Test error scenarios (Docker unavailable, port conflicts, etc.)
  - _Requirements: 5.3, 5.4, 5.5, 5.6, 5.7, 6.1_

- [ ] 26. Write UI tests for Textual screens

  - Write snapshot tests for Dashboard screen rendering
  - Write tests for Service Selector interactions
  - Write tests for Configuration Wizard navigation
  - Write tests for Stack Management screen
  - Write tests for Deployment Monitor updates
  - Test keyboard navigation and shortcuts
  - _Requirements: 1.1, 2.1, 3.1, 5.1, 6.1_

- [ ] 27. Add comprehensive error handling

  - Implement error boundaries for all screens
  - Add user-friendly error displays with remediation steps
  - Implement logging for debugging
  - Add crash recovery and state preservation
  - Test all error scenarios
  - _Requirements: 7.5, 7.6_

- [ ] 28. Performance optimization

  - Optimize Docker API polling frequency
  - Implement caching for service status
  - Add lazy loading for service templates
  - Optimize log streaming buffer size
  - Measure and optimize startup time
  - Profile memory usage and optimize
  - _Requirements: 8.4, 8.5_

- [ ] 29. Create documentation

  - Write installation guide (uv tool install, binary, Docker)
  - Write user guide with screenshots/examples
  - Write development guide for contributors
  - Document all configuration options
  - Create troubleshooting guide
  - Add inline code documentation
  - _Requirements: All_

- [ ] 30. Set up packaging and distribution
  - Configure PyInstaller for standalone binary builds
  - Create build scripts for multiple platforms
  - Set up GitHub Actions for CI/CD
  - Configure PyPI publishing
  - Create release workflow
  - Test installation methods on clean systems
  - _Requirements: 8.1, 8.2, 8.3_

## Notes

- Each task should be completed and tested before moving to the next
- All code must be integrated into the application, no orphaned code
- Follow Trash-Guides best practices for all service configurations
- Maintain type hints and documentation throughout
- Use Pydantic for all data validation
- Follow Python best practices (PEP 8, type hints, docstrings)
