"""Validation and operation result models."""


from datetime import datetime

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of a validation operation."""

    valid: bool = Field(..., description="Whether validation passed")
    errors: list[str] = Field(default_factory=list, description="List of validation errors")
    warnings: list[str] = Field(default_factory=list, description="List of validation warnings")

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.valid:
            self.valid = False

    def get_summary(self) -> str:
        """Get a summary of validation results."""
        if self.valid and not self.has_warnings:
            return "Validation passed"
        elif self.valid and self.has_warnings:
            return f"Validation passed with {len(self.warnings)} warning(s)"
        else:
            return f"Validation failed with {len(self.errors)} error(s)"


class OperationResult(BaseModel):
    """Result of a Docker operation."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable result message")
    details: str | None = Field(None, description="Additional details about the operation")

    @classmethod
    def success_result(cls, message: str, details: str | None = None) -> "OperationResult":
        """Create a successful operation result."""
        return cls(success=True, message=message, details=details)

    @classmethod
    def failure_result(cls, message: str, details: str | None = None) -> "OperationResult":
        """Create a failed operation result."""
        return cls(success=False, message=message, details=details)

    def get_full_message(self) -> str:
        """Get the full message including details if available."""
        if self.details:
            return f"{self.message}\n{self.details}"
        return self.message


class DeploymentEvent(BaseModel):
    """Event emitted during stack deployment."""

    timestamp: datetime = Field(..., description="When the event occurred")
    stage: str = Field(..., description="Deployment stage name")
    message: str = Field(..., description="Event message")
    progress: float = Field(..., description="Overall progress (0.0 to 1.0)", ge=0.0, le=1.0)

    @classmethod
    def create(cls, stage: str, message: str, progress: float) -> "DeploymentEvent":
        """Create a deployment event with current timestamp."""
        return cls(timestamp=datetime.now(), stage=stage, message=message, progress=progress)
