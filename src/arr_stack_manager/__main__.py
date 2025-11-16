"""Entry point for arr-stack-manager CLI."""

import argparse
import logging
import sys
from pathlib import Path

from arr_stack_manager import __version__
from arr_stack_manager.app import StackManagerApp


def setup_logging(verbose: bool = False, log_file: Path | None = None) -> None:
    """Set up application logging.

    Args:
        verbose: Enable verbose (DEBUG) logging
        log_file: Optional log file path
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
        ],
    )

    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("docker").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="arr-stack-manager",
        description="A TUI application for deploying and managing *arr media automation stacks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default configuration
  arr-stack-manager

  # Load a specific stack
  arr-stack-manager --stack-name media-automation

  # Use custom configuration directory
  arr-stack-manager --config-dir /path/to/config

  # Show welcome screen on startup
  arr-stack-manager --welcome

  # Enable verbose logging
  arr-stack-manager --verbose

For more information, visit: https://github.com/yourusername/arr-stack-manager
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version and exit",
    )

    parser.add_argument(
        "--config-dir",
        type=Path,
        metavar="PATH",
        help="Custom configuration directory (default: ~/.config/arr-stack-manager)",
    )

    parser.add_argument(
        "--template-dir",
        type=Path,
        metavar="PATH",
        help="Custom template directory (default: built-in templates)",
    )

    parser.add_argument(
        "--stack-name",
        type=str,
        metavar="NAME",
        help="Name of the stack to load on startup",
    )

    parser.add_argument(
        "--welcome",
        action="store_true",
        help="Show welcome screen on startup",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        metavar="PATH",
        help="Write logs to specified file",
    )

    parser.add_argument(
        "--no-docker-check",
        action="store_true",
        help="Skip Docker availability check on startup (for testing)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the application."""
    # Parse command-line arguments
    args = parse_args()

    # Set up logging
    setup_logging(verbose=args.verbose, log_file=args.log_file)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting arr Stack Manager v{__version__}")

    # Check Docker prerequisites before starting
    from arr_stack_manager.utils.docker_check import (
        check_docker_prerequisites,
        print_docker_check_result,
    )

    docker_check = check_docker_prerequisites()

    if not docker_check.is_ready:
        print_docker_check_result(docker_check)
        logger.error("Docker prerequisites check failed")
        sys.exit(1)

    logger.info("Docker prerequisites check passed")
    if docker_check.is_root:
        logger.warning("Running as root user")
    elif docker_check.in_docker_group:
        logger.info("User is in docker group")

    # Log configuration
    if args.config_dir:
        logger.info(f"Using custom config directory: {args.config_dir}")
    if args.template_dir:
        logger.info(f"Using custom template directory: {args.template_dir}")
    if args.stack_name:
        logger.info(f"Loading stack: {args.stack_name}")

    try:
        # Create and run the application
        app = StackManagerApp(
            config_dir=args.config_dir,
            template_dir=args.template_dir,
            stack_name=args.stack_name,
            show_welcome=args.welcome,
        )

        # Run the application
        app.run()

        logger.info("Application exited normally")

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"Application crashed: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        print("\nFor more information, run with --verbose flag", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
