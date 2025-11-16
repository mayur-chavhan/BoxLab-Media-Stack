"""Tests for Docker Compose generator."""

import tempfile
from pathlib import Path

import pytest

from arr_stack_manager.core.generator import ComposeGenerator
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.stack import StackConfig


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    config = Configuration(
        puid=1000,
        pgid=1000,
        timezone="America/New_York",
        paths=PathConfig(base_path="/mnt/storage"),
    )

    # Add Sonarr service
    config.add_service(
        ServiceConfig(
            name="sonarr",
            enabled=True,
            port=8989,
        )
    )

    # Add Radarr service
    config.add_service(
        ServiceConfig(
            name="radarr",
            enabled=True,
            port=7878,
        )
    )

    return config


@pytest.fixture
def sample_stack(sample_config):
    """Create a sample stack configuration."""
    return StackConfig(
        name="test-stack",
        configuration=sample_config,
        compose_path="/tmp/test-stack",
    )


def test_generator_initialization():
    """Test ComposeGenerator initialization."""
    generator = ComposeGenerator()
    assert generator.template_dir.exists()
    assert generator.env is not None


def test_generate_compose_basic(sample_stack):
    """Test basic docker-compose.yml generation."""
    generator = ComposeGenerator()
    compose_content = generator.generate_compose(sample_stack)

    # Verify basic structure
    assert "version:" in compose_content
    assert "services:" in compose_content
    assert "sonarr:" in compose_content
    assert "radarr:" in compose_content

    # Verify environment variables
    assert "PUID=1000" in compose_content
    assert "PGID=1000" in compose_content
    assert "TZ=America/New_York" in compose_content

    # Verify Trash-Guides UMASK setting
    assert "UMASK=002" in compose_content


def test_generate_compose_no_services():
    """Test that generation fails with no services."""
    config = Configuration(
        puid=1000,
        pgid=1000,
        timezone="UTC",
        paths=PathConfig(base_path="/tmp"),
    )
    stack = StackConfig(
        name="empty-stack",
        configuration=config,
        compose_path="/tmp/empty",
    )

    generator = ComposeGenerator()
    with pytest.raises(ValueError, match="No services selected"):
        generator.generate_compose(stack)


def test_generate_env_file(sample_config):
    """Test .env file generation."""
    generator = ComposeGenerator()
    env_content = generator.generate_env_file(sample_config)

    # Verify basic variables
    assert "PUID=1000" in env_content
    assert "PGID=1000" in env_content
    assert "TZ=America/New_York" in env_content
    assert "CONFIG_PATH=/mnt/storage/config" in env_content
    assert "DATA_PATH=/mnt/storage/data" in env_content


def test_configure_volumes_sonarr(sample_config):
    """Test volume configuration for Sonarr with Trash-Guides structure."""
    generator = ComposeGenerator()
    volumes = generator.configure_volumes("sonarr", sample_config)

    # Should have config and data volumes
    assert len(volumes) >= 2

    # Check config volume
    config_vol = next(v for v in volumes if v["container_path"] == "/config")
    assert config_vol["host_path"] == "/mnt/storage/config/sonarr"
    assert config_vol["read_only"] is False

    # Check data volume (Trash-Guides: single mount point)
    data_vol = next(v for v in volumes if v["container_path"] == "/data")
    assert data_vol["host_path"] == "/mnt/storage/data"
    assert data_vol["read_only"] is False


def test_configure_volumes_jellyseerr(sample_config):
    """Test volume configuration for Jellyseerr (special case)."""
    sample_config.add_service(
        ServiceConfig(name="jellyseerr", enabled=True, port=5055)
    )

    generator = ComposeGenerator()
    volumes = generator.configure_volumes("jellyseerr", sample_config)

    # Jellyseerr uses /app/config
    assert len(volumes) == 1
    assert volumes[0]["container_path"] == "/app/config"
    assert volumes[0]["host_path"] == "/mnt/storage/config/jellyseerr"


def test_configure_volumes_custom(sample_config):
    """Test custom volume configuration."""
    sample_config.add_service(
        ServiceConfig(
            name="sonarr",
            enabled=True,
            port=8989,
            custom_volumes={"/custom/host": "/custom/container"},
        )
    )

    generator = ComposeGenerator()
    volumes = generator.configure_volumes("sonarr", sample_config)

    # Should include custom volume
    custom_vol = next(
        v for v in volumes if v["container_path"] == "/custom/container"
    )
    assert custom_vol["host_path"] == "/custom/host"


def test_apply_trash_guides_settings():
    """Test Trash-Guides settings application."""
    config = Configuration(
        puid=1000,
        pgid=1000,
        timezone="UTC",
        paths=PathConfig(base_path="/tmp"),
    )

    generator = ComposeGenerator()

    # Test for Sonarr (should have Trash-Guides settings)
    sonarr_settings = generator.apply_trash_guides_settings("sonarr", config)
    assert "environment" in sonarr_settings
    assert sonarr_settings["environment"]["UMASK"] == "002"

    # Test for Radarr (should have Trash-Guides settings)
    radarr_settings = generator.apply_trash_guides_settings("radarr", config)
    assert "environment" in radarr_settings
    assert radarr_settings["environment"]["UMASK"] == "002"

    # Test for service without Trash-Guides settings
    jellyfin_settings = generator.apply_trash_guides_settings("jellyfin", config)
    assert jellyfin_settings == {}


def test_save_to_disk(sample_stack):
    """Test saving generated files to disk."""
    generator = ComposeGenerator()

    with tempfile.TemporaryDirectory() as tmpdir:
        compose_content = generator.generate_compose(sample_stack)
        env_content = generator.generate_env_file(sample_stack.configuration)

        generator.save_to_disk(tmpdir, compose_content, env_content)

        # Verify files were created
        compose_file = Path(tmpdir) / "docker-compose.yml"
        env_file = Path(tmpdir) / ".env"

        assert compose_file.exists()
        assert env_file.exists()

        # Verify content
        assert compose_file.read_text() == compose_content
        assert env_file.read_text() == env_content


def test_generate_compose_with_custom_env_vars(sample_config):
    """Test compose generation with custom environment variables."""
    sample_config.services["sonarr"].environment_vars = {
        "CUSTOM_VAR": "custom_value"
    }

    stack = StackConfig(
        name="test-stack",
        configuration=sample_config,
        compose_path="/tmp/test",
    )

    generator = ComposeGenerator()
    compose_content = generator.generate_compose(stack)

    # Verify custom environment variable is included
    assert "CUSTOM_VAR=custom_value" in compose_content


def test_generate_compose_ports():
    """Test port mapping in generated compose file."""
    config = Configuration(
        puid=1000,
        pgid=1000,
        timezone="UTC",
        paths=PathConfig(base_path="/tmp"),
    )

    # Add service with custom port
    config.add_service(ServiceConfig(name="sonarr", enabled=True, port=9999))

    stack = StackConfig(
        name="test-stack",
        configuration=config,
        compose_path="/tmp/test",
    )

    generator = ComposeGenerator()
    compose_content = generator.generate_compose(stack)

    # Verify custom port is used
    assert "9999:8989" in compose_content


def test_generate_compose_network_name(sample_stack):
    """Test network name in generated compose file."""
    generator = ComposeGenerator()
    compose_content = generator.generate_compose(sample_stack)

    # Verify network configuration
    assert "networks:" in compose_content
    assert "test-stack-network" in compose_content
