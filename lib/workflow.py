"""
Workflow orchestration with state persistence and resume capability.

This module provides a framework for managing multi-step workflows with:
- Step-by-step execution with validation
- State persistence to disk
- Resume capability for interrupted workflows
- Progress tracking
- Rollback support
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Any, Optional, Dict, List
from enum import Enum


class StepStatus(Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow.
    
    Attributes:
        id: Unique identifier for the step
        name: Display name for the step
        action: Function to execute for this step
        validation: Optional function to validate step completion
        rollback: Optional function to undo step if needed
        description: Optional detailed description
        required: Whether this step is mandatory
    """
    id: str
    name: str
    action: Callable[[Dict[str, Any]], Dict[str, Any]]
    validation: Optional[Callable[[Dict[str, Any]], bool]] = None
    rollback: Optional[Callable[[Dict[str, Any]], None]] = None
    description: str = ""
    required: bool = True
    status: StepStatus = field(default=StepStatus.PENDING)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary (excluding callables)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "status": self.status.value,
            "error_message": self.error_message
        }


class WorkflowError(Exception):
    """Base exception for workflow errors."""
    pass


class WorkflowValidationError(WorkflowError):
    """Raised when step validation fails."""
    pass


class WorkflowStateError(WorkflowError):
    """Raised when workflow state is invalid."""
    pass


