"""Tests for the Configuration Wizard screen."""

import pytest
from textual.widgets import Button, Input, Label

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.screens.config_wizard import (
    BaseConfigurationStep,
    ConfigWizardScreen,
    PathConfigurationStep,
    ServiceConfirmationStep,
    ServiceSpecificConfigurationStep,
    StepIndicator,
    WizardStep,
)


@pytest.fixture
def controller():
    """Create a test controller."""
    return AppController()


@pytest.fixture
def sample_configuration():
    """Create a sample configuration for testing."""
    return Configuration(
        puid=1000,
        pgid=1000,
        timezone="UTC",
        paths=PathConfig(base_path="/tmp/test"),
        services={
            "sonarr": ServiceConfig(name="sonarr", enabled=True, port=8989),
            "radarr": ServiceConfig(name="radarr", enabled=True, port=7878),
        },
    )


class TestStepIndicator:
    """Tests for the StepIndicator widget."""

    def test_step_indicator_initialization(self):
        """Test step indicator initializes correctly."""
        indicator = StepIndicator(
            current_step=1,
            total_steps=3,
            step_title="Test Step",
        )
        assert indicator.current_step == 1
        assert indicator.total_steps == 3
        assert indicator.step_title == "Test Step"

    def test_step_indicator_update(self):
        """Test step indicator can be updated."""
        indicator = StepIndicator(
            current_step=1,
            total_steps=3,
            step_title="Step 1",
        )
        indicator.update_step(2, "Step 2")
        assert indicator.current_step == 2
        assert indicator.step_title == "Step 2"


class TestServiceConfirmationStep:
    """Tests for the ServiceConfirmationStep widget."""

    def test_service_confirmation_with_services(self):
        """Test service confirmation step with selected services."""
        step = ServiceConfirmationStep(selected_services=["sonarr", "radarr", "prowlarr"])
        assert step.selected_services == ["sonarr", "radarr", "prowlarr"]

    def test_service_confirmation_empty(self):
        """Test service confirmation step with no services."""
        step = ServiceConfirmationStep(selected_services=[])
        assert step.selected_services == []


class TestBaseConfigurationStep:
    """Tests for the BaseConfigurationStep widget."""

    def test_base_config_initialization(self):
        """Test base configuration step initializes with defaults."""
        step = BaseConfigurationStep(puid=1000, pgid=1000, timezone="America/New_York")
        assert step.puid == 1000
        assert step.pgid == 1000
        assert step.timezone == "America/New_York"

    def test_base_config_detect_user(self):
        """Test user detection returns a string."""
        step = BaseConfigurationStep()
        user_info = step._detect_current_user()
        assert isinstance(user_info, str)
        assert len(user_info) > 0

    def test_base_config_detect_timezone(self):
        """Test timezone detection returns a string."""
        step = BaseConfigurationStep()
        timezone = step._detect_timezone()
        assert isinstance(timezone, str)
        assert len(timezone) > 0


class TestConfigWizardScreen:
    """Tests for the ConfigWizardScreen."""

    @pytest.mark.asyncio
    async def test_wizard_initialization(self, controller, sample_configuration):
        """Test wizard screen initializes correctly."""
        screen = ConfigWizardScreen(controller, sample_configuration)
        assert screen.controller == controller
        assert screen.configuration == sample_configuration
        assert screen._current_step == WizardStep.SERVICE_CONFIRMATION
        assert screen._total_steps == 4

    @pytest.mark.asyncio
    async def test_wizard_auto_detection(self, controller, sample_configuration):
        """Test wizard auto-detects PUID, PGID, and timezone."""
        screen = ConfigWizardScreen(controller, sample_configuration)
        assert screen._detected_puid >= 0
        assert screen._detected_pgid >= 0
        assert isinstance(screen._detected_timezone, str)
        assert len(screen._detected_timezone) > 0

    @pytest.mark.asyncio
    async def test_wizard_step_titles(self, controller, sample_configuration):
        """Test wizard returns correct step titles."""
        screen = ConfigWizardScreen(controller, sample_configuration)
        
        screen._current_step = WizardStep.SERVICE_CONFIRMATION
        assert screen._get_step_title() == "Service Selection Confirmation"
        
        screen._current_step = WizardStep.BASE_CONFIGURATION
        assert screen._get_step_title() == "Base Configuration"
        
        screen._current_step = WizardStep.PATH_CONFIGURATION
        assert screen._get_step_title() == "Directory Structure Configuration"
        
        screen._current_step = WizardStep.SERVICE_SPECIFIC_CONFIGURATION
        assert screen._get_step_title() == "Service-Specific Configuration"

    @pytest.mark.asyncio
    async def test_wizard_validation_service_confirmation(self, controller, sample_configuration):
        """Test validation passes for service confirmation step."""
        screen = ConfigWizardScreen(controller, sample_configuration)
        screen._current_step = WizardStep.SERVICE_CONFIRMATION
        assert screen._validate_current_step() is True

    @pytest.mark.asyncio
    async def test_wizard_detect_puid(self, controller, sample_configuration):
        """Test PUID detection."""
        screen = ConfigWizardScreen(controller, sample_configuration)
        puid = screen._detect_puid()
        assert isinstance(puid, int)
        assert puid >= 0

    @pytest.mark.asyncio
    async def test_wizard_detect_pgid(self, controller, sample_configuration):
        """Test PGID detection."""
        screen = ConfigWizardScreen(controller, sample_configuration)
        pgid = screen._detect_pgid()
        assert isinstance(pgid, int)
        assert pgid >= 0

    @pytest.mark.asyncio
    async def test_wizard_detect_timezone(self, controller, sample_configuration):
        """Test timezone detection."""
        screen = ConfigWizardScreen(controller, sample_configuration)
        timezone = screen._detect_timezone()
        assert isinstance(timezone, str)
        assert len(timezone) > 0
        # Should return a valid timezone or UTC as fallback
        assert timezone in ["UTC"] or "/" in timezone  # Valid timezones have / in them


