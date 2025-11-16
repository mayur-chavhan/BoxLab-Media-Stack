"""Tests for the Service Selector screen."""

from unittest.mock import patch

import pytest

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.screens.service_selector import (
    CATEGORY_NAMES,
    ServiceCategory,
    ServiceItem,
    ServiceSelectorScreen,
)
from arr_stack_manager.utils.services import SUPPORTED_SERVICES, get_services_by_category


@pytest.fixture
def mock_controller(tmp_path):
    """Create a mock controller for testing."""
    with patch("arr_stack_manager.controller.DockerManager"):
        controller = AppController(config_dir=tmp_path / "config")
        return controller


@pytest.fixture
def sample_configuration(tmp_path):
    """Create a sample configuration with some services selected."""
    config = Configuration(
        puid=1000,
        pgid=1000,
        timezone="America/New_York",
        paths=PathConfig(base_path=str(tmp_path / "stack")),
        services={
            "sonarr": ServiceConfig(name="sonarr", enabled=True, port=8989),
            "radarr": ServiceConfig(name="radarr", enabled=True, port=7878),
            "prowlarr": ServiceConfig(name="prowlarr", enabled=False, port=9696),
        },
    )
    return config


def test_service_item_initialization():
    """Test that ServiceItem initializes correctly."""
    item = ServiceItem(
        service_id="sonarr",
        service_name="Sonarr",
        description="TV show automation",
        selected=True,
    )

    assert item.service_id == "sonarr"
    assert item.service_name == "Sonarr"
    assert item.description == "TV show automation"
    assert item.selected is True


def test_service_item_not_selected():
    """Test ServiceItem with unselected state."""
    item = ServiceItem(
        service_id="radarr",
        service_name="Radarr",
        description="Movie automation",
        selected=False,
    )

    assert item.selected is False


def test_service_category_initialization():
    """Test that ServiceCategory initializes correctly."""
    selected = {"sonarr", "radarr"}
    category = ServiceCategory(
        category_id="media_management",
        category_name="Media Management",
        service_ids=["sonarr", "radarr", "prowlarr"],
        selected_services=selected,
    )

    assert category.category_id == "media_management"
    assert category.category_name == "Media Management"
    assert len(category.service_ids) == 3
    assert category.selected_services == selected


def test_service_selector_screen_initialization(mock_controller):
    """Test that ServiceSelectorScreen initializes correctly."""
    screen = ServiceSelectorScreen(mock_controller)

    assert screen.controller == mock_controller
    assert screen.existing_config is None
    assert len(screen._selected_services) == 0
    assert screen._validation_error is None


def test_service_selector_screen_with_existing_config(mock_controller, sample_configuration):
    """Test initialization with existing configuration."""
    screen = ServiceSelectorScreen(mock_controller, existing_config=sample_configuration)

    assert screen.existing_config == sample_configuration
    # Should pre-populate with enabled services
    assert "sonarr" in screen._selected_services
    assert "radarr" in screen._selected_services
    assert "prowlarr" not in screen._selected_services  # disabled


def test_service_selector_format_selected_count(mock_controller):
    """Test formatting of selected service count."""
    screen = ServiceSelectorScreen(mock_controller)

    # No services selected
    assert screen._format_selected_count() == "No services selected"

    # One service selected
    screen._selected_services.add("sonarr")
    assert screen._format_selected_count() == "1 service selected"

    # Multiple services selected
    screen._selected_services.add("radarr")
    assert screen._format_selected_count() == "2 services selected"


def test_service_selector_validate_selection_empty(mock_controller):
    """Test validation fails with no services selected."""
    screen = ServiceSelectorScreen(mock_controller)

    result = screen._validate_selection()

    assert result is False
    assert screen._validation_error is not None
    assert "at least one service" in screen._validation_error.lower()


def test_service_selector_validate_selection_success(mock_controller):
    """Test validation passes with services selected."""
    screen = ServiceSelectorScreen(mock_controller)
    screen._selected_services.add("sonarr")

    result = screen._validate_selection()

    assert result is True
    assert screen._validation_error is None


def test_service_selector_bindings(mock_controller):
    """Test that service selector has correct key bindings."""
    screen = ServiceSelectorScreen(mock_controller)

    assert len(screen.BINDINGS) > 0

    binding_keys = [binding[0] for binding in screen.BINDINGS]
    assert "escape" in binding_keys
    assert "q" in binding_keys


def test_get_services_by_category():
    """Test that services are correctly grouped by category."""
    categories = get_services_by_category()

    assert "media_management" in categories
    assert "media_server" in categories
    assert "request_management" in categories

    # Check that known services are in correct categories
    assert "sonarr" in categories["media_management"]
    assert "radarr" in categories["media_management"]
    assert "jellyfin" in categories["media_server"]


def test_category_names_defined():
    """Test that all category names are defined."""
    categories = get_services_by_category()

    for category_id in categories.keys():
        assert category_id in CATEGORY_NAMES, f"Missing display name for category: {category_id}"


def test_supported_services_structure():
    """Test that SUPPORTED_SERVICES has correct structure."""
    for service_id, metadata in SUPPORTED_SERVICES.items():
        assert "name" in metadata
        assert "description" in metadata
        assert "image" in metadata
        assert "default_port" in metadata
        assert "category" in metadata
        assert "required_volumes" in metadata
        assert "trash_guides_url" in metadata

        # Validate types
        assert isinstance(metadata["name"], str)
        assert isinstance(metadata["description"], str)
        assert isinstance(metadata["default_port"], int)
        assert isinstance(metadata["category"], str)
        assert isinstance(metadata["required_volumes"], list)


def test_service_selector_clear_validation_error(mock_controller):
    """Test clearing validation error."""
    screen = ServiceSelectorScreen(mock_controller)

    # Set an error
    screen._validation_error = "Test error"

    # Clear it
    screen._clear_validation_error()

    assert screen._validation_error is None


def test_service_selector_show_validation_error(mock_controller):
    """Test showing validation error."""
    screen = ServiceSelectorScreen(mock_controller)

    error_message = "Test validation error"
    screen._show_validation_error(error_message)

    assert screen._validation_error == error_message

