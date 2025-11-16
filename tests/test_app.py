"""Tests for the main Textual application."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arr_stack_manager.app import HelpScreen, StackManagerApp, WelcomeScreen


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary configuration directory.

    Args:
        tmp_path: Pytest temporary path fixture

    Returns:
        Path to temporary config directory
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def app(temp_config_dir: Path) -> StackManagerApp:
    """Create a StackManagerApp instance for testing.

    Args:
        temp_config_dir: Temporary configuration directory

    Returns:
        StackManagerApp instance
    """
    return StackManagerApp(config_dir=temp_config_dir, show_welcome=False)


def test_app_initialization(temp_config_dir: Path) -> None:
    """Test that the app initializes correctly."""
    app = StackManagerApp(config_dir=temp_config_dir)

    assert app.TITLE == "*arr Stack Manager"
    assert app.SUB_TITLE == "Media Automation Stack Management"
    assert app.controller is not None
    assert app.stack_name is None
    assert app.show_welcome is False


def test_app_initialization_with_stack_name(temp_config_dir: Path) -> None:
    """Test app initialization with a stack name."""
    stack_name = "test-stack"
    app = StackManagerApp(config_dir=temp_config_dir, stack_name=stack_name)

    assert app.stack_name == stack_name


def test_app_initialization_with_welcome(temp_config_dir: Path) -> None:
    """Test app initialization with welcome screen enabled."""
    app = StackManagerApp(config_dir=temp_config_dir, show_welcome=True)

    assert app.show_welcome is True


def test_navigation_callbacks_registered(app: StackManagerApp) -> None:
    """Test that navigation callbacks are registered."""
    # Check that callbacks are registered in the controller
    assert len(app.controller._navigation_callbacks) > 0


@pytest.mark.asyncio
async def test_help_screen_display() -> None:
    """Test that the help screen displays correctly."""
    app = StackManagerApp(show_welcome=False)

    async with app.run_test() as pilot:
        # Push help screen
        app.push_screen(HelpScreen())
        await pilot.pause()

        # Verify help screen is displayed
        assert isinstance(app.screen, HelpScreen)

        # Dismiss help screen
        await pilot.press("escape")
        await pilot.pause()


@pytest.mark.asyncio
async def test_welcome_screen_display() -> None:
    """Test that the welcome screen displays correctly."""
    app = StackManagerApp(show_welcome=False)

    async with app.run_test() as pilot:
        # Push welcome screen
        app.push_screen(WelcomeScreen())
        await pilot.pause()

        # Verify welcome screen is displayed
        assert isinstance(app.screen, WelcomeScreen)

        # Continue from welcome screen
        await pilot.press("enter")
        await pilot.pause()


@pytest.mark.asyncio
async def test_app_quit_action() -> None:
    """Test that the quit action works."""
    app = StackManagerApp(show_welcome=False)

    async with app.run_test() as pilot:
        # Trigger quit action
        await pilot.press("q")
        await pilot.pause()

        # App should exit (test framework handles this)


def test_app_help_action() -> None:
    """Test that the help action method exists and can be called."""
    app = StackManagerApp(show_welcome=False)
    
    # Test that the action method exists
    assert hasattr(app, "action_help")
    
    # Test that we can call it (it should push a help screen)
    with patch.object(app, "push_screen") as mock_push:
        app.action_help()
        mock_push.assert_called_once()
        # Verify it's pushing a HelpScreen
        args = mock_push.call_args[0]
        assert isinstance(args[0], HelpScreen)


def test_app_bindings_defined(app: StackManagerApp) -> None:
    """Test that global keyboard bindings are defined."""
    binding_keys = [binding.key for binding in app.BINDINGS]

    # Check that essential bindings are present
    assert "q" in binding_keys
    assert "h" in binding_keys
    assert "d" in binding_keys
    assert "s" in binding_keys
    assert "c" in binding_keys
    assert "m" in binding_keys
    assert "r" in binding_keys


def test_app_css_defined(app: StackManagerApp) -> None:
    """Test that CSS styling is defined."""
    assert app.CSS is not None
    assert len(app.CSS) > 0

    # Check for key CSS elements
    assert "App" in app.CSS
    assert "Header" in app.CSS
    assert "Footer" in app.CSS
    assert "Button" in app.CSS


def test_help_screen_bindings() -> None:
    """Test that help screen has proper bindings."""
    screen = HelpScreen()
    # BINDINGS is a list of tuples (key, action, description)
    binding_keys = [binding[0] if isinstance(binding, tuple) else binding.key for binding in screen.BINDINGS]

    assert "escape" in binding_keys
    assert "q" in binding_keys


def test_welcome_screen_bindings() -> None:
    """Test that welcome screen has proper bindings."""
    screen = WelcomeScreen()
    # BINDINGS is a list of tuples (key, action, description)
    binding_keys = [binding[0] if isinstance(binding, tuple) else binding.key for binding in screen.BINDINGS]

    assert "enter" in binding_keys
    assert "q" in binding_keys


def test_app_controller_integration(app: StackManagerApp) -> None:
    """Test that the app integrates properly with the controller."""
    # Controller should be initialized
    assert app.controller is not None

    # Controller should have access to core components
    assert app.controller.validator is not None
    assert app.controller.generator is not None
    assert app.controller.docker_manager is not None
    assert app.controller.config_repository is not None


@pytest.mark.asyncio
async def test_app_mount_without_stack() -> None:
    """Test app mounting without a stack name."""
    app = StackManagerApp(show_welcome=False)

    async with app.run_test() as pilot:
        await pilot.pause()

        # App should mount successfully
        assert app.is_mounted


@pytest.mark.asyncio
async def test_app_mount_with_welcome() -> None:
    """Test app mounting with welcome screen."""
    # Use a temporary directory with an existing stack to avoid first-run
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        # Create a dummy stack to avoid first-run detection
        stacks_dir = config_dir / "stacks"
        stacks_dir.mkdir(parents=True)
        (stacks_dir / "dummy.json").write_text('{"name": "dummy"}')

        app = StackManagerApp(config_dir=config_dir, show_welcome=True)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Welcome screen should be displayed (not setup wizard since we have a stack)
            assert isinstance(app.screen, WelcomeScreen)


@pytest.mark.asyncio
async def test_app_mount_first_run() -> None:
    """Test app mounting on first run shows setup wizard."""
    import tempfile
    from pathlib import Path
    from arr_stack_manager.screens import SetupWizardScreen

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        # Don't create any stacks - this simulates first run

        app = StackManagerApp(config_dir=config_dir)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Setup wizard should be displayed on first run
            assert isinstance(app.screen, SetupWizardScreen)


def test_navigation_methods_exist(app: StackManagerApp) -> None:
    """Test that navigation methods are defined."""
    assert hasattr(app, "_navigate_to_dashboard")
    assert hasattr(app, "_navigate_to_service_selector")
    assert hasattr(app, "_navigate_to_config_wizard")
    assert hasattr(app, "_navigate_to_stack_manager")
    assert hasattr(app, "_navigate_to_deployment_monitor")


def test_action_methods_exist(app: StackManagerApp) -> None:
    """Test that action methods are defined."""
    assert hasattr(app, "action_quit")
    assert hasattr(app, "action_help")
    assert hasattr(app, "action_goto_dashboard")
    assert hasattr(app, "action_goto_services")
    assert hasattr(app, "action_goto_config")
    assert hasattr(app, "action_goto_manager")
    assert hasattr(app, "action_refresh")
