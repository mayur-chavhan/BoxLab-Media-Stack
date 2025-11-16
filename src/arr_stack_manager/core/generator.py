"""Docker Compose generator for *arr stack deployments."""

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from arr_stack_manager.models.configuration import Configuration
from arr_stack_manager.models.stack import StackConfig
from arr_stack_manager.utils.services import SUPPORTED_SERVICES, get_service_metadata


class ComposeGenerator:
    """Generates Docker Compose files from templates with Trash-Guides best practices."""

    def __init__(self, template_dir: str | Path | None = None):
        """
        Initialize the Compose Generator.

        Args:
            template_dir: Directory containing Jinja2 templates. If None, uses default templates/ directory.
        """
        if template_dir is None:
            # Default to templates/ directory relative to project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            template_dir = project_root / "templates"

        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def generate_compose(self, stack: StackConfig) -> str:
        """
        Generate docker-compose.yml content from stack configuration.

        Args:
            stack: Stack configuration containing services and settings

        Returns:
            Generated docker-compose.yml content as string

        Raises:
            TemplateNotFound: If required template files are missing
            ValueError: If configuration is invalid
        """
        config = stack.configuration
        selected_services = config.get_selected_services()

        if not selected_services:
            raise ValueError("No services selected for stack generation")

        # Build service definitions with Trash-Guides settings
        services_data = []
        for service_name in selected_services:
            service_config = config.get_service(service_name)
            if not service_config:
                continue

            metadata = get_service_metadata(service_name)
            if not metadata:
                continue

            # Apply Trash-Guides settings and build service data
            service_data = self._build_service_data(
                service_name, service_config, metadata, config
            )
            services_data.append(service_data)

        # Prepare template context
        context = {
            "services": services_data,
            "network_name": f"{stack.name}-network",
            "puid": config.puid,
            "pgid": config.pgid,
            "timezone": config.timezone,
        }

        # Render the base template
        template = self.env.get_template("base.yml.j2")
        return template.render(context)

    def generate_env_file(self, config: Configuration) -> str:
        """
        Generate .env file content with user variables.

        Args:
            config: Configuration containing environment settings

        Returns:
            Generated .env file content as string
        """
        env_lines = [
            "# *arr Stack Manager - Environment Variables",
            "# Generated automatically - do not edit manually",
            "",
            "# User and Group IDs",
            f"PUID={config.puid}",
            f"PGID={config.pgid}",
            "",
            "# Timezone",
            f"TZ={config.timezone}",
            "",
            "# Paths",
            f"CONFIG_PATH={config.paths.config_path}",
            f"DATA_PATH={config.paths.data_path}",
            "",
        ]

        # Add service-specific environment variables
        for service_name, service_config in config.services.items():
            if not service_config.enabled:
                continue

            if service_config.environment_vars:
                env_lines.append(f"# {service_name.upper()} Environment Variables")
                for key, value in service_config.environment_vars.items():
                    env_lines.append(f"{key}={value}")
                env_lines.append("")

        return "\n".join(env_lines)

    def configure_volumes(
        self, service_name: str, config: Configuration
    ) -> list[dict[str, Any]]:
        """
        Configure volume mounts for a service with hardlink-compatible structure.

        This follows Trash-Guides best practices:
        - Single /data mount point for atomic moves and hardlinks
        - Separate /config mount for service configuration
        - Proper structure: /data/media and /data/downloads

        Args:
            service_name: Name of the service
            config: Configuration containing path settings

        Returns:
            List of volume mount dictionaries with host_path, container_path, and read_only
        """
        volumes = []
        metadata = get_service_metadata(service_name)
        service_config = config.get_service(service_name)

        if not metadata or not service_config:
            return volumes

        # Add config volume
        if "/config" in metadata["required_volumes"]:
            volumes.append({
                "host_path": f"{config.paths.config_path}/{service_name}",
                "container_path": "/config",
                "read_only": False,
            })

        # Add data volume for services that need it (Trash-Guides: single mount point)
        if "/data" in metadata["required_volumes"]:
            volumes.append({
                "host_path": config.paths.data_path,
                "container_path": "/data",
                "read_only": False,
            })

        # Handle special cases for media servers
        if "/data/media" in metadata["required_volumes"]:
            volumes.append({
                "host_path": f"{config.paths.data_path}/media",
                "container_path": "/data/media",
                "read_only": False,
            })

        # Handle special volume requirements for specific services
        if service_name == "jellyseerr":
            # Jellyseerr uses /app/config instead of /config
            volumes = [
                {
                    "host_path": f"{config.paths.config_path}/{service_name}",
                    "container_path": "/app/config",
                    "read_only": False,
                }
            ]
        elif service_name == "tdarr":
            # Tdarr has special volume requirements
            volumes = [
                {
                    "host_path": f"{config.paths.config_path}/{service_name}/server",
                    "container_path": "/app/server",
                    "read_only": False,
                },
                {
                    "host_path": f"{config.paths.config_path}/{service_name}/configs",
                    "container_path": "/app/configs",
                    "read_only": False,
                },
                {
                    "host_path": config.paths.data_path,
                    "container_path": "/data",
                    "read_only": False,
                },
            ]

        # Add custom volumes from service configuration
        for host_path, container_path in service_config.custom_volumes.items():
            volumes.append({
                "host_path": host_path,
                "container_path": container_path,
                "read_only": False,
            })

        return volumes

    def apply_trash_guides_settings(
        self, service_name: str, config: Configuration
    ) -> dict[str, Any]:
        """
        Apply Trash-Guides best practices for a service.

        This includes:
        - UMASK=002 for proper file permissions
        - Proper volume structure for hardlinks
        - Recommended environment variables

        Args:
            service_name: Name of the service
            config: Configuration containing service settings

        Returns:
            Dictionary of additional settings to apply
        """
        settings: dict[str, Any] = {}

        # Services that benefit from Trash-Guides settings
        trash_guides_services = ["sonarr", "radarr", "bazarr", "prowlarr"]

        if service_name in trash_guides_services:
            # Set UMASK for proper permissions (Trash-Guides recommendation)
            settings["environment"] = {"UMASK": "002"}

            # Add any service-specific Trash-Guides settings
            if service_name == "sonarr":
                # Sonarr-specific settings can be added here
                pass
            elif service_name == "radarr":
                # Radarr-specific settings can be added here
                pass

        return settings

    def save_to_disk(
        self, output_dir: str | Path, compose_content: str, env_content: str
    ) -> None:
        """
        Write generated files to disk.

        Args:
            output_dir: Directory where files should be written
            compose_content: Content of docker-compose.yml
            env_content: Content of .env file

        Raises:
            OSError: If files cannot be written
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write docker-compose.yml
        compose_file = output_path / "docker-compose.yml"
        compose_file.write_text(compose_content, encoding="utf-8")

        # Write .env file
        env_file = output_path / ".env"
        env_file.write_text(env_content, encoding="utf-8")

    def _build_service_data(
        self,
        service_name: str,
        service_config: Any,
        metadata: dict[str, Any],
        config: Configuration,
    ) -> dict[str, Any]:
        """
        Build service data dictionary for template rendering.

        Args:
            service_name: Name of the service
            service_config: Service configuration
            metadata: Service metadata from SUPPORTED_SERVICES
            config: Full configuration

        Returns:
            Dictionary containing all service data for template
        """
        # Get volumes with Trash-Guides structure
        volumes = self.configure_volumes(service_name, config)

        # Get Trash-Guides settings
        trash_settings = self.apply_trash_guides_settings(service_name, config)

        # Build environment variables
        environment = {
            "PUID": str(config.puid),
            "PGID": str(config.pgid),
            "TZ": config.timezone,
        }

        # Add Trash-Guides environment variables
        if "environment" in trash_settings:
            environment.update(trash_settings["environment"])

        # Add custom environment variables from service config
        environment.update(service_config.environment_vars)

        # Build port mappings
        ports = []
        if metadata["default_port"] > 0:  # Some services don't have web UIs
            ports.append({
                "host_port": service_config.port,
                "container_port": metadata["default_port"],
                "protocol": "tcp",
            })

        service_data = {
            "name": service_name,
            "image": metadata["image"],
            "environment": environment,
            "volumes": volumes,
            "ports": ports,
            "depends_on": [],  # Can be extended for service dependencies
        }

        return service_data