class WorkflowOrchestrator:
    """
    Manages workflow execution with state persistence.
    
    Example:
        >>> workflow = WorkflowOrchestrator(
        ...     workflow_id="install_services",
        ...     state_file=Path.home() / ".config/boxlab/workflow-state.json"
        ... )
        >>> 
        >>> def select_services(state):
        ...     # User selects services
        ...     return {"services": ["plex", "sonarr"]}
        >>> 
        >>> workflow.add_step(WorkflowStep(
        ...     id="select_services",
        ...     name="Select Services",
        ...     action=select_services
        ... ))
        >>> 
        >>> # Execute workflow
        >>> result = workflow.run()
    """
    
    def __init__(
        self, 
        workflow_id: str,
        state_file: Optional[Path] = None,
        auto_save: bool = True
    ):
        """
        Initialize workflow orchestrator.
        
        Args:
            workflow_id: Unique identifier for this workflow
            state_file: Path to state persistence file
            auto_save: Whether to auto-save state after each step
        """
        self.workflow_id = workflow_id
        self.state_file = state_file or self._get_default_state_file()
        self.auto_save = auto_save
        
        self.steps: List[WorkflowStep] = []
        self.state: Dict[str, Any] = {}
        self.current_step_index: int = 0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Try to load existing state
        self._load_state()
    
    def _get_default_state_file(self) -> Path:
        """Get default state file path."""
        config_dir = Path.home() / ".config" / "boxlab"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "workflow-state.json"
    
    def add_step(self, step: WorkflowStep) -> None:
        """
        Add a step to the workflow.
        
        Args:
            step: WorkflowStep to add
        
        Raises:
            ValueError: If step with same ID already exists
        """
        if any(s.id == step.id for s in self.steps):
            raise ValueError(f"Step with ID '{step.id}' already exists")
        
        self.steps.append(step)
    
    def get_progress(self) -> tuple[int, int]:
        """
        Get current progress.
        
        Returns:
            Tuple of (current_step_number, total_steps)
        """
        return (self.current_step_index + 1, len(self.steps))
    
    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID."""
        return next((s for s in self.steps if s.id == step_id), None)
    
    def _save_state(self) -> None:
        """Save current workflow state to disk."""
        state_data = {
            "version": 1,
            "workflow_id": self.workflow_id,
            "current_step_index": self.current_step_index,
            "total_steps": len(self.steps),
            "steps": [step.to_dict() for step in self.steps],
            "state": self.state,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "timestamp": datetime.now().isoformat()
        }
        
        # Ensure directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write atomically (write to temp file, then rename)
        temp_file = self.state_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(state_data, f, indent=2)
        
        temp_file.replace(self.state_file)
    
    def _load_state(self) -> bool:
        """
        Load workflow state from disk.
        
        Returns:
            True if state was loaded, False if no state file exists
        """
        if not self.state_file.exists():
            return False
        
        try:
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            
            # Validate state
            if state_data.get("workflow_id") != self.workflow_id:
                # Different workflow, don't load
                return False
            
            self.current_step_index = state_data.get("current_step_index", 0)
            self.state = state_data.get("state", {})
            
            if state_data.get("started_at"):
                self.started_at = datetime.fromisoformat(state_data["started_at"])
            
            if state_data.get("completed_at"):
                self.completed_at = datetime.fromisoformat(state_data["completed_at"])
            
            return True
            
        except (json.JSONDecodeError, KeyError) as e:
            # Corrupted state file, ignore
            return False
    
    def clear_state(self) -> None:
        """Clear saved workflow state."""
        if self.state_file.exists():
            self.state_file.unlink()
        
        self.state = {}
        self.current_step_index = 0
        self.started_at = None
        self.completed_at = None
    
    def can_resume(self) -> bool:
        """Check if workflow can be resumed from saved state."""
        return (
            self.state_file.exists() and
            self.current_step_index > 0 and
            self.current_step_index < len(self.steps) and
            self.completed_at is None
        )
    
    def run(self, resume: bool = True) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            resume: Whether to resume from saved state if available
        
        Returns:
            Final workflow state
        
        Raises:
            WorkflowError: If workflow execution fails
        """
        # Check if we should resume
        if resume and self.can_resume():
            print(f"\n🔄 Resuming workflow from step {self.current_step_index + 1}/{len(self.steps)}")
        else:
            # Start fresh
            self.current_step_index = 0
            self.state = {}
            self.started_at = datetime.now()
            self.completed_at = None
        
        # Execute steps
        try:
            while self.current_step_index < len(self.steps):
                step = self.steps[self.current_step_index]
                
                # Skip if already completed
                if step.status == StepStatus.COMPLETED:
                    print(f"✓ Step {self.current_step_index + 1}/{len(self.steps)}: {step.name} (already completed)")
                    self.current_step_index += 1
                    continue
                
                # Execute step
                self._execute_step(step)
                
                # Move to next step
                self.current_step_index += 1
                
                # Auto-save if enabled
                if self.auto_save:
                    self._save_state()
            
            # Mark as completed
            self.completed_at = datetime.now()
            self._save_state()
            
            print(f"\n✅ Workflow completed successfully!")
            
            return self.state
            
        except Exception as e:
            # Save state on failure
            self._save_state()
            raise WorkflowError(f"Workflow failed at step '{step.name}': {e}") from e
    
    def _execute_step(self, step: WorkflowStep) -> None:
        """
        Execute a single workflow step.
        
        Args:
            step: Step to execute
        
        Raises:
            WorkflowError: If step execution fails
        """
        print(f"\n⏳ Step {self.current_step_index + 1}/{len(self.steps)}: {step.name}")
        if step.description:
            print(f"   {step.description}")
        
        # Mark as in progress
        step.status = StepStatus.IN_PROGRESS
        
        try:
            # Execute step action
            result = step.action(self.state)
            
            # Merge result into state
            if result:
                self.state.update(result)
            
            # Validate if validator provided
            if step.validation:
                if not step.validation(self.state):
                    raise WorkflowValidationError(f"Step validation failed: {step.name}")
            
            # Mark as completed
            step.status = StepStatus.COMPLETED
            print(f"✓ Completed: {step.name}")
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            
            # Skip non-required steps
            if not step.required:
                print(f"⚠️  Skipped (optional): {step.name} - {e}")
                step.status = StepStatus.SKIPPED
                return
            
            raise
    
    def rollback(self, to_step_id: Optional[str] = None) -> None:
        """
        Rollback workflow to a specific step.
        
        Args:
            to_step_id: Step ID to rollback to (None = rollback all)
        
        Raises:
            WorkflowStateError: If rollback fails
        """
        target_index = 0
        if to_step_id:
            step = self.get_step_by_id(to_step_id)
            if not step:
                raise WorkflowStateError(f"Step '{to_step_id}' not found")
            target_index = self.steps.index(step)
        
        print(f"\n↩️  Rolling back workflow...")
        
        # Rollback steps in reverse order
        for i in range(len(self.steps) - 1, target_index - 1, -1):
            step = self.steps[i]
            
            if step.status == StepStatus.COMPLETED and step.rollback:
                print(f"   Rolling back: {step.name}")
                try:
                    step.rollback(self.state)
                    step.status = StepStatus.PENDING
                except Exception as e:
                    print(f"   ⚠️  Rollback failed for {step.name}: {e}")
        
        self.current_step_index = target_index
        self._save_state()
        
        print(f"✓ Rollback complete")
    
    def summary(self) -> str:
        """
        Get workflow summary.
        
        Returns:
            Human-readable summary string
        """
        lines = [
            f"Workflow: {self.workflow_id}",
            f"Progress: {self.current_step_index}/{len(self.steps)} steps",
            f"Status: {'Completed' if self.completed_at else 'In Progress'}",
            "",
            "Steps:"
        ]
        
        for i, step in enumerate(self.steps):
            status_symbol = {
                StepStatus.PENDING: "⏸️ ",
                StepStatus.IN_PROGRESS: "⏳",
                StepStatus.COMPLETED: "✓",
                StepStatus.FAILED: "✗",
                StepStatus.SKIPPED: "⊘"
            }.get(step.status, "?")
            
            lines.append(f"  {i + 1}. {status_symbol} {step.name}")
            if step.error_message:
                lines.append(f"     Error: {step.error_message}")
        
        return "\n".join(lines)


