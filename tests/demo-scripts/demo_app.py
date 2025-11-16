#!/usr/bin/env python3
"""Demo script to show the arr Stack Manager app."""

from pathlib import Path

from arr_stack_manager.app import StackManagerApp

if __name__ == "__main__":
    # Create app with welcome screen
    app = StackManagerApp(
        config_dir=Path("/tmp/arr-stack-manager-demo"),
        show_welcome=True,
    )

    # Run the app
    app.run()
