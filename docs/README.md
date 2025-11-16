# arr Stack Manager Documentation

This directory contains all documentation for the arr Stack Manager project.

## 📚 Documentation Index

### User Guides & Fixes

- **[Workflow Fix Summary](WORKFLOW_FIX_SUMMARY.md)** - Fixes for navigation workflow issues
- **[Config Wizard Fixes](CONFIG_WIZARD_FIXES.md)** - Step counter, path validation, and browse button fixes
- **[Stack Manager Crash Fix](STACK_MANAGER_CRASH_FIX.md)** - Fixes for crashes when navigating to Stack Manager
- **[Docker Permission Fix](DOCKER_PERMISSION_FIX.md)** - How to handle Docker permission issues for sudo/root/regular users

### Implementation Tasks

Implementation documentation for completed tasks:

- [Task 13 Summary](TASK_13_SUMMARY.md)
- [Task 14 Summary](TASK_14_SUMMARY.md)
- [Task 15 Implementation](TASK_15_IMPLEMENTATION.md)
- [Task 16 Implementation](TASK_16_IMPLEMENTATION.md)
- [Task 17 Implementation](TASK_17_IMPLEMENTATION.md)
- [Task 18 Implementation](TASK_18_IMPLEMENTATION.md)
- [Task 19 Implementation](TASK_19_IMPLEMENTATION.md)
- [Task 20 Implementation](TASK_20_IMPLEMENTATION.md)
- [Task 21 Implementation](TASK_21_IMPLEMENTATION.md)
- [Task 22 Implementation](TASK_22_IMPLEMENTATION.md)
- [Task 23 Implementation](TASK_23_IMPLEMENTATION.md)

## 📁 Project Structure

```
arr-stack-manager/
├── docs/              # Documentation files (you are here)
├── tests/             # Test files
├── src/               # Source code
│   └── arr_stack_manager/
├── templates/         # Jinja2 templates for Docker Compose
└── README.md          # Main project README
```

## 🔗 Quick Links

- [Main README](../README.md) - Project overview and getting started
- [Requirements Spec](../.kiro/specs/arr-stack-manager/requirements.md) - Feature requirements
- [Design Spec](../.kiro/specs/arr-stack-manager/design.md) - Architecture and design
- [Tasks](../.kiro/specs/arr-stack-manager/tasks.md) - Implementation task list

## 📝 Documentation Guidelines

When adding new documentation:

1. **Place all `.md` files in the `docs/` folder**
2. **Use descriptive filenames** (e.g., `FEATURE_NAME_FIX.md`)
3. **Update this README** to include your new document
4. **Follow the existing format** for consistency

### Documentation Categories

- **Fixes**: Document bug fixes and their solutions
- **Implementation**: Document completed tasks and features
- **Guides**: User guides and how-to documents
- **Architecture**: Design decisions and technical architecture

## 🧪 Testing

All test files are located in the `tests/` directory. See the [tests README](../tests/README.md) for more information.