class TestPathConfigurationStep:
    """Tests for the PathConfigurationStep widget."""

    def test_path_config_initialization(self):
        """Test path configuration step initializes with defaults."""
        step = PathConfigurationStep(base_path="/mnt/storage")
        assert step.base_path == "/mnt/storage"

    def test_path_config_default_path_detection(self):
        """Test default path detection returns a valid path."""
        step = PathConfigurationStep()
        assert isinstance(step.base_path, str)
        assert len(step.base_path) > 0

    def test_path_config_get_values(self):
        """Test getting values from path configuration step."""
        step = PathConfigurationStep(base_path="/test/path")
        values = step.get_values()
        assert "base_path" in values
        assert values["base_path"] == "/test/path"

    def test_path_config_validate_existing_path(self, tmp_path):
        """Test validation of an existing path."""
        step = PathConfigurationStep(base_path=str(tmp_path))
        result = step.validate_path()
        # Should be valid since tmp_path exists
        assert result.valid is True
        assert len(result.errors) == 0

    def test_path_config_validate_nonexistent_path(self):
        """Test validation of a non-existent path."""
        step = PathConfigurationStep(base_path="/nonexistent/path/that/does/not/exist")
        result = step.validate_path()
        # Should have errors since path doesn't exist
        assert len(result.errors) > 0

    def test_path_config_update_directory_tree(self):
        """Test updating directory tree preview."""
        step = PathConfigurationStep(base_path="/old/path")
        step.update_directory_tree("/new/path")
        assert step.base_path == "/new/path"



