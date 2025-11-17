"""Tests for the application controller."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from arr_stack_manager.controller import AppController, ScreenType
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.service import ServiceInfo, ServiceStatus
from arr_stack_manager.models.stack import StackConfig, StackStatus
from arr_stack_manager.models.validation import ValidationResult


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_stack_config():
    """Create a sample stack configuration for testing."""
    config = Configuration(
        puid=1000,
        pgid=1000,
        timezone="America/New_York",
        paths=PathConfig(base_path="/mnt/storage"),
        services={
            "sonarr": ServiceConfig(name="sonarr", port=8989, enabled=True),
            "radarr": ServiceConfig(name="radarr", port=7878, enabled=True),
        },
    )
    return StackConfig(
        name="test-stack",
        configuration=config,
        compose_path="/tmp/docker-compose.yml",
    )


@pytest.fixture
def mock_docker_manager():
    """Create a mock Docker manager."""
    with patch("arr_stack_manager.controller.DockerManager") as mock:
        instance = mock.return_value
        instance.ping = Mock()
        instance.is_docker_available = Mock(return_value=True)
        instance.get_docker_version = Mock(return_value="24.0.0")
        yield instance


@pytest.fixture
def controller(temp_config_dir, mock_docker_manager):
    """Create an AppController instance for testing."""
    return AppController(config_dir=temp_config_dir)


def test_controller_initialization(controller):
    """Test that controller initializes with all required components."""
    assert controller._config_repo is not None
    assert controller._validator is not None
    assert controller._generator is not None
    assert controller._docker_manager is not None
    assert controller._current_screen is None
    assert controller._current_stack is None


def test_initialize(controller, mock_docker_manager):
    """Test application initialization."""
    # Mock Docker validation
    with patch.object(controller._validator, "validate_docker") as mock_validate:
        mock_validate.return_value = ValidationResult(valid=True)
        
        controller.initialize()
        
        # Verify Docker validation was called
        mock_validate.assert_called_once()


def test_navigate_to(controller):
    """Test screen navigation."""
    # Register a callback
    callback_called = False
    callback_kwargs = {}
    
    def test_callback(**kwargs):
        nonlocal callback_called, callback_kwargs
        callback_called = True
        callback_kwargs = kwargs
    
    controller.register_navigation_callback(ScreenType.DASHBOARD, test_callback)
    
    # Navigate to dashboard
    controller.navigate_to(ScreenType.DASHBOARD, test_param="value")
    
    assert controller.current_screen == ScreenType.DASHBOARD
    assert callback_called
    assert callback_kwargs == {"test_param": "value"}


def test_navigate_to_without_callback(controller):
    """Test navigation to screen without registered callback."""
    # Should not raise an error
    controller.navigate_to(ScreenType.SERVICE_SELECTOR)
    assert controller.current_screen == ScreenType.SERVICE_SELECTOR


def test_save_and_load_configuration(controller, sample_stack_config):
    """Test saving and loading stack configurations."""
    # Save configuration
    controller.save_configuration(sample_stack_config)
    
    # Verify current stack is set
    assert controller.current_stack == sample_stack_config
    
    # Clear current stack
    controller.current_stack = None
    
    # Load configuration
    loaded = controller.load_configuration("test-stack")
    
    assert loaded.name == sample_stack_config.name
    assert loaded.configuration.puid == sample_stack_config.configuration.puid
    assert controller.current_stack == loaded


def test_load_nonexistent_configuration(controller):
    """Test loading a configuration that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        controller.load_configuration("nonexistent-stack")


def test_get_stack_status(controller, sample_stack_config, mock_docker_manager):
    """Test getting aggregated stack status."""
    # Save the stack configuration
    controller.save_configuration(sample_stack_config)
    
    # Mock service status responses
    def mock_get_status(service_name):
        if service_name == "sonarr":
            return ServiceInfo(
                name="sonarr",
                status=ServiceStatus.RUNNING,
                container_id="abc123",
                image="lscr.io/linuxserver/sonarr:latest",
            )
        else:  # radarr
            return ServiceInfo(
                name="radarr",
                status=ServiceStatus.STOPPED,
                container_id="def456",
                image="lscr.io/linuxserver/radarr:latest",
            )
    
    mock_docker_manager.get_service_status = Mock(side_effect=mock_get_status)
    
    # Get stack status
    status = controller.get_stack_status("test-stack")
    
    assert status.name == "test-stack"
    assert status.total_services == 2
    assert status.running_services == 1
    assert status.stopped_services == 1
    assert status.error_services == 0


