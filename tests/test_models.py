"""Tests for data models."""

import pytest
from pydantic import ValidationError

from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.service import ResourceMetrics, ServiceInfo, ServiceStatus
from arr_stack_manager.models.stack import StackConfig
from arr_stack_manager.models.validation import DeploymentEvent, OperationResult, ValidationResult


class TestPathConfig:
    """Test suite for PathConfig model."""

    def test_path_config_creation(self):
        """Test creating a PathConfig with base path."""
        config = PathConfig(base_path="/mnt/storage")

        assert config.base_path == "/mnt/storage"
        assert config.config_path == "/mnt/storage/config"
        assert config.data_path == "/mnt/storage/data"

    def test_path_config_explicit_paths(self):
        """Test creating PathConfig with explicit paths."""
        config = PathConfig(
            base_path="/mnt/storage",
            config_path="/custom/config",
            data_path="/custom/data",
        )

        assert config.base_path == "/mnt/storage"
        assert config.config_path == "/custom/config"
        assert config.data_path == "/custom/data"

    def test_path_config_empty_base_path(self):
        """Test that empty base path raises validation error."""
        with pytest.raises(ValidationError):
            PathConfig(base_path="")

    def test_path_config_whitespace_base_path(self):
        """Test that whitespace-only base path raises validation error."""
        with pytest.raises(ValidationError):
            PathConfig(base_path="   ")

    def test_path_config_strips_whitespace(self):
        """Test that base path whitespace is stripped."""
        config = PathConfig(base_path="  /mnt/storage  ")

        assert config.base_path == "/mnt/storage"


class TestServiceConfig:
    """Test suite for ServiceConfig model."""

    def test_service_config_creation(self):
        """Test creating a ServiceConfig."""
        config = ServiceConfig(name="sonarr", port=8989)

        assert config.name == "sonarr"
        assert config.enabled is True
        assert config.port == 8989
        assert config.custom_volumes == {}
        assert config.environment_vars == {}

    def test_service_config_disabled(self):
        """Test creating a disabled service."""
        config = ServiceConfig(name="radarr", port=7878, enabled=False)

        assert config.enabled is False

    def test_service_config_custom_volumes(self):
        """Test service with custom volumes."""
        config = ServiceConfig(
            name="sonarr",
            port=8989,
            custom_volumes={"/host/path": "/container/path"},
        )

        assert config.custom_volumes == {"/host/path": "/container/path"}

    def test_service_config_environment_vars(self):
        """Test service with environment variables."""
        config = ServiceConfig(
            name="sonarr",
            port=8989,
            environment_vars={"CUSTOM_VAR": "value"},
        )

        assert config.environment_vars == {"CUSTOM_VAR": "value"}

    def test_service_config_empty_name(self):
        """Test that empty service name raises validation error."""
        with pytest.raises(ValidationError):
            ServiceConfig(name="", port=8989)

    def test_service_config_name_lowercase(self):
        """Test that service name is converted to lowercase."""
        config = ServiceConfig(name="SONARR", port=8989)

        assert config.name == "sonarr"

    def test_service_config_invalid_port_zero(self):
        """Test that port 0 raises validation error."""
        with pytest.raises(ValidationError):
            ServiceConfig(name="sonarr", port=0)

    def test_service_config_invalid_port_negative(self):
        """Test that negative port raises validation error."""
        with pytest.raises(ValidationError):
            ServiceConfig(name="sonarr", port=-1)

    def test_service_config_invalid_port_too_high(self):
        """Test that port > 65535 raises validation error."""
        with pytest.raises(ValidationError):
            ServiceConfig(name="sonarr", port=70000)


