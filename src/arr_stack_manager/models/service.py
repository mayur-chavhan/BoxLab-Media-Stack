"""Service-related data models."""

from enum import Enum

from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Status of a service container."""

    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class ResourceMetrics(BaseModel):
    """Resource usage metrics for a service."""

    cpu_percent: float = Field(..., description="CPU usage percentage", ge=0.0, le=100.0)
    memory_usage: int = Field(..., description="Memory usage in bytes", ge=0)
    memory_limit: int = Field(..., description="Memory limit in bytes", ge=0)
    network_rx: int = Field(default=0, description="Network bytes received", ge=0)
    network_tx: int = Field(default=0, description="Network bytes transmitted", ge=0)

    @property
    def memory_percent(self) -> float:
        """Calculate memory usage percentage."""
        if self.memory_limit == 0:
            return 0.0
        return (self.memory_usage / self.memory_limit) * 100.0

    def format_memory(self) -> str:
        """Format memory usage as human-readable string."""
        usage_mb = self.memory_usage / (1024 * 1024)
        limit_mb = self.memory_limit / (1024 * 1024)
        return f"{usage_mb:.0f}MB / {limit_mb:.0f}MB"


class ServiceInfo(BaseModel):
    """Information about a service and its container."""

    name: str = Field(..., description="Service name")
    status: ServiceStatus = Field(..., description="Current service status")
    container_id: str | None = Field(None, description="Docker container ID")
    image: str = Field(..., description="Docker image name and tag")
    uptime: int | None = Field(None, description="Uptime in seconds", ge=0)
    web_ui_url: str | None = Field(None, description="URL to access the service web UI")
    metrics: ResourceMetrics | None = Field(None, description="Resource usage metrics")
    update_available: bool = Field(default=False, description="Whether an update is available")

    def format_uptime(self) -> str:
        """Format uptime as human-readable string."""
        if self.uptime is None:
            return "N/A"

        days = self.uptime // 86400
        hours = (self.uptime % 86400) // 3600
        minutes = (self.uptime % 3600) // 60

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or not parts:
            parts.append(f"{minutes}m")

        return " ".join(parts)

    @property
    def is_running(self) -> bool:
        """Check if service is in running state."""
        return self.status == ServiceStatus.RUNNING

    @property
    def is_stopped(self) -> bool:
        """Check if service is in stopped state."""
        return self.status == ServiceStatus.STOPPED
