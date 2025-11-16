#!/usr/bin/env python3
"""Demo script for testing the first-run experience."""

import tempfile
from pathlib import Path

from arr_stack_manager.app import StackManagerApp


def main():
    """Run the first-run experience demo."""
    # Use a temporary directory to simulate first run
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "config"

        print(f"Using temporary config directory: {config_dir}")
        print("This simulates a first-run experience.\n")

        # Create the app with the temporary config directory
        # This will trigger first-run detection
        app = StackManagerApp(config_dir=config_dir)

        # Run the app
        app.run()


if __name__ == "__main__":
    main()