class TestConfiguration:
    """Test suite for Configuration model."""

    def test_configuration_creation(self):
        """Test creating a Configuration."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            timezone="America/New_York",
            paths=PathConfig(base_path="/mnt/storage"),
        )

        assert config.puid == 1000
        assert config.pgid == 1000
        assert config.timezone == "America/New_York"
        assert config.paths.base_path == "/mnt/storage"
        assert config.services == {}

    def test_configuration_default_timezone(self):
        """Test that default timezone is UTC."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        assert config.timezone == "UTC"

    def test_configuration_negative_puid(self):
        """Test that negative PUID raises validation error."""
        with pytest.raises(ValidationError):
            Configuration(
                puid=-1,
                pgid=1000,
                paths=PathConfig(base_path="/tmp"),
            )

    def test_configuration_negative_pgid(self):
        """Test that negative PGID raises validation error."""
        with pytest.raises(ValidationError):
            Configuration(
                puid=1000,
                pgid=-1,
                paths=PathConfig(base_path="/tmp"),
            )

    def test_configuration_empty_timezone(self):
        """Test that empty timezone raises validation error."""
        with pytest.raises(ValidationError):
            Configuration(
                puid=1000,
                pgid=1000,
                timezone="",
                paths=PathConfig(base_path="/tmp"),
            )

    def test_add_service(self):
        """Test adding a service to configuration."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        service = ServiceConfig(name="sonarr", port=8989)
        config.add_service(service)

        assert "sonarr" in config.services
        assert config.services["sonarr"].port == 8989

    def test_add_service_updates_existing(self):
        """Test that adding a service updates existing one."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        service1 = ServiceConfig(name="sonarr", port=8989)
        config.add_service(service1)

        service2 = ServiceConfig(name="sonarr", port=9999)
        config.add_service(service2)

        assert config.services["sonarr"].port == 9999

    def test_remove_service(self):
        """Test removing a service from configuration."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        service = ServiceConfig(name="sonarr", port=8989)
        config.add_service(service)
        config.remove_service("sonarr")

        assert "sonarr" not in config.services

    def test_remove_nonexistent_service(self):
        """Test that removing nonexistent service doesn't raise error."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        config.remove_service("nonexistent")  # Should not raise

    def test_get_service(self):
        """Test getting a service from configuration."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        service = ServiceConfig(name="sonarr", port=8989)
        config.add_service(service)

        retrieved = config.get_service("sonarr")
        assert retrieved is not None
        assert retrieved.name == "sonarr"

    def test_get_nonexistent_service(self):
        """Test getting a nonexistent service returns None."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        retrieved = config.get_service("nonexistent")
        assert retrieved is None

    def test_get_selected_services(self):
        """Test getting list of enabled services."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        config.add_service(ServiceConfig(name="sonarr", port=8989, enabled=True))
        config.add_service(ServiceConfig(name="radarr", port=7878, enabled=True))
        config.add_service(ServiceConfig(name="bazarr", port=6767, enabled=False))

        selected = config.get_selected_services()

        assert len(selected) == 2
        assert "sonarr" in selected
        assert "radarr" in selected
        assert "bazarr" not in selected

    def test_from_env_with_all_values(self):
        """Test creating Configuration from environment variables."""
        from unittest.mock import Mock

        # Create mock environment loader
        env_loader = Mock()
        env_loader.get.side_effect = lambda key: {
            "PUID": 1001,
            "PGID": 1001,
            "TZ": "America/Los_Angeles",
            "BASE_PATH": "/mnt/media",
            "CONFIG_PATH": "/mnt/media/configs",
            "DATA_PATH": "/mnt/media/data",
        }.get(key)

        config = Configuration.from_env(env_loader)

        assert config.puid == 1001
        assert config.pgid == 1001
        assert config.timezone == "America/Los_Angeles"
        assert config.paths.base_path == "/mnt/media"
        assert config.paths.config_path == "/mnt/media/configs"
        assert config.paths.data_path == "/mnt/media/data"

    def test_from_env_with_defaults(self):
        """Test creating Configuration from environment with defaults."""
        import os
        from unittest.mock import Mock

        # Create mock environment loader that returns None for PUID/PGID
        env_loader = Mock()
        env_loader.get.side_effect = lambda key: {
            "BASE_PATH": "/mnt/storage",
        }.get(key)

        config = Configuration.from_env(env_loader)

        # Should use current user's UID/GID
        assert config.puid == os.getuid()
        assert config.pgid == os.getgid()
        assert config.timezone == "UTC"
        assert config.paths.base_path == "/mnt/storage"

    def test_from_env_timezone_alternative(self):
        """Test that TIMEZONE env var works as alternative to TZ."""
        from unittest.mock import Mock

        env_loader = Mock()
        env_loader.get.side_effect = lambda key: {
            "BASE_PATH": "/mnt/storage",
            "TIMEZONE": "Europe/London",
        }.get(key)

        config = Configuration.from_env(env_loader)

        assert config.timezone == "Europe/London"

    def test_from_env_missing_base_path(self):
        """Test that from_env raises error when BASE_PATH is missing."""
        from unittest.mock import Mock

        env_loader = Mock()
        env_loader.get.return_value = None

        with pytest.raises(ValueError, match="BASE_PATH environment variable is required"):
            Configuration.from_env(env_loader)

    def test_merge_with_env_overrides_all(self):
        """Test merging configuration with environment variables."""
        from unittest.mock import Mock

        # Create initial configuration
        config = Configuration(
            puid=1000,
            pgid=1000,
            timezone="UTC",
            paths=PathConfig(base_path="/tmp"),
        )

        # Add a service
        config.add_service(ServiceConfig(name="sonarr", port=8989))

        # Create mock environment loader with override values
        env_loader = Mock()
        env_loader.get.side_effect = lambda key: {
            "PUID": 2000,
            "PGID": 2000,
            "TZ": "America/New_York",
            "BASE_PATH": "/mnt/storage",
            "CONFIG_PATH": "/mnt/storage/config",
            "DATA_PATH": "/mnt/storage/data",
        }.get(key)

        merged = config.merge_with_env(env_loader)

        # Check that environment values override
        assert merged.puid == 2000
        assert merged.pgid == 2000
        assert merged.timezone == "America/New_York"
        assert merged.paths.base_path == "/mnt/storage"
        assert merged.paths.config_path == "/mnt/storage/config"
        assert merged.paths.data_path == "/mnt/storage/data"

        # Check that services are preserved
        assert "sonarr" in merged.services
        assert merged.services["sonarr"].port == 8989

    def test_merge_with_env_partial_override(self):
        """Test merging with only some environment variables set."""
        from unittest.mock import Mock

        config = Configuration(
            puid=1000,
            pgid=1000,
            timezone="UTC",
            paths=PathConfig(base_path="/tmp"),
        )

        # Only override PUID and timezone
        env_loader = Mock()
        env_loader.get.side_effect = lambda key: {
            "PUID": 1500,
            "TZ": "Europe/Paris",
        }.get(key)

        merged = config.merge_with_env(env_loader)

        # Check that only specified values are overridden
        assert merged.puid == 1500
        assert merged.pgid == 1000  # Not overridden
        assert merged.timezone == "Europe/Paris"
        assert merged.paths.base_path == "/tmp"  # Not overridden

    def test_merge_with_env_no_overrides(self):
        """Test merging when no environment variables are set."""
        from unittest.mock import Mock

        config = Configuration(
            puid=1000,
            pgid=1000,
            timezone="UTC",
            paths=PathConfig(base_path="/tmp"),
        )

        # No environment variables set
        env_loader = Mock()
        env_loader.get.return_value = None

        merged = config.merge_with_env(env_loader)

        # All values should remain the same
        assert merged.puid == 1000
        assert merged.pgid == 1000
        assert merged.timezone == "UTC"
        assert merged.paths.base_path == "/tmp"


class TestValidationResult:
    """Test suite for ValidationResult model."""

    def test_validation_result_valid(self):
        """Test creating a valid ValidationResult."""
        result = ValidationResult(valid=True)

        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []
        assert not result.has_errors
        assert not result.has_warnings

    def test_validation_result_with_errors(self):
        """Test ValidationResult with errors."""
        result = ValidationResult(valid=False, errors=["Error 1", "Error 2"])

        assert result.valid is False
        assert len(result.errors) == 2
        assert result.has_errors

    def test_validation_result_with_warnings(self):
        """Test ValidationResult with warnings."""
        result = ValidationResult(valid=True, warnings=["Warning 1"])

        assert result.valid is True
        assert len(result.warnings) == 1
        assert result.has_warnings

    def test_add_error(self):
        """Test adding an error to ValidationResult."""
        result = ValidationResult(valid=True)
        result.add_error("New error")

        assert result.valid is False
        assert "New error" in result.errors
        assert result.has_errors

    def test_add_warning(self):
        """Test adding a warning to ValidationResult."""
        result = ValidationResult(valid=True)
        result.add_warning("New warning")

        assert result.valid is True
        assert "New warning" in result.warnings
        assert result.has_warnings

    def test_merge_results(self):
        """Test merging two ValidationResults."""
        result1 = ValidationResult(valid=True, warnings=["Warning 1"])
        result2 = ValidationResult(valid=False, errors=["Error 1"], warnings=["Warning 2"])

        result1.merge(result2)

        assert result1.valid is False
        assert len(result1.errors) == 1
        assert len(result1.warnings) == 2

    def test_get_summary_valid(self):
        """Test summary for valid result."""
        result = ValidationResult(valid=True)

        assert result.get_summary() == "Validation passed"

    def test_get_summary_valid_with_warnings(self):
        """Test summary for valid result with warnings."""
        result = ValidationResult(valid=True, warnings=["Warning 1", "Warning 2"])

        summary = result.get_summary()
        assert "2 warning(s)" in summary

    def test_get_summary_invalid(self):
        """Test summary for invalid result."""
        result = ValidationResult(valid=False, errors=["Error 1", "Error 2", "Error 3"])

        summary = result.get_summary()
        assert "3 error(s)" in summary


class TestOperationResult:
    """Test suite for OperationResult model."""

    def test_operation_result_success(self):
        """Test creating a successful OperationResult."""
        result = OperationResult(success=True, message="Operation completed")

        assert result.success is True
        assert result.message == "Operation completed"
        assert result.details is None

    def test_operation_result_failure(self):
        """Test creating a failed OperationResult."""
        result = OperationResult(success=False, message="Operation failed")

        assert result.success is False
        assert result.message == "Operation failed"

    def test_operation_result_with_details(self):
        """Test OperationResult with details."""
        result = OperationResult(
            success=True,
            message="Operation completed",
            details="Additional information",
        )

        assert result.details == "Additional information"

    def test_success_result_factory(self):
        """Test creating success result with factory method."""
        result = OperationResult.success_result("Success message")

        assert result.success is True
        assert result.message == "Success message"

    def test_failure_result_factory(self):
        """Test creating failure result with factory method."""
        result = OperationResult.failure_result("Failure message", "Error details")

        assert result.success is False
        assert result.message == "Failure message"
        assert result.details == "Error details"

    def test_get_full_message_without_details(self):
        """Test getting full message without details."""
        result = OperationResult(success=True, message="Test message")

        assert result.get_full_message() == "Test message"

    def test_get_full_message_with_details(self):
        """Test getting full message with details."""
        result = OperationResult(
            success=True,
            message="Test message",
            details="Extra details",
        )

        full_message = result.get_full_message()
        assert "Test message" in full_message
        assert "Extra details" in full_message


class TestResourceMetrics:
    """Test suite for ResourceMetrics model."""

    def test_resource_metrics_creation(self):
        """Test creating ResourceMetrics."""
        metrics = ResourceMetrics(
            cpu_percent=25.5,
            memory_usage=1024 * 1024 * 100,  # 100MB
            memory_limit=1024 * 1024 * 512,  # 512MB
        )

        assert metrics.cpu_percent == 25.5
        assert metrics.memory_usage == 1024 * 1024 * 100
        assert metrics.memory_limit == 1024 * 1024 * 512
        assert metrics.network_rx == 0
        assert metrics.network_tx == 0

    def test_resource_metrics_with_network(self):
        """Test ResourceMetrics with network stats."""
        metrics = ResourceMetrics(
            cpu_percent=10.0,
            memory_usage=1024,
            memory_limit=2048,
            network_rx=1000,
            network_tx=2000,
        )

        assert metrics.network_rx == 1000
        assert metrics.network_tx == 2000

    def test_memory_percent_calculation(self):
        """Test memory percentage calculation."""
        metrics = ResourceMetrics(
            cpu_percent=10.0,
            memory_usage=1024 * 1024 * 256,  # 256MB
            memory_limit=1024 * 1024 * 512,  # 512MB
        )

        assert metrics.memory_percent == 50.0

    def test_memory_percent_zero_limit(self):
        """Test memory percentage with zero limit."""
        metrics = ResourceMetrics(
            cpu_percent=10.0,
            memory_usage=1024,
            memory_limit=0,
        )

        assert metrics.memory_percent == 0.0

    def test_format_memory(self):
        """Test formatting memory as human-readable string."""
        metrics = ResourceMetrics(
            cpu_percent=10.0,
            memory_usage=1024 * 1024 * 145,  # 145MB
            memory_limit=1024 * 1024 * 512,  # 512MB
        )

        formatted = metrics.format_memory()
        assert "145MB" in formatted
        assert "512MB" in formatted

    def test_invalid_cpu_percent_negative(self):
        """Test that negative CPU percent raises validation error."""
        with pytest.raises(ValidationError):
            ResourceMetrics(
                cpu_percent=-1.0,
                memory_usage=1024,
                memory_limit=2048,
            )

    def test_invalid_cpu_percent_too_high(self):
        """Test that CPU percent > 100 raises validation error."""
        with pytest.raises(ValidationError):
            ResourceMetrics(
                cpu_percent=150.0,
                memory_usage=1024,
                memory_limit=2048,
            )

    def test_invalid_memory_negative(self):
        """Test that negative memory raises validation error."""
        with pytest.raises(ValidationError):
            ResourceMetrics(
                cpu_percent=10.0,
                memory_usage=-1,
                memory_limit=2048,
            )


class TestServiceInfo:
    """Test suite for ServiceInfo model."""

    def test_service_info_creation(self):
        """Test creating ServiceInfo."""
        info = ServiceInfo(
            name="sonarr",
            status=ServiceStatus.RUNNING,
            image="lscr.io/linuxserver/sonarr:latest",
        )

        assert info.name == "sonarr"
        assert info.status == ServiceStatus.RUNNING
        assert info.image == "lscr.io/linuxserver/sonarr:latest"
        assert info.container_id is None
        assert info.uptime is None
        assert info.web_ui_url is None
        assert info.metrics is None
        assert info.update_available is False

    def test_service_info_with_all_fields(self):
        """Test ServiceInfo with all fields."""
        metrics = ResourceMetrics(
            cpu_percent=10.0,
            memory_usage=1024 * 1024 * 100,
            memory_limit=1024 * 1024 * 512,
        )

        info = ServiceInfo(
            name="sonarr",
            status=ServiceStatus.RUNNING,
            container_id="abc123",
            image="lscr.io/linuxserver/sonarr:latest",
            uptime=3600,
            web_ui_url="http://localhost:8989",
            metrics=metrics,
            update_available=True,
        )

        assert info.container_id == "abc123"
        assert info.uptime == 3600
        assert info.web_ui_url == "http://localhost:8989"
        assert info.metrics is not None
        assert info.update_available is True

    def test_format_uptime_none(self):
        """Test formatting uptime when None."""
        info = ServiceInfo(
            name="sonarr",
            status=ServiceStatus.STOPPED,
            image="lscr.io/linuxserver/sonarr:latest",
        )

        assert info.format_uptime() == "N/A"

    def test_format_uptime_minutes(self):
        """Test formatting uptime in minutes."""
        info = ServiceInfo(
            name="sonarr",
            status=ServiceStatus.RUNNING,
            image="lscr.io/linuxserver/sonarr:latest",
            uptime=300,  # 5 minutes
        )

        assert info.format_uptime() == "5m"

    def test_format_uptime_hours(self):
        """Test formatting uptime in hours and minutes."""
        info = ServiceInfo(
            name="sonarr",
            status=ServiceStatus.RUNNING,
            image="lscr.io/linuxserver/sonarr:latest",
            uptime=7200,  # 2 hours
        )

        formatted = info.format_uptime()
        assert "2h" in formatted

    def test_format_uptime_days(self):
        """Test formatting uptime in days, hours, and minutes."""
        info = ServiceInfo(
            name="sonarr",
            status=ServiceStatus.RUNNING,
            image="lscr.io/linuxserver/sonarr:latest",
            uptime=90061,  # 1 day, 1 hour, 1 minute
        )

        formatted = info.format_uptime()
        assert "1d" in formatted
        assert "1h" in formatted
        assert "1m" in formatted

    def test_is_running_property(self):
        """Test is_running property."""
        info = ServiceInfo(
            name="sonarr",
            status=ServiceStatus.RUNNING,
            image="lscr.io/linuxserver/sonarr:latest",
        )

        assert info.is_running is True

    def test_is_stopped_property(self):
        """Test is_stopped property."""
        info = ServiceInfo(
            name="sonarr",
            status=ServiceStatus.STOPPED,
            image="lscr.io/linuxserver/sonarr:latest",
        )

        assert info.is_stopped is True

    def test_is_running_false_when_stopped(self):
        """Test is_running is False when stopped."""
        info = ServiceInfo(
            name="sonarr",
            status=ServiceStatus.STOPPED,
            image="lscr.io/linuxserver/sonarr:latest",
        )

        assert info.is_running is False


class TestDeploymentEvent:
    """Test suite for DeploymentEvent model."""

    def test_deployment_event_creation(self):
        """Test creating a DeploymentEvent."""
        from datetime import datetime

        now = datetime.now()
        event = DeploymentEvent(
            timestamp=now,
            stage="pulling_images",
            message="Pulling container images",
            progress=0.5,
        )

        assert event.timestamp == now
        assert event.stage == "pulling_images"
        assert event.message == "Pulling container images"
        assert event.progress == 0.5

    def test_deployment_event_create_factory(self):
        """Test creating DeploymentEvent with factory method."""
        event = DeploymentEvent.create(
            stage="starting_services",
            message="Starting containers",
            progress=0.75,
        )

        assert event.stage == "starting_services"
        assert event.message == "Starting containers"
        assert event.progress == 0.75
        assert event.timestamp is not None

    def test_deployment_event_invalid_progress_negative(self):
        """Test that negative progress raises validation error."""
        from datetime import datetime

        with pytest.raises(ValidationError):
            DeploymentEvent(
                timestamp=datetime.now(),
                stage="test",
                message="test",
                progress=-0.1,
            )

    def test_deployment_event_invalid_progress_too_high(self):
        """Test that progress > 1.0 raises validation error."""
        from datetime import datetime

        with pytest.raises(ValidationError):
            DeploymentEvent(
                timestamp=datetime.now(),
                stage="test",
                message="test",
                progress=1.5,
            )


class TestStackConfig:
    """Test suite for StackConfig model."""

    def test_stack_config_creation(self):
        """Test creating a StackConfig."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        stack = StackConfig(
            name="test-stack",
            configuration=config,
            compose_path="/tmp/docker-compose.yml",
        )

        assert stack.name == "test-stack"
        assert stack.configuration.puid == 1000
        assert stack.compose_path == "/tmp/docker-compose.yml"
        assert stack.created_at is not None
        assert stack.last_modified is not None

    def test_stack_config_timestamps(self):
        """Test that timestamps are set automatically."""
        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        stack = StackConfig(
            name="test-stack",
            configuration=config,
            compose_path="/tmp/docker-compose.yml",
        )

        assert stack.created_at <= stack.last_modified

    def test_update_modified_time(self):
        """Test updating the modified timestamp."""
        import time

        config = Configuration(
            puid=1000,
            pgid=1000,
            paths=PathConfig(base_path="/tmp"),
        )

        stack = StackConfig(
            name="test-stack",
            configuration=config,
            compose_path="/tmp/docker-compose.yml",
        )

        original_modified = stack.last_modified
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        stack.update_modified_time()

        assert stack.last_modified > original_modified


