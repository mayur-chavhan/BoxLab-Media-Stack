"""Configuration data models."""


from pydantic import BaseModel, Field, field_validator


class PathConfig(BaseModel):
    """Path configuration for stack deployment."""

    base_path: str = Field(..., description="Base directory for all stack data")
    config_path: str | None = Field(
        None, description="Path for service configurations (derived from base_path if not set)"
    )
    data_path: str | None = Field(
        None, description="Path for media and downloads (derived from base_path if not set)"
    )

    @field_validator("base_path")
    @classmethod
    def validate_base_path(cls, v: str) -> str:
        """Validate base path is not empty."""
        if not v or not v.strip():
            raise ValueError("Base path cannot be empty")
        return v.strip()

    def model_post_init(self, __context: object) -> None:
        """Set derived paths if not explicitly provided."""
        if self.config_path is None:
            self.config_path = f"{self.base_path}/config"
        if self.data_path is None:
            self.data_path = f"{self.base_path}/data"


class ServiceConfig(BaseModel):
    """Configuration for an individual service."""

    name: str = Field(..., description="Service name (e.g., 'sonarr', 'radarr')")
    enabled: bool = Field(default=True, description="Whether the service is enabled")
    port: int = Field(..., description="Host port for the service", gt=0, lt=65536)
    custom_volumes: dict[str, str] = Field(
        default_factory=dict, description="Custom volume mounts (host_path: container_path)"
    )
    environment_vars: dict[str, str] = Field(
        default_factory=dict, description="Additional environment variables"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate service name is not empty and lowercase."""
        if not v or not v.strip():
            raise ValueError("Service name cannot be empty")
        return v.strip().lower()


class Configuration(BaseModel):
    """Main application configuration."""

    puid: int = Field(..., description="User ID for container processes", ge=0)
    pgid: int = Field(..., description="Group ID for container processes", ge=0)
    timezone: str = Field(default="UTC", description="Timezone for services")
    paths: PathConfig = Field(..., description="Path configuration")
    services: dict[str, ServiceConfig] = Field(
        default_factory=dict, description="Service configurations by service name"
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone is not empty."""
        if not v or not v.strip():
            raise ValueError("Timezone cannot be empty")
        return v.strip()

    def get_selected_services(self) -> list[str]:
        """Get list of enabled service names."""
        return [name for name, config in self.services.items() if config.enabled]

    def add_service(self, service_config: ServiceConfig) -> None:
        """Add or update a service configuration."""
        self.services[service_config.name] = service_config

    def remove_service(self, service_name: str) -> None:
        """Remove a service configuration."""
        self.services.pop(service_name, None)

    def get_service(self, service_name: str) -> ServiceConfig | None:
        """Get a service configuration by name."""
        return self.services.get(service_name)
