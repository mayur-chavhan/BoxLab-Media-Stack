"""Tests for Docker manager operations."""

import pytest
from docker.errors import DockerException

from arr_stack_manager.core.docker_manager import DockerManager
from arr_stack_manager.models.service import ServiceStatus


@pytest.fixture
def docker_manager():
    """Create a DockerManager instance for testing."""
    try:
        manager = DockerManager()
        return manager
    except DockerException:
        pytest.skip("Docker daemon not available")


def test_docker_manager_initialization():
    """Test that DockerManager initializes successfully with Docker available."""
    try:
        manager = DockerManager()
        assert manager is not None
        assert manager.is_docker_available()
    except DockerException:
        pytest.skip("Docker daemon not available")


def test_docker_manager_initialization_fails_without_docker(monkeypatch):
    """Test that DockerManager raises exception when Docker is unavailable."""
    import docker

    def mock_from_env():
        raise DockerException("Cannot connect")

    monkeypatch.setattr(docker, "from_env", mock_from_env)

    with pytest.raises(DockerException):
        DockerManager()


def test_is_docker_available(docker_manager):
    """Test checking Docker availability."""
    assert docker_manager.is_docker_available() is True


def test_get_docker_version(docker_manager):
    """Test getting Docker version."""
    version = docker_manager.get_docker_version()
    assert version is not None
    assert isinstance(version, str)


def test_get_service_status_nonexistent(docker_manager):
    """Test getting status of a nonexistent service."""
    service_info = docker_manager.get_service_status("nonexistent-service-12345")

    assert service_info.name == "nonexistent-service-12345"
    assert service_info.status == ServiceStatus.UNKNOWN
    assert service_info.container_id is None


def test_start_service_nonexistent(docker_manager):
    """Test starting a nonexistent service returns failure."""
    result = docker_manager.start_service("nonexistent-service-12345")

    assert result.success is False
    assert "not found" in result.message.lower()


def test_stop_service_nonexistent(docker_manager):
    """Test stopping a nonexistent service returns failure."""
    result = docker_manager.stop_service("nonexistent-service-12345")

    assert result.success is False
    assert "not found" in result.message.lower()


def test_restart_service_nonexistent(docker_manager):
    """Test restarting a nonexistent service returns failure."""
    result = docker_manager.restart_service("nonexistent-service-12345")

    assert result.success is False
    assert "not found" in result.message.lower()


def test_remove_service_nonexistent(docker_manager):
    """Test removing a nonexistent service returns failure."""
    result = docker_manager.remove_service("nonexistent-service-12345")

    assert result.success is False
    assert "not found" in result.message.lower()


def test_get_resource_usage_nonexistent(docker_manager):
    """Test getting resource usage for nonexistent service returns None."""
    metrics = docker_manager.get_resource_usage("nonexistent-service-12345")

    assert metrics is None


def test_get_service_logs_nonexistent(docker_manager):
    """Test getting logs for nonexistent service returns empty list."""
    logs = docker_manager.get_service_logs("nonexistent-service-12345")

    assert logs == []
    assert isinstance(logs, list)


def test_get_service_logs_with_parameters(docker_manager):
    """Test getting logs with custom parameters."""
    logs = docker_manager.get_service_logs(
        "nonexistent-service-12345", lines=50, timestamps=False
    )

    assert logs == []


def test_stream_logs_nonexistent(docker_manager):
    """Test streaming logs for nonexistent service raises NotFound."""
    from docker.errors import NotFound

    with pytest.raises(NotFound):
        # Consume the generator to trigger the error
        list(docker_manager.stream_logs("nonexistent-service-12345"))


def test_update_service_nonexistent(docker_manager):
    """Test updating a nonexistent service returns failure."""
    result = docker_manager.update_service("nonexistent-service-12345")

    assert result.success is False
    assert "not found" in result.message.lower()


def test_check_for_updates_nonexistent(docker_manager):
    """Test checking for updates on nonexistent service returns False."""
    has_update = docker_manager.check_for_updates("nonexistent-service-12345")

    assert has_update is False


def test_get_service_status_with_update_check(docker_manager):
    """Test getting service status with update check parameter."""
    service_info = docker_manager.get_service_status(
        "nonexistent-service-12345", check_updates=True
    )

    assert service_info.name == "nonexistent-service-12345"
    assert service_info.status == ServiceStatus.UNKNOWN
    assert service_info.update_available is False


def test_get_service_status_without_update_check(docker_manager):
    """Test getting service status without update check (default)."""
    service_info = docker_manager.get_service_status(
        "nonexistent-service-12345", check_updates=False
    )

    assert service_info.name == "nonexistent-service-12345"
    assert service_info.status == ServiceStatus.UNKNOWN
    assert service_info.update_available is False


def test_deploy_stack_nonexistent_file(docker_manager):
    """Test deploying with nonexistent compose file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        # Consume the generator to trigger the error
        list(docker_manager.deploy_stack("/nonexistent/path/docker-compose.yml"))
