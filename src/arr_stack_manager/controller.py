"""Application controller for orchestrating business logic and screen navigation."""

import logging
from enum import Enum
from pathlib import Path
from typing import Any

from arr_stack_manager.core.config_store import ConfigRepository
from arr_stack_manager.core.docker_manager import DockerManager
from arr_stack_manager.core.generator import ComposeGenerator
from arr_stack_manager.core.validator import ConfigurationValidator
from arr_stack_manager.models.configuration import Configuration
from arr_stack_manager.models.service import ServiceInfo, ServiceStatus
from arr_stack_manager.models.stack import StackConfig, StackStatus
from arr_stack_manager.models.validation import ValidationResult
from arr_stack_manager.utils.env_loader import EnvironmentLoader

logger = logging.getLogger(__name__)


class ScreenType(str, Enum):
    """Available screen types for navigation."""

    DASHBOARD = "dashboard"
    SERVICE_SELECTOR = "service_selector"
    CONFIG_WIZARD = "config_wizard"
    STACK_MANAGER = "stack_manager"
    DEPLOYMENT_MONITOR = "deployment_monitor"
    LOG_VIEWER = "log_viewer"
    SETUP_WIZARD = "setup_wizard"


class AppController:
    """
    Application controller that orchestrates business logic and screen navigation.

    This controller acts as the central coordinator between the UI layer and
    the business logic layer, managing:
    - Application state and lifecycle
    - Screen navigation
    - Configuration persistence
    - Stack status aggregation
    - Integration of validator, generator, and docker_manager
    """

    def __init__(
        self,
        config_dir: Path | None = None,
        template_dir: Path | None = None,
    ) -> None:
        """
        Initialize the application controller.

        Args:
            config_dir: Optional custom configuration directory
            template_dir: Optional custom template directory
        """
        # Initialize core components
        self._config_repo = ConfigRepository(config_dir)
        self._validator = ConfigurationValidator()
        self._generator = ComposeGenerator(template_dir)
        self._docker_manager = DockerManager()
        self._env_loader = EnvironmentLoader()

        # Application state
        self._current_screen: ScreenType | None = None
        self._current_stack: StackConfig | None = None
        self._navigation_callbacks: dict[ScreenType, Any] = {}

        logger.info("AppController initialized successfully")

    def initialize(self) -> None:
        """
        Set up application state and perform initial checks.

        This method:
        - Verifies Docker availability
        - Checks for existing configurations
        - Performs system detection
        - Sets up initial application state
        """
        logger.info("Initializing application state")

        # Verify Docker is available
        docker_result = self._validator.validate_docker()
        if not docker_result.valid:
            logger.warning("Docker validation failed during initialization")
            logger.warning(f"Errors: {docker_result.errors}")
        else:
            logger.info("Docker daemon is available")

        # Check for existing stacks
        existing_stacks = self._config_repo.list_stacks()
        if existing_stacks:
            logger.info(f"Found {len(existing_stacks)} existing stack(s): {existing_stacks}")
        else:
            logger.info("No existing stacks found - first run")
            # Generate .env.example on first run if it doesn't exist
            self._generate_env_example_if_needed()

        logger.info("Application initialization complete")

    def _generate_env_example_if_needed(self) -> None:
        """Generate .env.example file on first run if it doesn't exist."""
        env_example_path = Path.cwd() / ".env.example"
        
        if not env_example_path.exists():
            try:
                self._env_loader.generate_example_file(env_example_path)
                logger.info(f"Generated .env.example file at: {env_example_path}")
            except Exception as e:
                logger.warning(f"Failed to generate .env.example: {e}")

    def is_first_run(self) -> bool:
        """
        Check if this is the first run of the application.

        Returns:
            True if no stacks exist and config directory is new, False otherwise
        """
        # Check if any stacks exist
        existing_stacks = self._config_repo.list_stacks()
        if existing_stacks:
            return False

        # Check if config directory was just created (no files)
        config_dir = self._config_repo.get_config_dir()
        stacks_dir = config_dir / "stacks"

        # If stacks directory doesn't exist or is empty, it's first run
        if not stacks_dir.exists():
            return True

        # Check if there are any files in the config directory
        has_files = any(config_dir.rglob("*.json"))
        return not has_files

    def navigate_to(self, screen: ScreenType, **kwargs: Any) -> None:
        """
        Navigate to a different screen.

        Args:
            screen: The screen type to navigate to
            **kwargs: Additional parameters to pass to the screen
        """
        logger.info(f"Navigating from {self._current_screen} to {screen}")
        self._current_screen = screen

        # Call registered navigation callback if available
        if screen in self._navigation_callbacks:
            callback = self._navigation_callbacks[screen]
            callback(**kwargs)
        else:
            logger.warning(f"No navigation callback registered for screen: {screen}")

    def register_navigation_callback(
        self, screen: ScreenType, callback: Any
    ) -> None:
        """
        Register a callback function for screen navigation.

        Args:
            screen: The screen type to register the callback for
            callback: The callback function to invoke when navigating to this screen
        """
        self._navigation_callbacks[screen] = callback
        logger.debug(f"Registered navigation callback for {screen}")

    def load_configuration(self, stack_name: str) -> StackConfig:
        """
        Load a saved stack configuration and merge with environment variables.

        Environment variables take precedence over saved configuration values.

        Args:
            stack_name: Name of the stack to load

        Returns:
            The loaded stack configuration with environment variables merged

        Raises:
            FileNotFoundError: If the configuration doesn't exist
            ValueError: If the configuration is invalid
        """
        logger.info(f"Loading configuration for stack: {stack_name}")

        try:
            stack_config = self._config_repo.load(stack_name)
            
            # Merge environment variables into configuration
            merged_config = stack_config.configuration.merge_with_env(self._env_loader)
            stack_config.configuration = merged_config
            
            self._current_stack = stack_config
            logger.info(f"Successfully loaded stack configuration: {stack_name}")
            logger.debug("Environment variables merged into configuration")
            return stack_config
        except FileNotFoundError:
            logger.error(f"Stack configuration not found: {stack_name}")
            raise
        except ValueError as e:
            logger.error(f"Invalid stack configuration: {e}")
            raise

    def save_configuration(self, stack_config: StackConfig) -> None:
        """
        Persist a stack configuration to disk.

        Args:
            stack_config: The stack configuration to save

        Raises:
            IOError: If unable to write to disk
            ValueError: If stack_config is invalid
        """
        logger.info(f"Saving configuration for stack: {stack_config.name}")

        try:
            self._config_repo.save(stack_config)
            self._current_stack = stack_config
            logger.info(f"Successfully saved stack configuration: {stack_config.name}")
        except (IOError, ValueError) as e:
            logger.error(f"Failed to save stack configuration: {e}")
            raise

    def get_env_defaults(self) -> dict[str, Any]:
        """
        Get default configuration values from environment variables.

        This method is useful for pre-filling wizard forms with environment values.

        Returns:
            Dictionary containing environment variable values for configuration
        """
        logger.debug("Getting environment defaults for configuration")
        
        env_vars = self._env_loader.get_all()
        
        defaults = {}
        
        # Map environment variables to configuration fields
        if "PUID" in env_vars:
            defaults["puid"] = env_vars["PUID"]
        
        if "PGID" in env_vars:
            defaults["pgid"] = env_vars["PGID"]
        
        # Support both TZ and TIMEZONE
        if "TZ" in env_vars:
            defaults["timezone"] = env_vars["TZ"]
        elif "TIMEZONE" in env_vars:
            defaults["timezone"] = env_vars["TIMEZONE"]
        
        if "BASE_PATH" in env_vars:
            defaults["base_path"] = env_vars["BASE_PATH"]
        
        if "CONFIG_PATH" in env_vars:
            defaults["config_path"] = env_vars["CONFIG_PATH"]
        
        if "DATA_PATH" in env_vars:
            defaults["data_path"] = env_vars["DATA_PATH"]
        
        if "STACK_NAME" in env_vars:
            defaults["stack_name"] = env_vars["STACK_NAME"]
        
        logger.debug(f"Environment defaults: {list(defaults.keys())}")
        return defaults

    def load_or_create_configuration(self, stack_name: str) -> StackConfig | None:
        """
        Load a saved configuration or create one from environment variables.

        This method attempts to:
        1. Load saved configuration if it exists
        2. Create configuration from environment variables if no saved config exists
        3. Return None if neither saved config nor required env vars exist

        Args:
            stack_name: Name of the stack to load or create

        Returns:
            StackConfig if configuration exists or can be created from env, None otherwise
        """
        logger.info(f"Loading or creating configuration for stack: {stack_name}")
        
        # Try to load saved configuration first
        try:
            return self.load_configuration(stack_name)
        except FileNotFoundError:
            logger.info(f"No saved configuration found for stack: {stack_name}")
        
        # Try to create from environment variables
        try:
            logger.info("Attempting to create configuration from environment variables")
            config = Configuration.from_env(self._env_loader)
            
            # Create a new stack config
            from datetime import datetime
            stack_config = StackConfig(
                name=stack_name,
                configuration=config,
                compose_path="",  # Will be set during deployment
                created_at=datetime.now(),
                last_modified=datetime.now(),
            )
            
            self._current_stack = stack_config
            logger.info("Successfully created configuration from environment variables")
            return stack_config
            
        except ValueError as e:
            logger.info(f"Cannot create configuration from environment: {e}")
            logger.info("User will need to use configuration wizard")
            return None

    def get_stack_status(self, stack_name: str | None = None) -> StackStatus:
        """
        Aggregate service statuses for a stack.

        Args:
            stack_name: Name of the stack to check. If None, uses current stack.

        Returns:
            StackStatus with aggregated service information

        Raises:
            ValueError: If no stack is specified and no current stack is set
        """
        # Determine which stack to check
        if stack_name is None:
            if self._current_stack is None:
                raise ValueError("No stack specified and no current stack set")
            stack_name = self._current_stack.name
            config = self._current_stack.configuration
        else:
            # Load the stack configuration
            stack_config = self._config_repo.load(stack_name)
            config = stack_config.configuration

        logger.info(f"Getting status for stack: {stack_name}")

        # Get enabled services
        enabled_services = config.get_selected_services()
        total_services = len(enabled_services)

        # Query status for each service
        running_count = 0
        stopped_count = 0
        error_count = 0

        for service_name in enabled_services:
            service_info = self._docker_manager.get_service_status(service_name)

            if service_info.status == ServiceStatus.RUNNING:
                running_count += 1
            elif service_info.status in (ServiceStatus.STOPPED, ServiceStatus.UNKNOWN):
                stopped_count += 1
            elif service_info.status == ServiceStatus.ERROR:
                error_count += 1
            else:
                # Starting/stopping states count as transitional
                stopped_count += 1

        stack_status = StackStatus(
            name=stack_name,
            total_services=total_services,
            running_services=running_count,
            stopped_services=stopped_count,
            error_services=error_count,
        )

        logger.info(
            f"Stack status: {running_count}/{total_services} running, "
            f"{stopped_count} stopped, {error_count} errors"
        )

        return stack_status

    def get_service_info(self, service_name: str) -> ServiceInfo:
        """
        Get detailed information about a specific service.

        Args:
            service_name: Name of the service to query

        Returns:
            ServiceInfo with current status and metrics
        """
        logger.debug(f"Getting service info for: {service_name}")
        return self._docker_manager.get_service_status(service_name)

    def validate_stack(self, stack_config: StackConfig) -> ValidationResult:
        """
        Validate a complete stack configuration before deployment.

        Args:
            stack_config: The stack configuration to validate

        Returns:
            ValidationResult with any errors or warnings
        """
        logger.info(f"Validating stack configuration: {stack_config.name}")
        result = self._validator.validate_complete_stack(stack_config)

        if result.valid:
            logger.info("Stack validation passed")
        else:
            logger.warning(f"Stack validation failed with {len(result.errors)} error(s)")

        return result

    def generate_compose_files(
        self, stack_config: StackConfig, output_dir: str | Path
    ) -> tuple[str, str]:
        """
        Generate Docker Compose and .env files for a stack.

        Args:
            stack_config: The stack configuration to generate files for
            output_dir: Directory where files should be written

        Returns:
            Tuple of (compose_content, env_content)

        Raises:
            ValueError: If configuration is invalid
        """
        logger.info(f"Generating compose files for stack: {stack_config.name}")

        try:
            # Generate docker-compose.yml content
            compose_content = self._generator.generate_compose(stack_config)

            # Generate .env file content
            env_content = self._generator.generate_env_file(stack_config.configuration)

            # Save to disk
            self._generator.save_to_disk(output_dir, compose_content, env_content)

            logger.info(f"Successfully generated compose files in: {output_dir}")
            return compose_content, env_content

        except Exception as e:
            logger.error(f"Failed to generate compose files: {e}")
            raise

    def list_available_stacks(self) -> list[str]:
        """
        Get a list of all saved stack configurations.

        Returns:
            List of stack names
        """
        stacks = self._config_repo.list_stacks()
        logger.debug(f"Found {len(stacks)} available stack(s)")
        return stacks

    def delete_stack(self, stack_name: str) -> None:
        """
        Delete a saved stack configuration.

        Args:
            stack_name: Name of the stack to delete

        Raises:
            FileNotFoundError: If the stack doesn't exist
        """
        logger.info(f"Deleting stack configuration: {stack_name}")
        self._config_repo.delete(stack_name)

        # Clear current stack if it was deleted
        if self._current_stack and self._current_stack.name == stack_name:
            self._current_stack = None

        logger.info(f"Successfully deleted stack: {stack_name}")

    def backup_stack(self, stack_name: str) -> Path:
        """
        Create a backup of a stack configuration.

        Args:
            stack_name: Name of the stack to backup

        Returns:
            Path to the backup file

        Raises:
            FileNotFoundError: If the stack doesn't exist
        """
        logger.info(f"Creating backup of stack: {stack_name}")
        backup_path = self._config_repo.backup(stack_name)
        logger.info(f"Backup created at: {backup_path}")
        return backup_path

    @property
    def current_screen(self) -> ScreenType | None:
        """Get the current screen type."""
        return self._current_screen

    @property
    def current_stack(self) -> StackConfig | None:
        """Get the current stack configuration."""
        return self._current_stack

    @current_stack.setter
    def current_stack(self, stack: StackConfig | None) -> None:
        """Set the current stack configuration."""
        self._current_stack = stack
        if stack:
            logger.info(f"Current stack set to: {stack.name}")
        else:
            logger.info("Current stack cleared")

    @property
    def validator(self) -> ConfigurationValidator:
        """Get the configuration validator instance."""
        return self._validator

    @property
    def generator(self) -> ComposeGenerator:
        """Get the compose generator instance."""
        return self._generator

    @property
    def docker_manager(self) -> DockerManager:
        """Get the Docker manager instance."""
        return self._docker_manager

    @property
    def config_repository(self) -> ConfigRepository:
        """Get the configuration repository instance."""
        return self._config_repo

    @property
    def env_loader(self) -> EnvironmentLoader:
        """Get the environment loader instance."""
        return self._env_loader

    def is_docker_available(self) -> bool:
        """
        Check if Docker daemon is available.

        Returns:
            True if Docker is available, False otherwise
        """
        return self._docker_manager.is_docker_available()

    def get_docker_version(self) -> str | None:
        """
        Get Docker daemon version.

        Returns:
            Docker version string, or None if unavailable
        """
        return self._docker_manager.get_docker_version()

    def check_service_updates(self, service_name: str) -> bool:
        """
        Check if an update is available for a service.

        Args:
            service_name: Name of the service to check

        Returns:
            True if an update is available, False otherwise
        """
        logger.debug(f"Checking for updates: {service_name}")
        return self._docker_manager.check_for_updates(service_name)

    def update_service(self, service_name: str) -> Any:
        """
        Update a service to the latest image version.

        Args:
            service_name: Name of the service to update

        Returns:
            OperationResult indicating success or failure
        """
        logger.info(f"Updating service: {service_name}")
        return self._docker_manager.update_service(service_name)

    def update_all_services(self) -> dict[str, Any]:
        """
        Update all services in the current stack.

        Returns:
            Dictionary mapping service names to OperationResults
        """
        if not self._current_stack:
            logger.error("Cannot update services: no current stack set")
            return {}

        logger.info(f"Updating all services in stack: {self._current_stack.name}")

        enabled_services = self._current_stack.configuration.get_selected_services()
        results = {}

        for service_name in enabled_services:
            logger.info(f"Updating service: {service_name}")
            result = self._docker_manager.update_service(service_name)
            results[service_name] = result

            if result.success:
                logger.info(f"Successfully updated {service_name}")
            else:
                logger.warning(f"Failed to update {service_name}: {result.message}")

        return results

    def start_service(self, service_name: str) -> Any:
        """
        Start a service container.

        Args:
            service_name: Name of the service to start

        Returns:
            OperationResult indicating success or failure
        """
        logger.info(f"Starting service: {service_name}")
        return self._docker_manager.start_service(service_name)

    def stop_service(self, service_name: str) -> Any:
        """
        Stop a service container.

        Args:
            service_name: Name of the service to stop

        Returns:
            OperationResult indicating success or failure
        """
        logger.info(f"Stopping service: {service_name}")
        return self._docker_manager.stop_service(service_name)

    def restart_service(self, service_name: str) -> Any:
        """
        Restart a service container.

        Args:
            service_name: Name of the service to restart

        Returns:
            OperationResult indicating success or failure
        """
        logger.info(f"Restarting service: {service_name}")
        return self._docker_manager.restart_service(service_name)