def test_get_stack_status_with_current_stack(controller, sample_stack_config, mock_docker_manager):
    """Test getting stack status using current stack."""
    controller.current_stack = sample_stack_config
    
    # Mock service status
    mock_docker_manager.get_service_status = Mock(
        return_value=ServiceInfo(
            name="test",
            status=ServiceStatus.RUNNING,
            container_id="abc",
            image="test:latest",
        )
    )
    
    # Get status without specifying stack name
    status = controller.get_stack_status()
    
    assert status.name == "test-stack"
    assert status.total_services == 2


def test_get_stack_status_no_stack_raises_error(controller):
    """Test that getting status without a stack raises ValueError."""
    with pytest.raises(ValueError, match="No stack specified"):
        controller.get_stack_status()


def test_get_service_info(controller, mock_docker_manager):
    """Test getting service information."""
    expected_info = ServiceInfo(
        name="sonarr",
        status=ServiceStatus.RUNNING,
        container_id="abc123",
        image="lscr.io/linuxserver/sonarr:latest",
    )
    
    mock_docker_manager.get_service_status = Mock(return_value=expected_info)
    
    info = controller.get_service_info("sonarr")
    
    assert info == expected_info
    mock_docker_manager.get_service_status.assert_called_once_with("sonarr")


def test_validate_stack(controller, sample_stack_config):
    """Test stack validation."""
    with patch.object(controller._validator, "validate_complete_stack") as mock_validate:
        expected_result = ValidationResult(valid=True)
        mock_validate.return_value = expected_result
        
        result = controller.validate_stack(sample_stack_config)
        
        assert result == expected_result
        mock_validate.assert_called_once_with(sample_stack_config)


def test_generate_compose_files(controller, sample_stack_config, temp_config_dir):
    """Test generating Docker Compose files."""
    output_dir = temp_config_dir / "output"
    
    with patch.object(controller._generator, "generate_compose") as mock_compose, \
         patch.object(controller._generator, "generate_env_file") as mock_env, \
         patch.object(controller._generator, "save_to_disk") as mock_save:
        
        mock_compose.return_value = "compose content"
        mock_env.return_value = "env content"
        
        compose, env = controller.generate_compose_files(sample_stack_config, output_dir)
        
        assert compose == "compose content"
        assert env == "env content"
        mock_compose.assert_called_once_with(sample_stack_config)
        mock_env.assert_called_once_with(sample_stack_config.configuration)
        mock_save.assert_called_once_with(output_dir, "compose content", "env content")


def test_list_available_stacks(controller, sample_stack_config):
    """Test listing available stacks."""
    # Initially empty
    assert controller.list_available_stacks() == []
    
    # Save a stack
    controller.save_configuration(sample_stack_config)
    
    stacks = controller.list_available_stacks()
    assert "test-stack" in stacks


def test_delete_stack(controller, sample_stack_config):
    """Test deleting a stack configuration."""
    # Save a stack
    controller.save_configuration(sample_stack_config)
    assert controller.current_stack == sample_stack_config
    
    # Delete it
    controller.delete_stack("test-stack")
    
    # Verify it's gone
    assert "test-stack" not in controller.list_available_stacks()
    # Current stack should be cleared
    assert controller.current_stack is None


def test_delete_different_stack_keeps_current(controller, sample_stack_config):
    """Test that deleting a different stack doesn't clear current stack."""
    controller.current_stack = sample_stack_config
    
    # Save another stack
    other_stack = sample_stack_config.model_copy(deep=True)
    other_stack.name = "other-stack"
    controller.save_configuration(other_stack)
    
    # Set current back to test-stack
    controller.current_stack = sample_stack_config
    
    # Delete other stack
    controller.delete_stack("other-stack")
    
    # Current stack should still be set
    assert controller.current_stack == sample_stack_config


