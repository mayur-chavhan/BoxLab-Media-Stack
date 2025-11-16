"""Tests for first-run experience and system detection."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arr_stack_manager.controller import AppController
from arr_stack_manager.utils.system_detection import SystemDetector


class TestSystemDetector:
    """Tests for SystemDetector class."""

    def test_get_current_user_info(self):
        """Test getting current user PUID and PGID."""
        detector = SystemDetector()
        puid, pgid = detector.get_current_user_info()

        # Should return integers
        assert isinstance(puid, int)
        assert isinstance(pgid, int)

        # Should be positive values
        assert puid > 0
        assert pgid > 0

    def test_get_current_username(self):
        """Test getting current username."""
        detector = SystemDetector()
        username = detector.get_current_username()

        # Should return a non-empty string
        assert isinstance(username, str)
        assert len(username) > 0

    def test_detect_timezone(self):
        """Test timezone detection."""
        detector = SystemDetector()
        timezone = detector.detect_timezone()

        # Should return a non-empty string
        assert isinstance(timezone, str)
        assert len(timezone) > 0

        # Should be a valid timezone format (e.g., "America/New_York" or "UTC")
        assert "/" in timezone or timezone == "UTC"

    def test_check_docker_available(self):
        """Test Docker availability check."""
        detector = SystemDetector()
        is_available, version = detector.check_docker_available()

        # Should return boolean and optional string
        assert isinstance(is_available, bool)
        if is_available:
            assert isinstance(version, str)
            assert len(version) > 0
        else:
            assert version is None

    def test_get_system_info(self):
        """Test getting system information."""
        detector = SystemDetector()
        info = detector.get_system_info()

        # Should return a dictionary with expected keys
        assert isinstance(info, dict)
        assert "os" in info
        assert "os_version" in info
        assert "architecture" in info
        assert "python_version" in info

        # All values should be non-empty strings
        for key, value in info.items():
            assert isinstance(value, str)
            assert len(value) > 0

    def test_suggest_base_path(self):
        """Test base path suggestion."""
        detector = SystemDetector()
        path = detector.suggest_base_path()

        # Should return a Path object
        assert isinstance(path, Path)

        # Path should be absolute
        assert path.is_absolute()

    def test_check_disk_space(self):
        """Test disk space checking."""
        detector = SystemDetector()

        # Check disk space for home directory
        has_enough, available_gb = detector.check_disk_space(Path.home(), required_gb=1.0)

        # Should return boolean and float
        assert isinstance(has_enough, bool)
        assert isinstance(available_gb, float)
        assert available_gb >= 0


class TestFirstRunDetection:
    """Tests for first-run detection."""

    def test_is_first_run_with_empty_config(self):
        """Test first-run detection with empty config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            controller = AppController(config_dir=config_dir)

            # Should be first run with empty directory
            assert controller.is_first_run() is True

    def test_is_first_run_with_existing_stack(self):
        """Test first-run detection with existing stack."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            controller = AppController(config_dir=config_dir)

            # Create a dummy stack file
            stacks_dir = config_dir / "stacks"
            stacks_dir.mkdir(parents=True, exist_ok=True)
            (stacks_dir / "test-stack.json").write_text('{"name": "test"}')

            # Should not be first run with existing stack
            assert controller.is_first_run() is False

    def test_is_first_run_after_initialization(self):
        """Test first-run detection after controller initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            controller = AppController(config_dir=config_dir)

            # Initialize creates directory structure
            controller.initialize()

            # Should still be first run (no stacks created)
            assert controller.is_first_run() is True


class TestSetupWizardIntegration:
    """Integration tests for setup wizard."""

    def test_setup_wizard_detects_system_info(self):
        """Test that setup wizard detects system information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            controller = AppController(config_dir=config_dir)

            # Import here to avoid circular dependency
            from arr_stack_manager.screens.setup_wizard import SetupWizardScreen

            wizard = SetupWizardScreen(controller)

            # Should have detected system information
            assert wizard.puid > 0
            assert wizard.pgid > 0
            assert len(wizard.username) > 0
            assert len(wizard.timezone) > 0
            assert isinstance(wizard.docker_available, bool)
            assert isinstance(wizard.system_info, dict)
            assert isinstance(wizard.suggested_path, Path)

    def test_setup_wizard_creates_config_directory(self):
        """Test that setup wizard works with config directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "new_config"
            controller = AppController(config_dir=config_dir)

            # Config directory should be created during initialization
            controller.initialize()

            # Directory should exist
            assert config_dir.exists()
            assert (config_dir / "stacks").exists()
            assert (config_dir / "backups").exists()
