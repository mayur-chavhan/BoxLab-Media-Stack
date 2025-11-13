# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) documenting significant architectural decisions made in the BoxLab project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:

```markdown
# ADR-NNNN: Title

**Status**: Proposed | Accepted | Deprecated | Superseded by ADR-XXXX

**Date**: YYYY-MM-DD

**Context**: What is the issue we're addressing?

**Decision**: What is the change we're proposing and/or doing?

**Consequences**: What becomes easier or more difficult after this decision?

**Alternatives Considered**: What other options were evaluated?
```

## Index

| ADR                                          | Title                                         | Status   | Date       |
| -------------------------------------------- | --------------------------------------------- | -------- | ---------- |
| [0001](./0001-use-python-instead-of-bash.md) | Use Python instead of Bash for CLI            | Accepted | 2024-01-15 |
| [0002](./0002-integrate-gum-for-tui.md)      | Integrate Charm's Gum for TUI                 | Accepted | 2024-01-15 |
| [0003](./0003-workflow-orchestration.md)     | Workflow Orchestration with State Persistence | Accepted | 2024-11-13 |
| [0004](./0004-workflow-orchestration.md)     | Workflow Orchestration with State Persistence | Proposed | 2024-01-15 |

## Creating New ADRs

1. Copy the template below
2. Create a new file: `NNNN-brief-title.md` (increment NNNN)
3. Fill in all sections
4. Update this README index
5. Submit for review

### Template

```markdown
# ADR-NNNN: [Title]

**Status**: Proposed

**Date**: YYYY-MM-DD

## Context

Describe the forces at play, including technological, political, social, and project-specific concerns. This section describes the problem space and why a decision is needed.

## Decision

Describe the architectural decision and how it addresses the context. Be specific about what will change.

## Consequences

### Positive

- What becomes easier
- What problems does this solve
- What benefits does this bring

### Negative

- What becomes more difficult
- What new problems might this introduce
- What are the tradeoffs

## Alternatives Considered

### Alternative 1: [Name]

**Description**: Brief description

**Pros**:

- Pro 1
- Pro 2

**Cons**:

- Con 1
- Con 2

**Why not chosen**: Explanation

### Alternative 2: [Name]

...

## References

- Link to relevant documentation
- Link to related discussions
- Link to related ADRs
```