class TestStackStatus:
    """Test suite for StackStatus model."""

    def test_stack_status_creation(self):
        """Test creating a StackStatus."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=4,
            stopped_services=1,
            error_services=0,
        )

        assert status.name == "test-stack"
        assert status.total_services == 5
        assert status.running_services == 4
        assert status.stopped_services == 1
        assert status.error_services == 0
        assert status.last_updated is not None

    def test_is_healthy_all_running(self):
        """Test is_healthy when all services are running."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=5,
            stopped_services=0,
            error_services=0,
        )

        assert status.is_healthy is True

    def test_is_healthy_with_stopped(self):
        """Test is_healthy when some services are stopped."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=4,
            stopped_services=1,
            error_services=0,
        )

        assert status.is_healthy is False

    def test_is_healthy_with_errors(self):
        """Test is_healthy when services have errors."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=4,
            stopped_services=0,
            error_services=1,
        )

        assert status.is_healthy is False

    def test_has_errors_true(self):
        """Test has_errors when errors exist."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=3,
            stopped_services=1,
            error_services=1,
        )

        assert status.has_errors is True

    def test_has_errors_false(self):
        """Test has_errors when no errors exist."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=4,
            stopped_services=1,
            error_services=0,
        )

        assert status.has_errors is False

    def test_get_status_summary_healthy(self):
        """Test status summary when healthy."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=5,
            stopped_services=0,
            error_services=0,
        )

        summary = status.get_status_summary()
        assert "Running" in summary
        assert "5/5" in summary

    def test_get_status_summary_with_errors(self):
        """Test status summary when errors exist."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=3,
            stopped_services=1,
            error_services=1,
        )

        summary = status.get_status_summary()
        assert "Error" in summary
        assert "1" in summary

    def test_get_status_summary_all_stopped(self):
        """Test status summary when all services are stopped."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=0,
            stopped_services=5,
            error_services=0,
        )

        summary = status.get_status_summary()
        assert "Stopped" in summary

    def test_get_status_summary_partial(self):
        """Test status summary when partially running."""
        from arr_stack_manager.models.stack import StackStatus

        status = StackStatus(
            name="test-stack",
            total_services=5,
            running_services=3,
            stopped_services=2,
            error_services=0,
        )

        summary = status.get_status_summary()
        assert "Partial" in summary
        assert "3/5" in summary

    def test_invalid_negative_services(self):
        """Test that negative service counts raise validation error."""
        from arr_stack_manager.models.stack import StackStatus

        with pytest.raises(ValidationError):
            StackStatus(
                name="test-stack",
                total_services=-1,
                running_services=0,
                stopped_services=0,
                error_services=0,
            )
