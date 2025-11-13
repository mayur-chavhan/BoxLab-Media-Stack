# ADR-0003: Workflow Orchestration with State Persistence

**Status**: Accepted

**Date**: 2024-11-13

## Context

BoxLab's installation process involves multiple sequential steps:

1. Check Docker installation
2. Select services from catalog
3. Resolve dependencies
4. Collect configuration
5. Generate docker-compose.yml
6. Set permissions
7. Launch services

Problems with the original ad-hoc approach:

- **No Resume Capability**: If installation failed mid-way, users had to start over
- **No Progress Tracking**: Users couldn't see where they were in the process
- **State Management**: Configuration collected in early steps was lost on failure
- **Error Recovery**: No way to rollback or retry failed steps
- **Testing Difficulty**: Hard to test individual steps in isolation

Requirements:

1. Step-by-step execution with clear progress indication
2. State persistence to disk for resume capability
3. Validation hooks for each step
4. Optional rollback support
5. Graceful handling of required vs optional steps
6. Clear error messages with context

## Decision

Implement a workflow orchestration framework with:

### Core Components

1. **`WorkflowStep` dataclass**: Represents a single step with:

   - Unique ID and display name
   - Action function (callable)
   - Optional validation function
   - Optional rollback function
   - Required/optional flag
   - Status tracking

2. **`WorkflowOrchestrator` class**: Manages execution with:

   - Step registration and ordering
   - Sequential execution with state passing
   - Progress tracking (step N of M)
   - State persistence to `~/.config/boxlab/workflow-state.json`
   - Resume capability from saved state
   - Rollback support

3. **State Persistence Format**:

```json
{
  "version": 1,
  "workflow_id": "boxlab_install",
  "current_step_index": 3,
  "total_steps": 7,
  "steps": [
    {
      "id": "select_services",
      "name": "Select Services",
      "status": "completed",
      "error_message": null
    }
  ],
  "state": {
    "selected_services": ["plex", "sonarr"],
    "config": {...}
  },
  "started_at": "2024-11-13T10:30:00Z",
  "completed_at": null,
  "timestamp": "2024-11-13T10:35:00Z"
}
```

### API Design

```python
# Create workflow
workflow = WorkflowOrchestrator(
    workflow_id="boxlab_install",
    auto_save=True
)

# Define step
def select_services(state: Dict[str, Any]) -> Dict[str, Any]:
    """Step action function."""
    services = tui.choose_many("Select services:", catalog.list())
    return {"selected_services": services}

# Add step
workflow.add_step(WorkflowStep(
    id="select_services",
    name="Select Services",
    action=select_services,
    validation=lambda s: len(s.get("selected_services", [])) > 0,
    description="Choose which services to install",
    required=True
))

# Execute (automatically resumes if state exists)
result = workflow.run()
```

### Key Features

1. **Auto-Save**: State saved after each step completion
2. **Resume on Failure**: Next run automatically resumes from failure point
3. **Progress Display**: Shows "Step 3/7: Select Services"
4. **State Merging**: Each step's return value merged into global state
5. **Optional Steps**: Can skip non-required steps on failure
6. **Rollback**: Can undo steps in reverse order if rollback functions provided
7. **Summary**: Human-readable workflow status

## Consequences

### Positive

- **Resilient**: Installation can survive crashes, network issues, user interruption
- **User-Friendly**: Clear progress indication and ability to resume
- **Testable**: Each step can be tested independently
- **Maintainable**: Adding new steps is straightforward
- **Debuggable**: State file shows exactly what happened
- **Flexible**: Support for required/optional steps, validation, rollback
- **Professional UX**: Modern CLI tools should handle interruptions gracefully

### Negative

- **Complexity**: ~400 lines of orchestration code vs simple sequential calls
- **State File Management**: Must handle corrupted state files gracefully
- **Memory**: State kept in memory during execution
- **Learning Curve**: Contributors need to understand workflow pattern
- **Debugging**: Step execution happens in orchestrator, not directly

## Alternatives Considered

### Alternative 1: Simple Sequential Execution

**Description**: Just call functions in sequence without framework

```python
def run_installation():
    check_docker()
    services = select_services()
    services = resolve_dependencies(services)
    config = collect_config()
    generate_compose(services, config)
    set_permissions(config)
    launch_services()
```

**Pros**:

- Simple and easy to understand
- No framework overhead
- Direct function calls, easy to debug

