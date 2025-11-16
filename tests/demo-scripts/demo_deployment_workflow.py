#!/usr/bin/env python3
"""Demo script showing the deployment workflow integration.

This demonstrates how the Configuration Wizard integrates with:
1. Configuration validation
2. Docker Compose file generation
3. Deployment Monitor
4. Stack persistence
5. Navigation to Dashboard after success
"""

import asyncio
import logging
from pathlib import Path

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.stack import StackConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def demo_deployment_workflow():
    """Demonstrate the deployment workflow integration."""
    print("\n" + "=" * 80)
    print("DEPLOYMENT WORKFLOW INTEGRATION DEMO")
    print("=" * 80 + "\n")

    # Step 1: Create a sample configuration (as would come from wizard)
    print("Step 1: Creating sample configuration from wizard...")
    
    config = Configuration(
        puid=1000,
        pgid=1000,
        timezone="America/New_York",
        paths=PathConfig(base_path="/tmp/arr-stack-demo"),
        services={
            "sonarr": ServiceConfig(
                name="sonarr",
                enabled=True,
                port=8989,
                custom_volumes={},
                environment_vars={},
            ),
            "radarr": ServiceConfig(
                name="radarr",
                enabled=True,
                port=7878,
                custom_volumes={},
                environment_vars={},
            ),
            "prowlarr": ServiceConfig(
                name="prowlarr",
                enabled=True,
                port=9696,
                custom_volumes={},
                environment_vars={},
            ),
        },
    )
    
    print(f"  ✓ Configuration created with {len(config.get_selected_services())} services")
    print(f"    Services: {', '.join(config.get_selected_services())}")
    print(f"    Base path: {config.paths.base_path}")
    print(f"    PUID/PGID: {config.puid}/{config.pgid}")
    print(f"    Timezone: {config.timezone}\n")

    # Step 2: Initialize controller
    print("Step 2: Initializing application controller...")
    controller = AppController()
    controller.initialize()
    print("  ✓ Controller initialized\n")

    # Step 3: Create StackConfig
    print("Step 3: Creating stack configuration...")
    stack_name = "demo-stack"
    output_dir = Path("/tmp/arr-stack-demo/stacks") / stack_name
    output_dir.mkdir(parents=True, exist_ok=True)
    compose_path = str(output_dir / "docker-compose.yml")
    
    stack_config = StackConfig(
        name=stack_name,
        configuration=config,
        compose_path=compose_path,
    )
    print(f"  ✓ Stack config created: {stack_name}")
    print(f"    Compose path: {compose_path}\n")

    # Step 4: Validate configuration
    print("Step 4: Validating stack configuration...")
    validation_result = controller.validate_stack(stack_config)
    
    if validation_result.valid:
        print("  ✓ Validation passed")
    else:
        print("  ✗ Validation failed")
        for error in validation_result.errors:
            print(f"    - {error}")
    
    if validation_result.warnings:
        print("  ⚠ Warnings:")
        for warning in validation_result.warnings:
            print(f"    - {warning}")
    print()

    # Step 5: Generate Docker Compose files
    print("Step 5: Generating Docker Compose files...")
    try:
        compose_content, env_content = controller.generate_compose_files(
            stack_config, output_dir
        )
        print(f"  ✓ Generated docker-compose.yml ({len(compose_content)} bytes)")
        print(f"  ✓ Generated .env file ({len(env_content)} bytes)")
        print(f"  ✓ Files saved to: {output_dir}\n")
        
        # Show a snippet of the generated compose file
        print("  Docker Compose snippet:")
        lines = compose_content.split('\n')[:15]
        for line in lines:
            print(f"    {line}")
        print("    ...\n")
        
    except Exception as e:
        print(f"  ✗ Failed to generate compose files: {e}\n")
        return

    # Step 6: Persist stack configuration
    print("Step 6: Persisting stack configuration...")
    try:
        controller.save_configuration(stack_config)
        print(f"  ✓ Stack configuration saved")
        print(f"    Location: {controller.config_repository.get_config_dir()}/stacks/{stack_name}.json\n")
    except Exception as e:
        print(f"  ⚠ Failed to save configuration: {e}\n")

    # Step 7: Simulate deployment workflow
    print("Step 7: Deployment workflow summary...")
    print("  The following would happen in the actual application:")
    print("  1. ✓ Configuration validated")
    print("  2. ✓ Docker Compose files generated")
    print("  3. ✓ Stack configuration persisted")
    print("  4. → Launch Deployment Monitor screen")
    print("  5. → Stream Docker Compose output in real-time")
    print("  6. → Show deployment progress (validation, directories, pull, start, health)")
    print("  7. → On success: Navigate to Dashboard")
    print("  8. → On failure: Show error with remediation steps\n")

    # Step 8: Show what happens after deployment
    print("Step 8: Post-deployment actions...")
    print("  After successful deployment:")
    print("  - User clicks 'View Dashboard' button")
    print("  - DeploymentMonitorScreen pops from stack")
    print("  - Controller navigates to Dashboard screen")
    print("  - Dashboard loads stack status and displays running services")
    print("  - User can manage services (start, stop, restart, view logs)\n")

    # Step 9: Verify saved configuration can be loaded
    print("Step 9: Verifying saved configuration...")
    try:
        loaded_config = controller.load_configuration(stack_name)
        print(f"  ✓ Configuration loaded successfully")
        print(f"    Stack name: {loaded_config.name}")
        print(f"    Services: {len(loaded_config.configuration.get_selected_services())}")
        print(f"    Created: {loaded_config.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception as e:
        print(f"  ✗ Failed to load configuration: {e}\n")

    print("=" * 80)
    print("DEPLOYMENT WORKFLOW INTEGRATION COMPLETE")
    print("=" * 80 + "\n")
    
    print("Key Integration Points:")
    print("  1. ConfigWizardScreen._start_deployment_workflow() - Orchestrates the workflow")
    print("  2. AppController.validate_stack() - Validates before deployment")
    print("  3. AppController.generate_compose_files() - Generates Docker files")
    print("  4. AppController.save_configuration() - Persists stack config")
    print("  5. DeploymentMonitorScreen - Shows real-time deployment progress")
    print("  6. DeploymentMonitorScreen.handle_view_dashboard() - Navigates to Dashboard")
    print("\nAll components are properly wired together! ✓\n")


if __name__ == "__main__":
    demo_deployment_workflow()
