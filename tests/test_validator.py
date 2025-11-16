"""Tests for configuration validator."""

import tempfile
from pathlib import Path

import pytest

from arr_stack_manager.core.validator import ConfigurationValidator
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.stack import StackConfig


class TestConfigurationValidator:
    """Test suite for ConfigurationValidator."""

    def test_validate_paths_valid(self):
        """Test path validation with valid paths."""
        validator = ConfigurationValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = PathConfig(base_path=tmpdir)
            result = validator.validate_paths(paths)

            assert result.valid is True
            assert len(result.errors) == 0

    def test_validate_paths_nonexistent(self):
        """Test path validation with nonexistent path."""
        validator = ConfigurationValidator()

        paths = PathConfig(base_path="/nonexistent/path/that/does/not/exist")
        result = validator.validate_paths(paths)

        assert result.valid is False
        assert len(result.errors) > 0
        assert "does not exist" in result.errors[0]

    def test_validate_ports_valid(self):
        """Test port validation with valid ports."""
        validator = ConfigurationValidator()

        result = validator.validate_ports([8080, 9090, 7878])

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_ports_duplicate(self):
        """Test port validation with duplicate ports."""
        validator = ConfigurationValidator()

        result = validator.validate_ports([8080, 8080, 9090])

        assert result.valid is False
        assert any("Duplicate port" in error for error in result.errors)

    def test_validate_ports_invalid_range(self):
        """Test port validation with invalid port range."""
        validator = ConfigurationValidator()

        result = validator.validate_ports([0, 70000])

        assert result.valid is False
        assert len(result.errors) >= 2

    def test_validate_permissions_valid(self):
        """Test permission validation with valid PUID/PGID."""
        validator = ConfigurationValidator()

        result = validator.validate_permissions(1000, 1000)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_permissions_negative(self):
        """Test permission validation with negative values."""
        validator = ConfigurationValidator()

        result = validator.validate_permissions(-1, -1)

        assert result.valid is False
        assert len(result.errors) >= 2

    def test_validate_docker(self):
        """Test Docker availability check."""
        validator = ConfigurationValidator()

        result = validator.validate_docker()

        # Result depends on whether Docker is available
        # Just check that it returns a ValidationResult
        assert result is not None
        assert isinstance(result.valid, bool)

    def test_validate_service_config_valid(self):
        """Test service configuration validation with valid config."""
        validator = ConfigurationValidator()

        result = validator.validate_service_config(
            "sonarr", {"port": 8989, "custom_volumes": {"/host": "/container"}}
        )

        assert result.valid is True

    def test_validate_service_config_unsupported(self):
        """Test service configuration validation with unsupported service."""
        validator = ConfigurationValidator()

        result = validator.validate_service_config("invalid_service", {})

        assert result.valid is False
        assert any("Unsupported service" in error for error in result.errors)

    def test_validate_complete_stack(self):
        """Test complete stack validation."""
        validator = ConfigurationValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(
                puid=1000,
                pgid=1000,
                timezone="UTC",
                paths=PathConfig(base_path=tmpdir),
                services={
                    "sonarr": ServiceConfig(name="sonarr", port=8989),
                    "radarr": ServiceConfig(name="radarr", port=7878),
                },
            )

            stack = StackConfig(
                name="test-stack", configuration=config, compose_path="/tmp/docker-compose.yml"
            )

            result = validator.validate_complete_stack(stack)

            # Should have warnings but may be valid depending on Docker availability
            assert result is not None
            assert len(result.errors) == 0 or not result.valid

    def test_validate_complete_stack_no_services(self):
        """Test complete stack validation with no enabled services."""
        validator = ConfigurationValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(
                puid=1000, pgid=1000, timezone="UTC", paths=PathConfig(base_path=tmpdir), services={}
            )

            stack = StackConfig(
                name="test-stack", configuration=config, compose_path="/tmp/docker-compose.yml"
            )

            result = validator.validate_complete_stack(stack)

            assert result.valid is False
            assert any("No services are enabled" in error for error in result.errors)