**Cons**:

- No resume capability
- No progress tracking
- Lost state on failure
- Hard to test individual steps
- No rollback support

**Why not chosen**: Modern CLI tools need to handle interruptions gracefully. Users expect to be able to resume after fixing issues (like Docker not running).

### Alternative 2: Shell Script with Checkpoints

**Description**: Use bash with checkpoint files

```bash
#!/bin/bash
if [ ! -f .checkpoint-1 ]; then
    check_docker && touch .checkpoint-1
fi
if [ ! -f .checkpoint-2 ]; then
    select_services && touch .checkpoint-2
fi
# etc...
```

**Pros**:

- Simple checkpoint mechanism
- Can resume from checkpoints
- Bash is familiar to many

**Cons**:

- We already decided to move away from Bash (ADR-0001)
- State passing between steps is awkward
- No type safety
- Hard to validate or rollback
- Checkpoint files clutter working directory

**Why not chosen**: Contradicts ADR-0001 (Use Python instead of Bash). Python provides much better state management.

### Alternative 3: Use Existing Workflow Library (Luigi, Airflow, Prefect)

**Description**: Use production workflow orchestration framework

**Pros**:

- Battle-tested code
- Rich features (DAG, parallel execution, monitoring)
- Professional implementation
- Active development

**Cons**:

- **Heavy Dependencies**: Luigi (5+ deps), Airflow (100+ deps), Prefect (50+ deps)
- **Overkill**: These are designed for data pipelines and ETL, not CLI wizards
- **Complex Setup**: Require database, web UI, background workers
- **Learning Curve**: Steep learning curve for contributors
- **Installation Burden**: Users must install large dependency trees

**Why not chosen**: BoxLab aims for zero Python dependencies (only Gum binary). These frameworks are designed for complex data pipelines, not interactive CLI wizards. Our needs are simpler: sequential steps with state persistence.

### Alternative 4: State Machine Pattern

**Description**: Implement formal state machine with transitions

```python
class InstallationStateMachine:
    states = ["START", "DOCKER_CHECK", "SERVICE_SELECT", ...]
    transitions = [
        {"trigger": "check_docker", "source": "START", "dest": "DOCKER_CHECK"},
        # etc...
    ]
```

**Pros**:

- Formal model of state transitions
- Can validate state transitions
- Good for complex branching logic
- Well-understood pattern

**Cons**:

- More complex than needed for linear workflow
- State machine libraries add dependencies
- Harder to understand for contributors
- BoxLab workflow is mostly linear (few branches)

**Why not chosen**: State machines are excellent for complex workflows with many branches and conditional paths. BoxLab's installation is mostly linear with occasional optional steps. The workflow orchestrator pattern is simpler and sufficient.

### Alternative 5: Ansible Playbook

**Description**: Model installation as Ansible playbook

**Pros**:

- Idempotent by design
- Built-in state management
- Rich module ecosystem
- YAML-based, easy to read

**Cons**:

- Requires Ansible installation (Python dependency)
- Overkill for local installation wizard
- Less interactive (Ansible is for automation)
- YAML can't call Python TUI functions easily
- Learning curve for contributors

**Why not chosen**: Ansible is designed for infrastructure automation across many hosts. BoxLab is an interactive, local installation wizard. The workflow orchestrator gives us the control we need while keeping it interactive.

## Implementation Notes

### State File Location

`~/.config/boxlab/workflow-state.json` follows XDG Base Directory specification, which is standard on Linux and increasingly adopted on macOS.

### Atomic File Writes

State is written to `.tmp` file first, then atomically renamed. This prevents corruption if process is killed during write.

### Error Handling

```python
try:
    result = workflow.run()
except WorkflowError as e:
    print(f"Error: {e}")
    print(f"State saved. Run again to resume from step {workflow.current_step_index + 1}")
```

### Testing Strategy

Each step can be tested independently:

```python
def test_select_services_step():
    step = WorkflowStep(id="test", name="Test", action=select_services)
    state = {}
    result = step.action(state)
    assert "selected_services" in result
```

Full workflow can be tested with mock steps that complete instantly.

## References

- [OpenSpec Design Document](../../../openspec/changes/fix-cli-workflow-and-architecture/design.md)
- [Workflow Module Source](../../../lib/workflow.py)
- [State Pattern](https://refactoring.guru/design-patterns/state)
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