# Example usage and helper functions

def create_boxlab_workflow() -> WorkflowOrchestrator:
    """
    Create the main BoxLab installation workflow.
    
    Returns:
        Configured WorkflowOrchestrator
    """
    workflow = WorkflowOrchestrator(
        workflow_id="boxlab_install",
        auto_save=True
    )
    
    # Define steps (these would be implemented in cli.py)
    
    def check_docker(state: Dict[str, Any]) -> Dict[str, Any]:
        """Check if Docker is installed and running."""
        import subprocess
        try:
            subprocess.run(["docker", "version"], capture_output=True, check=True)
            return {"docker_available": True}
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise WorkflowError("Docker is not installed or not running")
    
    def select_services(state: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt user to select services."""
        # This would use lib.tui.choose_many()
        # For now, placeholder
        return {"selected_services": []}
    
    def resolve_dependencies(state: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve service dependencies."""
        # This would use lib.catalog.resolve_dependencies()
        services = state.get("selected_services", [])
        return {"resolved_services": services}
    
    def collect_configuration(state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect configuration from user."""
        # This would use lib.tui.input_text(), confirm(), etc.
        return {
            "config": {
                "data_dir": "/mnt/media",
                "puid": 1000,
                "pgid": 1000
            }
        }
    
    def generate_compose_file(state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate docker-compose.yml."""
        # This would use lib.compose.generate_compose()
        return {"compose_file": "docker-compose.yml"}
    
    def set_permissions(state: Dict[str, Any]) -> Dict[str, Any]:
        """Set directory permissions."""
        # This would use lib.permissions functions
        return {}
    
    def launch_services(state: Dict[str, Any]) -> Dict[str, Any]:
        """Launch Docker services."""
        import subprocess
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
        return {"services_launched": True}
    
    # Add steps
    workflow.add_step(WorkflowStep(
        id="check_docker",
        name="Check Docker Installation",
        action=check_docker,
        description="Verify Docker is installed and running"
    ))
    
    workflow.add_step(WorkflowStep(
        id="select_services",
        name="Select Services",
        action=select_services,
        description="Choose which services to install"
    ))
    
    workflow.add_step(WorkflowStep(
        id="resolve_dependencies",
        name="Resolve Dependencies",
        action=resolve_dependencies,
        description="Add required dependency services"
    ))
    
    workflow.add_step(WorkflowStep(
        id="collect_config",
        name="Collect Configuration",
        action=collect_configuration,
        description="Gather configuration settings"
    ))
    
    workflow.add_step(WorkflowStep(
        id="generate_compose",
        name="Generate Compose File",
        action=generate_compose_file,
        description="Create docker-compose.yml"
    ))
    
    workflow.add_step(WorkflowStep(
        id="set_permissions",
        name="Set Permissions",
        action=set_permissions,
        description="Configure directory permissions",
        required=False  # Optional step
    ))
    
    workflow.add_step(WorkflowStep(
        id="launch_services",
        name="Launch Services",
        action=launch_services,
        description="Start Docker containers"
    ))
    
    return workflow


if __name__ == "__main__":
    # Example: Run workflow
    workflow = create_boxlab_workflow()
    
    print("BoxLab Installation Workflow")
    print("=" * 40)
    
    try:
        result = workflow.run()
        print("\n" + workflow.summary())
    except WorkflowError as e:
        print(f"\n❌ Error: {e}")
        print("\n" + workflow.summary())
        print(f"\nWorkflow state saved. Run again to resume from step {workflow.current_step_index + 1}.")
