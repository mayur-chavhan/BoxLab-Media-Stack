# ADR-0001: Use Python instead of Bash for CLI

**Status**: Accepted

**Date**: 2024-01-15

## Context

The original BoxLab implementation used a mix of Bash scripts and Python code:

- `setup.sh` - Main entry point
- `install_gum.sh` - Gum binary installation (macOS ARM64 only)
- `update_containers.sh` - Container updates
- `remove_old_users.sh` - Cleanup utility
- `main.py` - Service selection logic

This mixed architecture created several problems:

1. **Platform Limitations**: Bash scripts only worked on Unix-like systems (Linux, macOS)
2. **Binary Management**: `install_gum.sh` only supported macOS ARM64, requiring manual installation on other platforms
3. **Maintenance Burden**: Logic duplicated between Bash and Python
4. **Error Handling**: Inconsistent error handling across languages
5. **Testing Difficulty**: Hard to test bash scripts in CI/CD
6. **User Experience**: Required users to understand both Bash and Python ecosystems

## Decision

Convert all CLI functionality to pure Python (Python 3.8+):

1. **Unified Language**: Single codebase in Python only
2. **Standard Library**: Use only Python standard library (no external dependencies except Gum binary)
3. **Cross-Platform**: Support Linux (x86_64, ARM64) and macOS (x86_64, ARM64)
4. **Module Structure**: Organize code into logical modules:
   - `lib/platform.py` - OS/architecture detection
   - `lib/setup.py` - Binary management
   - `lib/tui.py` - User interface
   - `lib/catalog.py` - Service catalog
   - `lib/compose.py` - Docker Compose generation
   - `lib/config.py` - Configuration management
   - `lib/permissions.py` - Permission handling
   - `lib/cli.py` - Main workflow
5. **Entry Point**: Single executable `./boxlab` launcher

## Consequences

### Positive

- **Cross-Platform**: Works on all major platforms without modification
- **Maintainability**: Single language, easier to understand and modify
- **Testability**: Python has excellent testing frameworks (pytest, unittest)
- **Error Handling**: Consistent exception hierarchy and error messages
- **Type Safety**: Can use type hints for better IDE support
- **Standard Library**: Rich standard library reduces external dependencies
- **Package Management**: Easy to distribute via pip/pipx in future
- **Documentation**: Python docstrings and Sphinx for docs generation

### Negative

- **Migration Effort**: Requires rewriting ~300 lines of Bash
- **Learning Curve**: Contributors must know Python (but this is common)
- **Startup Time**: Python interpreter adds ~50ms overhead vs Bash
- **Binary Size**: Python installation required (but Docker users likely have it)

## Alternatives Considered

### Alternative 1: Keep Bash Scripts

**Description**: Continue with mixed Bash/Python architecture

**Pros**:

- No migration effort required
- Bash is universally available on Unix systems
- Fast startup time

**Cons**:

- Platform limitations (no native Windows support)
- Difficult to test and maintain
- Inconsistent error handling
- Limited to macOS ARM64 for binary management

**Why not chosen**: Platform limitations and maintenance burden outweigh the benefits. Users expect modern CLI tools to work across platforms.

### Alternative 2: Use Go or Rust

**Description**: Rewrite entire CLI in compiled language

**Pros**:

- Single binary distribution
- Fast execution
- Cross-compilation for all platforms
- No runtime dependencies

**Cons**:

- Complete rewrite required (~2000+ lines)
- Steeper learning curve for contributors
- Slower iteration during development
- Overkill for a configuration/orchestration tool

**Why not chosen**: BoxLab doesn't need the performance benefits of compiled languages. Python's rapid development cycle and extensive standard library make it more suitable for a CLI tool that mostly orchestrates Docker and collects user input.

### Alternative 3: Use Node.js

**Description**: Implement CLI in JavaScript/TypeScript with Node.js

**Pros**:

- Cross-platform
- Large ecosystem (npm)
- Async I/O built-in
- Can generate single executable with pkg/nexe

**Cons**:

- Requires Node.js runtime (larger dependency)
- npm ecosystem complexity
- Less suitable for system scripting than Python
- Many contributors already know Python

**Why not chosen**: Python is more prevalent in the Docker/self-hosting community. Python's standard library has better support for system operations (subprocess, pathlib, os, platform, etc.).

## References

- [Python Documentation](https://docs.python.org/3/)
- [Cross-Platform Python Best Practices](https://docs.python-guide.org/)
- [OpenSpec Proposal](../../../openspec/changes/fix-cli-workflow-and-architecture/proposal.md)
- [Comparison Document](../../development/before-after-comparison.md)