def test_backup_stack(controller, sample_stack_config):
    """Test creating a stack backup."""
    controller.save_configuration(sample_stack_config)
    
    backup_path = controller.backup_stack("test-stack")
    
    assert backup_path.exists()
    assert "test-stack" in backup_path.name


def test_current_stack_property(controller, sample_stack_config):
    """Test current_stack property getter and setter."""
    assert controller.current_stack is None
    
    controller.current_stack = sample_stack_config
    assert controller.current_stack == sample_stack_config
    
    controller.current_stack = None
    assert controller.current_stack is None


def test_component_properties(controller):
    """Test that component properties return correct instances."""
    assert controller.validator is not None
    assert controller.generator is not None
    assert controller.docker_manager is not None
    assert controller.config_repository is not None


def test_is_docker_available(controller, mock_docker_manager):
    """Test Docker availability check."""
    mock_docker_manager.is_docker_available.return_value = True
    assert controller.is_docker_available() is True
    
    mock_docker_manager.is_docker_available.return_value = False
    assert controller.is_docker_available() is False


def test_get_docker_version(controller, mock_docker_manager):
    """Test getting Docker version."""
    mock_docker_manager.get_docker_version.return_value = "24.0.0"
    assert controller.get_docker_version() == "24.0.0"
    
    mock_docker_manager.get_docker_version.return_value = None
    assert controller.get_docker_version() is None


def test_check_service_updates(controller, mock_docker_manager):
    """Test checking for service updates."""
    mock_docker_manager.check_for_updates = Mock(return_value=True)
    
    has_update = controller.check_service_updates("sonarr")
    
    assert has_update is True
    mock_docker_manager.check_for_updates.assert_called_once_with("sonarr")


def test_update_service(controller, mock_docker_manager):
    """Test updating a single service."""
    from arr_stack_manager.models.validation import OperationResult
    
    expected_result = OperationResult.success_result(
        message="Service updated successfully"
    )
    mock_docker_manager.update_service = Mock(return_value=expected_result)
    
    result = controller.update_service("sonarr")
    
    assert result.success is True
    mock_docker_manager.update_service.assert_called_once_with("sonarr")


def test_update_all_services(controller, sample_stack_config, mock_docker_manager):
    """Test updating all services in a stack."""
    from arr_stack_manager.models.validation import OperationResult
    
    controller.current_stack = sample_stack_config
    
    # Mock update results
    mock_docker_manager.update_service = Mock(
        return_value=OperationResult.success_result(message="Updated")
    )
    
    results = controller.update_all_services()
    
    assert len(results) == 2
    assert "sonarr" in results
    assert "radarr" in results
    assert results["sonarr"].success is True
    assert results["radarr"].success is True


def test_update_all_services_no_stack(controller, mock_docker_manager):
    """Test updating all services without a current stack."""
    results = controller.update_all_services()
    
    assert results == {}


def test_start_service(controller, mock_docker_manager):
    """Test starting a service."""
    from arr_stack_manager.models.validation import OperationResult
    
    expected_result = OperationResult.success_result(message="Service started")
    mock_docker_manager.start_service = Mock(return_value=expected_result)
    
    result = controller.start_service("sonarr")
    
    assert result.success is True
    mock_docker_manager.start_service.assert_called_once_with("sonarr")


def test_stop_service(controller, mock_docker_manager):
    """Test stopping a service."""
    from arr_stack_manager.models.validation import OperationResult
    
    expected_result = OperationResult.success_result(message="Service stopped")
    mock_docker_manager.stop_service = Mock(return_value=expected_result)
    
    result = controller.stop_service("sonarr")
    
    assert result.success is True
    mock_docker_manager.stop_service.assert_called_once_with("sonarr")


