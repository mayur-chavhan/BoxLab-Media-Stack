"""Tests for configuration storage and persistence."""

import json
import tempfile
from pathlib import Path

import pytest

from arr_stack_manager.core.config_store import ConfigRepository
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.stack import StackConfig


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
            "sonarr": ServiceConfig(name="sonarr", port=8989),
            "radarr": ServiceConfig(name="radarr", port=7878),
        },
    )
    return StackConfig(
        name="test-stack",
        configuration=config,
        compose_path="/tmp/docker-compose.yml",
    )


def test_get_config_dir():
    """Test that get_config_dir returns the correct path."""
    config_dir = ConfigRepository.get_config_dir()
    expected = Path.home() / ".config" / "arr-stack-manager"
    assert config_dir == expected


def test_init_creates_directory_structure(temp_config_dir):
    """Test that initialization creates the required directory structure."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    assert temp_config_dir.exists()
    assert (temp_config_dir / "stacks").exists()
    assert (temp_config_dir / "backups").exists()


def test_save_and_load(temp_config_dir, sample_stack_config):
    """Test saving and loading a stack configuration."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    # Save the configuration
    repo.save(sample_stack_config)

    # Verify file was created
    stack_file = temp_config_dir / "stacks" / "test-stack.json"
    assert stack_file.exists()

    # Load the configuration
    loaded_config = repo.load("test-stack")

    # Verify loaded data matches original
    assert loaded_config.name == sample_stack_config.name
    assert loaded_config.configuration.puid == sample_stack_config.configuration.puid
    assert loaded_config.configuration.pgid == sample_stack_config.configuration.pgid
    assert loaded_config.configuration.timezone == sample_stack_config.configuration.timezone
    assert len(loaded_config.configuration.services) == 2


def test_save_updates_modified_time(temp_config_dir, sample_stack_config):
    """Test that saving updates the last_modified timestamp."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    original_modified = sample_stack_config.last_modified
    repo.save(sample_stack_config)

    loaded_config = repo.load("test-stack")
    assert loaded_config.last_modified >= original_modified


def test_list_stacks(temp_config_dir, sample_stack_config):
    """Test listing all stack configurations."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    # Initially empty
    assert repo.list_stacks() == []

    # Save a stack
    repo.save(sample_stack_config)
    assert repo.list_stacks() == ["test-stack"]

    # Save another stack
    sample_stack_config.name = "another-stack"
    repo.save(sample_stack_config)
    stacks = repo.list_stacks()
    assert len(stacks) == 2
    assert "test-stack" in stacks
    assert "another-stack" in stacks


def test_exists(temp_config_dir, sample_stack_config):
    """Test checking if a stack configuration exists."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    assert not repo.exists("test-stack")

    repo.save(sample_stack_config)
    assert repo.exists("test-stack")


def test_delete(temp_config_dir, sample_stack_config):
    """Test deleting a stack configuration."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    repo.save(sample_stack_config)
    assert repo.exists("test-stack")

    repo.delete("test-stack")
    assert not repo.exists("test-stack")


def test_delete_nonexistent_raises_error(temp_config_dir):
    """Test that deleting a nonexistent stack raises FileNotFoundError."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    with pytest.raises(FileNotFoundError):
        repo.delete("nonexistent-stack")


def test_load_nonexistent_raises_error(temp_config_dir):
    """Test that loading a nonexistent stack raises FileNotFoundError."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    with pytest.raises(FileNotFoundError):
        repo.load("nonexistent-stack")


def test_backup(temp_config_dir, sample_stack_config):
    """Test creating a backup of a stack configuration."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    repo.save(sample_stack_config)
    backup_path = repo.backup("test-stack")

    assert backup_path.exists()
    assert backup_path.parent == temp_config_dir / "backups"
    assert "test-stack" in backup_path.name


def test_restore_from_backup(temp_config_dir, sample_stack_config):
    """Test restoring a stack configuration from a backup."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    # Save and backup
    repo.save(sample_stack_config)
    backup_path = repo.backup("test-stack")

    # Delete original
    repo.delete("test-stack")
    assert not repo.exists("test-stack")

    # Restore from backup
    repo.restore_from_backup(backup_path)
    assert repo.exists("test-stack")

    # Verify restored data
    restored = repo.load("test-stack")
    assert restored.name == sample_stack_config.name


def test_restore_with_new_name(temp_config_dir, sample_stack_config):
    """Test restoring a backup with a different name."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    repo.save(sample_stack_config)
    backup_path = repo.backup("test-stack")

    # Restore with new name
    repo.restore_from_backup(backup_path, stack_name="restored-stack")
    assert repo.exists("restored-stack")

    restored = repo.load("restored-stack")
    assert restored.name == "restored-stack"


def test_get_stack_metadata(temp_config_dir, sample_stack_config):
    """Test getting stack metadata without loading full configuration."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    repo.save(sample_stack_config)
    metadata = repo.get_stack_metadata("test-stack")

    assert metadata["name"] == "test-stack"
    assert "created_at" in metadata
    assert "last_modified" in metadata
    assert metadata["file_size"] > 0
    assert metadata["service_count"] == 2


def test_save_invalid_stack_name_raises_error(temp_config_dir, sample_stack_config):
    """Test that saving with an empty stack name raises ValueError."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    sample_stack_config.name = ""
    with pytest.raises(ValueError):
        repo.save(sample_stack_config)


def test_sanitizes_stack_name(temp_config_dir, sample_stack_config):
    """Test that stack names are sanitized to prevent directory traversal."""
    repo = ConfigRepository(config_dir=temp_config_dir)

    sample_stack_config.name = "../../../etc/passwd"
    repo.save(sample_stack_config)

    # Should create a safe filename
    stack_file = temp_config_dir / "stacks" / "etcpasswd.json"
    assert stack_file.exists()