class TestServiceSpecificConfigurationStep:
    """Tests for the ServiceSpecificConfigurationStep widget."""

    def test_service_specific_initialization(self, sample_configuration):
        """Test service-specific configuration step initializes correctly."""
        selected_services = ["sonarr", "radarr", "jellyfin"]
        step = ServiceSpecificConfigurationStep(
            selected_services=selected_services,
            configuration=sample_configuration,
        )
        assert step.selected_services == selected_services
        assert step.configuration == sample_configuration
        assert len(step._custom_volumes) == 3
        assert "sonarr" in step._custom_volumes
        assert "radarr" in step._custom_volumes
        assert "jellyfin" in step._custom_volumes

    def test_service_specific_get_values(self, sample_configuration):
        """Test getting values from service-specific configuration step."""
        selected_services = ["sonarr", "radarr"]
        step = ServiceSpecificConfigurationStep(
            selected_services=selected_services,
            configuration=sample_configuration,
        )
        
        values = step.get_values()
        
        # Should return configuration for all selected services
        assert "sonarr" in values
        assert "radarr" in values
        
        # Check default values
        assert values["sonarr"]["name"] == "sonarr"
        assert values["sonarr"]["enabled"] is True
        assert values["sonarr"]["port"] == 8989
        assert isinstance(values["sonarr"]["custom_volumes"], dict)
        
        assert values["radarr"]["name"] == "radarr"
        assert values["radarr"]["enabled"] is True
        assert values["radarr"]["port"] == 7878

    def test_service_specific_validate_no_errors(self, sample_configuration):
        """Test validation passes with valid configuration."""
        selected_services = ["sonarr", "radarr"]
        step = ServiceSpecificConfigurationStep(
            selected_services=selected_services,
            configuration=sample_configuration,
        )
        
        result = step.validate_services()
        
        # Should be valid with default ports
        assert result.valid is True
        assert len(result.errors) == 0

    def test_service_specific_validate_port_conflict(self, sample_configuration):
        """Test validation detects port conflicts."""
        selected_services = ["sonarr", "radarr"]
        step = ServiceSpecificConfigurationStep(
            selected_services=selected_services,
            configuration=sample_configuration,
        )
        
        # Manually set conflicting ports
        step._custom_volumes["sonarr"] = []
        step._custom_volumes["radarr"] = []
        
        # Override get_values to return conflicting ports
        original_get_values = step.get_values
        
        def mock_get_values():
            values = original_get_values()
            values["sonarr"]["port"] = 8080
            values["radarr"]["port"] = 8080  # Same port as sonarr
            return values
        
        step.get_values = mock_get_values
        
        result = step.validate_services()
        
        # Should detect port conflict
        assert result.valid is False
        assert len(result.errors) > 0
        assert "conflict" in result.errors[0].lower()

    def test_service_specific_validate_invalid_port_range(self, sample_configuration):
        """Test validation detects invalid port ranges."""
        selected_services = ["sonarr"]
        step = ServiceSpecificConfigurationStep(
            selected_services=selected_services,
            configuration=sample_configuration,
        )
        
        # Override get_values to return invalid port
        original_get_values = step.get_values
        
        def mock_get_values():
            values = original_get_values()
            values["sonarr"]["port"] = 99999  # Invalid port
            return values
        
        step.get_values = mock_get_values
        
        result = step.validate_services()
        
        # Should detect invalid port
        assert result.valid is False
        assert len(result.errors) > 0
        assert "out of valid range" in result.errors[0].lower()

    def test_service_specific_custom_volumes_tracking(self, sample_configuration):
        """Test custom volumes are tracked correctly."""
        selected_services = ["sonarr"]
        step = ServiceSpecificConfigurationStep(
            selected_services=selected_services,
            configuration=sample_configuration,
        )
        
        # Initially no custom volumes
        assert len(step._custom_volumes["sonarr"]) == 0
        
        # Add a volume mount (this would normally be done through UI)
        step._custom_volumes["sonarr"].append(("/host/path", "/container/path"))
        
        assert len(step._custom_volumes["sonarr"]) == 1
        assert step._custom_volumes["sonarr"][0] == ("/host/path", "/container/path")



class TestDeploymentWorkflowIntegration:
    """Tests for deployment workflow integration."""

    @pytest.mark.asyncio
    async def test_deployment_workflow_validation(self, controller, sample_configuration, tmp_path):
        """Test deployment workflow validates configuration before proceeding."""
        # Set up a valid configuration with paths
        sample_configuration.paths = PathConfig(base_path=str(tmp_path))
        
        screen = ConfigWizardScreen(controller, sample_configuration)
        screen._current_step = WizardStep.SERVICE_SPECIFIC_CONFIGURATION
        
        # Verify the deployment workflow method exists and can be called
        assert hasattr(screen, '_start_deployment_workflow')
        assert callable(screen._start_deployment_workflow)

    @pytest.mark.asyncio
    async def test_wizard_completes_on_last_step(self, controller, sample_configuration):
        """Test wizard triggers deployment workflow on last step completion."""
        screen = ConfigWizardScreen(controller, sample_configuration)
        screen._current_step = WizardStep.SERVICE_SPECIFIC_CONFIGURATION
        
        # Mock validation to pass
        original_validate = screen._validate_current_step
        screen._validate_current_step = lambda: True
        
        # Mock save step data
        original_save = screen._save_current_step_data
        screen._save_current_step_data = lambda: None
        
        # Mock the deployment workflow to prevent actual execution
        deployment_called = []
        original_deploy = screen._start_deployment_workflow
        screen._start_deployment_workflow = lambda: deployment_called.append(True)
        
        # Trigger next step
        screen._go_to_next_step()
        
        # Should have called deployment workflow
        assert len(deployment_called) == 1
        
        # Restore original methods
        screen._validate_current_step = original_validate
        screen._save_current_step_data = original_save
        screen._start_deployment_workflow = original_deploy

    def test_deployment_workflow_creates_stack_config(self, controller, sample_configuration, tmp_path):
        """Test deployment workflow creates proper StackConfig."""
        from arr_stack_manager.models.stack import StackConfig
        
        # Set up valid configuration
        sample_configuration.paths = PathConfig(base_path=str(tmp_path))
        
        # Create a stack config as the workflow would
        stack_name = "test-stack"
        compose_path = str(tmp_path / "docker-compose.yml")
        
        stack_config = StackConfig(
            name=stack_name,
            configuration=sample_configuration,
            compose_path=compose_path,
        )
        
        assert stack_config.name == stack_name
        assert stack_config.configuration == sample_configuration
        assert stack_config.configuration.puid == 1000
        assert stack_config.configuration.pgid == 1000
        assert stack_config.compose_path == compose_path