def test_restart_service(controller, mock_docker_manager):
    """Test restarting a service."""
    from arr_stack_manager.models.validation import OperationResult
    
    expected_result = OperationResult.success_result(message="Service restarted")
    mock_docker_manager.restart_service = Mock(return_value=expected_result)
    
    result = controller.restart_service("sonarr")
    
    assert result.success is True
    mock_docker_manager.restart_service.assert_called_once_with("sonarr")


def test_env_loader_initialized(controller):
    """Test that environment loader is initialized."""
    assert controller._env_loader is not None
    assert controller.env_loader is not None


def test_get_env_defaults(controller):
    """Test getting environment defaults."""
    with patch.object(controller._env_loader, "get_all") as mock_get_all:
        mock_get_all.return_value = {
            "PUID": 1001,
            "PGID": 1001,
            "TZ": "America/Los_Angeles",
            "BASE_PATH": "/data",
            "STACK_NAME": "my-stack",
        }
        
        defaults = controller.get_env_defaults()
        
        assert defaults["puid"] == 1001
        assert defaults["pgid"] == 1001
        assert defaults["timezone"] == "America/Los_Angeles"
        assert defaults["base_path"] == "/data"
        assert defaults["stack_name"] == "my-stack"


def test_get_env_defaults_with_timezone_alternative(controller):
    """Test getting environment defaults with TIMEZONE instead of TZ."""
    with patch.object(controller._env_loader, "get_all") as mock_get_all:
        mock_get_all.return_value = {
            "TIMEZONE": "Europe/London",
        }
        
        defaults = controller.get_env_defaults()
        
        assert defaults["timezone"] == "Europe/London"


def test_get_env_defaults_empty(controller):
    """Test getting environment defaults when no env vars are set."""
    with patch.object(controller._env_loader, "get_all") as mock_get_all:
        mock_get_all.return_value = {}
        
        defaults = controller.get_env_defaults()
        
        assert defaults == {}


def test_load_configuration_merges_env(controller, sample_stack_config):
    """Test that loading configuration merges environment variables."""
    # Save configuration
    controller.save_configuration(sample_stack_config)
    
    # Mock environment loader to return different values
    with patch.object(controller._env_loader, "get") as mock_get:
        def get_side_effect(key):
            env_values = {
                "PUID": 2000,
                "PGID": 2000,
                "TZ": "Europe/Paris",
            }
            return env_values.get(key)
        
        mock_get.side_effect = get_side_effect
        
        # Load configuration
        loaded = controller.load_configuration("test-stack")
        
        # Verify environment values were merged
        assert loaded.configuration.puid == 2000
        assert loaded.configuration.pgid == 2000
        assert loaded.configuration.timezone == "Europe/Paris"


def test_load_or_create_configuration_loads_existing(controller, sample_stack_config):
    """Test load_or_create_configuration loads existing config."""
    # Save configuration
    controller.save_configuration(sample_stack_config)
    
    # Load or create
    loaded = controller.load_or_create_configuration("test-stack")
    
    assert loaded is not None
    assert loaded.name == "test-stack"


def test_load_or_create_configuration_creates_from_env(controller):
    """Test load_or_create_configuration creates config from environment."""
    with patch.object(controller._env_loader, "get") as mock_get:
        def get_side_effect(key):
            env_values = {
                "PUID": 1000,
                "PGID": 1000,
                "TZ": "UTC",
                "BASE_PATH": "/mnt/data",
            }
            return env_values.get(key)
        
        mock_get.side_effect = get_side_effect
        
        # Load or create (no saved config exists)
        created = controller.load_or_create_configuration("new-stack")
        
        assert created is not None
        assert created.name == "new-stack"
        assert created.configuration.puid == 1000
        assert created.configuration.pgid == 1000
        assert created.configuration.timezone == "UTC"
        assert created.configuration.paths.base_path == "/mnt/data"


def test_load_or_create_configuration_returns_none_without_env(controller):
    """Test load_or_create_configuration returns None when no config or env exists."""
    with patch.object(controller._env_loader, "get") as mock_get:
        mock_get.return_value = None
        
        # Load or create (no saved config, no env vars)
        result = controller.load_or_create_configuration("nonexistent-stack")
        
        assert result is None
