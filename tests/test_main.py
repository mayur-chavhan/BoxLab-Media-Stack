"""Tests for the main entry point and CLI."""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arr_stack_manager.__main__ import main, parse_args, setup_logging


def test_parse_args_default() -> None:
    """Test parsing arguments with defaults."""
    with patch.object(sys, "argv", ["arr-stack-manager"]):
        args = parse_args()

        assert args.config_dir is None
        assert args.template_dir is None
        assert args.stack_name is None
        assert args.welcome is False
        assert args.verbose is False
        assert args.log_file is None
        assert args.no_docker_check is False


def test_parse_args_with_config_dir() -> None:
    """Test parsing arguments with custom config directory."""
    test_path = "/tmp/test-config"
    with patch.object(sys, "argv", ["arr-stack-manager", "--config-dir", test_path]):
        args = parse_args()

        assert args.config_dir == Path(test_path)


def test_parse_args_with_template_dir() -> None:
    """Test parsing arguments with custom template directory."""
    test_path = "/tmp/test-templates"
    with patch.object(sys, "argv", ["arr-stack-manager", "--template-dir", test_path]):
        args = parse_args()

        assert args.template_dir == Path(test_path)


def test_parse_args_with_stack_name() -> None:
    """Test parsing arguments with stack name."""
    stack_name = "media-automation"
    with patch.object(sys, "argv", ["arr-stack-manager", "--stack-name", stack_name]):
        args = parse_args()

        assert args.stack_name == stack_name


def test_parse_args_with_welcome() -> None:
    """Test parsing arguments with welcome flag."""
    with patch.object(sys, "argv", ["arr-stack-manager", "--welcome"]):
        args = parse_args()

        assert args.welcome is True


def test_parse_args_with_verbose() -> None:
    """Test parsing arguments with verbose flag."""
    with patch.object(sys, "argv", ["arr-stack-manager", "--verbose"]):
        args = parse_args()

        assert args.verbose is True


def test_parse_args_with_verbose_short() -> None:
    """Test parsing arguments with verbose short flag."""
    with patch.object(sys, "argv", ["arr-stack-manager", "-v"]):
        args = parse_args()

        assert args.verbose is True


def test_parse_args_with_log_file() -> None:
    """Test parsing arguments with log file."""
    log_path = "/tmp/test.log"
    with patch.object(sys, "argv", ["arr-stack-manager", "--log-file", log_path]):
        args = parse_args()

        assert args.log_file == Path(log_path)


def test_parse_args_with_no_docker_check() -> None:
    """Test parsing arguments with no-docker-check flag."""
    with patch.object(sys, "argv", ["arr-stack-manager", "--no-docker-check"]):
        args = parse_args()

        assert args.no_docker_check is True


def test_parse_args_combined() -> None:
    """Test parsing multiple arguments together."""
    with patch.object(
        sys,
        "argv",
        [
            "arr-stack-manager",
            "--config-dir",
            "/tmp/config",
            "--stack-name",
            "test-stack",
            "--verbose",
            "--welcome",
        ],
    ):
        args = parse_args()

        assert args.config_dir == Path("/tmp/config")
        assert args.stack_name == "test-stack"
        assert args.verbose is True
        assert args.welcome is True


def test_setup_logging_default() -> None:
    """Test logging setup with default settings."""
    # Create a new logger for testing
    test_logger = logging.getLogger("test_setup_default")
    test_logger.handlers.clear()
    
    setup_logging(verbose=False, log_file=None)

    # Check that root logger has handlers configured
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0


def test_setup_logging_verbose() -> None:
    """Test logging setup with verbose enabled."""
    # Create a new logger for testing
    test_logger = logging.getLogger("test_setup_verbose")
    test_logger.handlers.clear()
    
    setup_logging(verbose=True, log_file=None)

    # Check that root logger has handlers configured
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0


def test_setup_logging_with_file(tmp_path: Path) -> None:
    """Test logging setup with log file."""
    log_file = tmp_path / "test.log"
    setup_logging(verbose=False, log_file=log_file)

    # Check that log file was created
    assert log_file.parent.exists()

    # Log a test message
    logger = logging.getLogger("test")
    logger.info("Test message")

    # File should exist after logging
    assert log_file.exists()


@patch("arr_stack_manager.__main__.StackManagerApp")
def test_main_default(mock_app_class: MagicMock) -> None:
    """Test main function with default arguments."""
    mock_app = MagicMock()
    mock_app_class.return_value = mock_app

    with patch.object(sys, "argv", ["arr-stack-manager"]):
        main()

    # App should be created with default arguments
    mock_app_class.assert_called_once()
    call_kwargs = mock_app_class.call_args[1]
    assert call_kwargs["config_dir"] is None
    assert call_kwargs["template_dir"] is None
    assert call_kwargs["stack_name"] is None
    assert call_kwargs["show_welcome"] is False

    # App should be run
    mock_app.run.assert_called_once()


@patch("arr_stack_manager.__main__.StackManagerApp")
def test_main_with_arguments(mock_app_class: MagicMock) -> None:
    """Test main function with custom arguments."""
    mock_app = MagicMock()
    mock_app_class.return_value = mock_app

    with patch.object(
        sys,
        "argv",
        [
            "arr-stack-manager",
            "--config-dir",
            "/tmp/config",
            "--stack-name",
            "test-stack",
            "--welcome",
        ],
    ):
        main()

    # App should be created with custom arguments
    mock_app_class.assert_called_once()
    call_kwargs = mock_app_class.call_args[1]
    assert call_kwargs["config_dir"] == Path("/tmp/config")
    assert call_kwargs["stack_name"] == "test-stack"
    assert call_kwargs["show_welcome"] is True

    # App should be run
    mock_app.run.assert_called_once()


@patch("arr_stack_manager.__main__.StackManagerApp")
def test_main_keyboard_interrupt(mock_app_class: MagicMock) -> None:
    """Test main function handling keyboard interrupt."""
    mock_app = MagicMock()
    mock_app.run.side_effect = KeyboardInterrupt()
    mock_app_class.return_value = mock_app

    with patch.object(sys, "argv", ["arr-stack-manager"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0


@patch("arr_stack_manager.__main__.StackManagerApp")
def test_main_exception(mock_app_class: MagicMock) -> None:
    """Test main function handling exceptions."""
    mock_app = MagicMock()
    mock_app.run.side_effect = Exception("Test error")
    mock_app_class.return_value = mock_app

    with patch.object(sys, "argv", ["arr-stack-manager"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1


def test_version_argument() -> None:
    """Test --version argument."""
    with patch.object(sys, "argv", ["arr-stack-manager", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            parse_args()

        # Version flag causes exit with code 0
        assert exc_info.value.code == 0


def test_help_argument() -> None:
    """Test --help argument."""
    with patch.object(sys, "argv", ["arr-stack-manager", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            parse_args()

        # Help flag causes exit with code 0
        assert exc_info.value.code == 0
