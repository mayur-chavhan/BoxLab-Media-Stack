"""Stack-related data models."""

from datetime import datetime

from pydantic import BaseModel, Field

from arr_stack_manager.models.configuration import Configuration


class StackConfig(BaseModel):
    """Configuration for a complete stack deployment."""

    name: str = Field(..., description="Stack name")
    configuration: Configuration = Field(..., description="Stack configuration")
    compose_path: str = Field(..., description="Path to docker-compose.yml file")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp when stack was created"
    )
    last_modified: datetime = Field(
        default_factory=datetime.now, description="Timestamp of last modification"
    )

    def update_modified_time(self) -> None:
        """Update the last_modified timestamp to current time."""
        self.last_modified = datetime.now()


class StackStatus(BaseModel):
    """Overall status of a stack."""

    name: str = Field(..., description="Stack name")
    total_services: int = Field(..., description="Total number of services", ge=0)
    running_services: int = Field(..., description="Number of running services", ge=0)
    stopped_services: int = Field(..., description="Number of stopped services", ge=0)
    error_services: int = Field(..., description="Number of services in error state", ge=0)
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Timestamp of last status update"
    )

    @property
    def is_healthy(self) -> bool:
        """Check if all services are running."""
        return self.running_services == self.total_services and self.error_services == 0

    @property
    def has_errors(self) -> bool:
        """Check if any services are in error state."""
        return self.error_services > 0

    def get_status_summary(self) -> str:
        """Get a human-readable status summary."""
        if self.is_healthy:
            return f"Running ({self.running_services}/{self.total_services} services)"
        elif self.has_errors:
            return f"Error ({self.error_services} services with errors)"
        elif self.stopped_services == self.total_services:
            return "Stopped"
        else:
            return f"Partial ({self.running_services}/{self.total_services} running)"
