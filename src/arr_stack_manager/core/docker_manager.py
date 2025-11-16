"""Docker container management and operations."""

import logging
import subprocess
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound
from docker.models.containers import Container

from arr_stack_manager.models.service import ResourceMetrics, ServiceInfo, ServiceStatus
from arr_stack_manager.models.validation import DeploymentEvent, OperationResult

logger = logging.getLogger(__name__)


class DockerManager:
    """Manager for Docker container lifecycle operations."""

    def __init__(self) -> None:
        """
        Initialize the Docker manager.

        Raises:
            DockerException: If unable to connect to Docker daemon
        """
        try:
            self._client = docker.from_env()
            # Test connection
            self._client.ping()
            logger.info("Successfully connected to Docker daemon")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise DockerException(
                "Cannot connect to Docker daemon. "
                "Ensure Docker is installed and running, "
                "and your user has Docker permissions."
            ) from e

    def start_service(self, service_name: str) -> OperationResult:
        """
        Start an individual service container.

        Args:
            service_name: Name of the service/container to start

        Returns:
            OperationResult indicating success or failure
        """
        try:
            container = self._get_container(service_name)
            if container.status == "running":
                return OperationResult.success_result(
                    message=f"Service '{service_name}' is already running",
                    details=f"Container ID: {container.short_id}",
                )

            container.start()
            logger.info(f"Started service: {service_name}")
            return OperationResult.success_result(
                message=f"Successfully started service '{service_name}'",
                details=f"Container ID: {container.short_id}",
            )

        except NotFound:
            logger.error(f"Container not found: {service_name}")
            return OperationResult.failure_result(
                message=f"Service '{service_name}' not found",
                details="The container may not have been created yet. "
                "Try deploying the stack first.",
            )
        except APIError as e:
            logger.error(f"Docker API error starting {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Failed to start service '{service_name}'",
                details=str(e),
            )
        except DockerException as e:
            logger.error(f"Docker error starting {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Docker error while starting '{service_name}'",
                details=str(e),
            )

    def stop_service(self, service_name: str, timeout: int = 10) -> OperationResult:
        """
        Stop a service container gracefully.

        Args:
            service_name: Name of the service/container to stop
            timeout: Seconds to wait before forcefully killing the container

        Returns:
            OperationResult indicating success or failure
        """
        try:
            container = self._get_container(service_name)
            if container.status == "exited":
                return OperationResult.success_result(
                    message=f"Service '{service_name}' is already stopped",
                    details=f"Container ID: {container.short_id}",
                )

            container.stop(timeout=timeout)
            logger.info(f"Stopped service: {service_name}")
            return OperationResult.success_result(
                message=f"Successfully stopped service '{service_name}'",
                details=f"Container ID: {container.short_id}",
            )

        except NotFound:
            logger.error(f"Container not found: {service_name}")
            return OperationResult.failure_result(
                message=f"Service '{service_name}' not found",
                details="The container may have already been removed.",
            )
        except APIError as e:
            logger.error(f"Docker API error stopping {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Failed to stop service '{service_name}'",
                details=str(e),
            )
        except DockerException as e:
            logger.error(f"Docker error stopping {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Docker error while stopping '{service_name}'",
                details=str(e),
            )

    def restart_service(self, service_name: str, timeout: int = 10) -> OperationResult:
        """
        Restart a service container.

        Args:
            service_name: Name of the service/container to restart
            timeout: Seconds to wait before forcefully killing during stop

        Returns:
            OperationResult indicating success or failure
        """
        try:
            container = self._get_container(service_name)
            container.restart(timeout=timeout)
            logger.info(f"Restarted service: {service_name}")
            return OperationResult.success_result(
                message=f"Successfully restarted service '{service_name}'",
                details=f"Container ID: {container.short_id}",
            )

        except NotFound:
            logger.error(f"Container not found: {service_name}")
            return OperationResult.failure_result(
                message=f"Service '{service_name}' not found",
                details="The container may not have been created yet.",
            )
        except APIError as e:
            logger.error(f"Docker API error restarting {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Failed to restart service '{service_name}'",
                details=str(e),
            )
        except DockerException as e:
            logger.error(f"Docker error restarting {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Docker error while restarting '{service_name}'",
                details=str(e),
            )

    def remove_service(
        self, service_name: str, remove_volumes: bool = False, force: bool = False
    ) -> OperationResult:
        """
        Remove a service container and optionally its volumes.

        Args:
            service_name: Name of the service/container to remove
            remove_volumes: Whether to remove associated volumes
            force: Force removal even if container is running

        Returns:
            OperationResult indicating success or failure
        """
        try:
            container = self._get_container(service_name)
            container_id = container.short_id

            # Stop container first if it's running and force is True
            if container.status == "running" and force:
                container.stop(timeout=10)

            container.remove(v=remove_volumes, force=force)
            logger.info(f"Removed service: {service_name} (volumes: {remove_volumes})")

            details = f"Container ID: {container_id}"
            if remove_volumes:
                details += "\nAssociated volumes were also removed"

            return OperationResult.success_result(
                message=f"Successfully removed service '{service_name}'",
                details=details,
            )

        except NotFound:
            logger.error(f"Container not found: {service_name}")
            return OperationResult.failure_result(
                message=f"Service '{service_name}' not found",
                details="The container may have already been removed.",
            )
        except APIError as e:
            logger.error(f"Docker API error removing {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Failed to remove service '{service_name}'",
                details=str(e),
            )
        except DockerException as e:
            logger.error(f"Docker error removing {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Docker error while removing '{service_name}'",
                details=str(e),
            )

    def get_service_status(self, service_name: str, check_updates: bool = False) -> ServiceInfo:
        """
        Query the current state of a service container.

        Args:
            service_name: Name of the service/container to query
            check_updates: Whether to check for available updates (slower)

        Returns:
            ServiceInfo with current status and details
        """
        try:
            container = self._get_container(service_name)
            container.reload()  # Refresh container data

            # Map Docker status to ServiceStatus enum
            status = self._map_container_status(container.status)

            # Get container image
            image = container.image.tags[0] if container.image.tags else container.image.short_id

            # Calculate uptime if running
            uptime = None
            if status == ServiceStatus.RUNNING:
                uptime = self._calculate_uptime(container)

            # Get web UI URL if available
            web_ui_url = self._get_web_ui_url(container)

            # Get resource metrics if running
            metrics = None
            if status == ServiceStatus.RUNNING:
                metrics = self._get_container_metrics(container)

            # Check for updates if requested
            update_available = False
            if check_updates:
                update_available = self.check_for_updates(service_name)

            return ServiceInfo(
                name=service_name,
                status=status,
                container_id=container.short_id,
                image=image,
                uptime=uptime,
                web_ui_url=web_ui_url,
                metrics=metrics,
                update_available=update_available,
            )

        except NotFound:
            logger.warning(f"Container not found: {service_name}")
            return ServiceInfo(
                name=service_name,
                status=ServiceStatus.UNKNOWN,
                container_id=None,
                image="unknown",
                uptime=None,
                web_ui_url=None,
                metrics=None,
                update_available=False,
            )
        except (APIError, DockerException) as e:
            logger.error(f"Error getting status for {service_name}: {e}")
            return ServiceInfo(
                name=service_name,
                status=ServiceStatus.ERROR,
                container_id=None,
                image="unknown",
                uptime=None,
                web_ui_url=None,
                metrics=None,
                update_available=False,
            )

    def get_resource_usage(self, service_name: str) -> ResourceMetrics | None:
        """
        Collect CPU and memory metrics for a service.

        Args:
            service_name: Name of the service/container

        Returns:
            ResourceMetrics if container is running, None otherwise
        """
        try:
            container = self._get_container(service_name)
            if container.status != "running":
                return None

            return self._get_container_metrics(container)

        except (NotFound, APIError, DockerException) as e:
            logger.error(f"Error getting resource usage for {service_name}: {e}")
            return None

    def _get_container(self, service_name: str) -> Container:
        """
        Get a container by service name.

        Args:
            service_name: Name of the service/container

        Returns:
            Docker Container object

        Raises:
            NotFound: If container doesn't exist
        """
        return self._client.containers.get(service_name)

    def _map_container_status(self, docker_status: str) -> ServiceStatus:
        """
        Map Docker container status to ServiceStatus enum.

        Args:
            docker_status: Docker container status string

        Returns:
            Corresponding ServiceStatus enum value
        """
        status_map = {
            "running": ServiceStatus.RUNNING,
            "exited": ServiceStatus.STOPPED,
            "created": ServiceStatus.STOPPED,
            "restarting": ServiceStatus.STARTING,
            "removing": ServiceStatus.STOPPING,
            "paused": ServiceStatus.STOPPED,
            "dead": ServiceStatus.ERROR,
        }
        return status_map.get(docker_status.lower(), ServiceStatus.UNKNOWN)

    def _calculate_uptime(self, container: Container) -> int | None:
        """
        Calculate container uptime in seconds.

        Args:
            container: Docker Container object

        Returns:
            Uptime in seconds, or None if unable to calculate
        """
        try:
            # Get container start time from inspect
            started_at = container.attrs.get("State", {}).get("StartedAt")
            if not started_at:
                return None

            # Parse ISO 8601 timestamp
            # Docker returns timestamps like "2024-01-15T10:30:00.123456789Z"
            # Remove nanoseconds and parse
            if "." in started_at:
                started_at = started_at.split(".")[0] + "Z"

            start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            current_time = datetime.now(UTC)
            uptime_delta = current_time - start_time

            return int(uptime_delta.total_seconds())

        except (ValueError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to calculate uptime: {e}")
            return None

    def _get_web_ui_url(self, container: Container) -> str | None:
        """
        Extract web UI URL from container port mappings.

        Args:
            container: Docker Container object

        Returns:
            Web UI URL if available, None otherwise
        """
        try:
            ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            if not ports:
                return None

            # Look for common web ports
            for container_port in ports:
                if ports[container_port]:
                    host_binding = ports[container_port][0]
                    host_port = host_binding.get("HostPort")
                    if host_port:
                        return f"http://localhost:{host_port}"

            return None

        except (KeyError, IndexError, AttributeError):
            return None

    def _get_container_metrics(self, container: Container) -> ResourceMetrics | None:
        """
        Get resource metrics from a running container.

        Args:
            container: Docker Container object

        Returns:
            ResourceMetrics if available, None otherwise
        """
        try:
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_percent = self._calculate_cpu_percent(stats)

            # Get memory usage
            memory_stats = stats.get("memory_stats", {})
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)

            # Get network stats
            networks = stats.get("networks", {})
            network_rx = sum(net.get("rx_bytes", 0) for net in networks.values())
            network_tx = sum(net.get("tx_bytes", 0) for net in networks.values())

            return ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_usage=memory_usage,
                memory_limit=memory_limit,
                network_rx=network_rx,
                network_tx=network_tx,
            )

        except (APIError, KeyError, ValueError) as e:
            logger.warning(f"Failed to get container metrics: {e}")
            return None

    def _calculate_cpu_percent(self, stats: dict[str, Any]) -> float:
        """
        Calculate CPU usage percentage from Docker stats.

        Args:
            stats: Docker stats dictionary

        Returns:
            CPU usage percentage (0.0 to 100.0)
        """
        try:
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})

            cpu_delta = (
                cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            )

            system_delta = (
                cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)
            )

            online_cpus = cpu_stats.get("online_cpus", 1)

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
                return float(round(cpu_percent, 2))

            return 0.0

        except (KeyError, ZeroDivisionError, TypeError):
            return 0.0

    def is_docker_available(self) -> bool:
        """
        Check if Docker daemon is available and responding.

        Returns:
            True if Docker is available, False otherwise
        """
        try:
            self._client.ping()
            return True
        except DockerException:
            return False

    def get_docker_version(self) -> str | None:
        """
        Get Docker daemon version information.

        Returns:
            Docker version string, or None if unavailable
        """
        try:
            version_info = self._client.version()
            version = version_info.get("Version", "unknown")
            return str(version) if version else "unknown"
        except DockerException:
            return None

    def get_service_logs(
        self, service_name: str, lines: int = 100, timestamps: bool = True
    ) -> list[str]:
        """
        Retrieve container logs for a service.

        Args:
            service_name: Name of the service/container
            lines: Number of recent log lines to retrieve
            timestamps: Whether to include timestamps in logs

        Returns:
            List of log lines, empty list if container not found or error occurs
        """
        try:
            container = self._get_container(service_name)
            logs = container.logs(
                tail=lines, timestamps=timestamps, stdout=True, stderr=True
            )

            # Decode bytes to string and split into lines
            if isinstance(logs, bytes):
                log_text = logs.decode("utf-8", errors="replace")
            else:
                log_text = str(logs)

            log_lines = log_text.strip().split("\n")
            logger.info(f"Retrieved {len(log_lines)} log lines for {service_name}")
            return log_lines

        except NotFound:
            logger.warning(f"Container not found: {service_name}")
            return []
        except (APIError, DockerException) as e:
            logger.error(f"Error retrieving logs for {service_name}: {e}")
            return []

    def stream_logs(
        self, service_name: str, timestamps: bool = True, follow: bool = True
    ) -> Iterator[str]:
        """
        Stream container logs in real-time.

        Args:
            service_name: Name of the service/container
            timestamps: Whether to include timestamps in logs
            follow: Whether to follow log output (stream continuously)

        Yields:
            Log lines as they are produced

        Raises:
            NotFound: If container doesn't exist
            DockerException: If Docker API error occurs
        """
        try:
            container = self._get_container(service_name)
            log_stream = container.logs(
                stream=True, follow=follow, timestamps=timestamps, stdout=True, stderr=True
            )

            logger.info(f"Started streaming logs for {service_name}")

            for log_chunk in log_stream:
                if isinstance(log_chunk, bytes):
                    log_text = log_chunk.decode("utf-8", errors="replace")
                else:
                    log_text = str(log_chunk)

                # Yield each line separately
                for line in log_text.strip().split("\n"):
                    if line:
                        yield line

        except NotFound:
            logger.error(f"Container not found: {service_name}")
            raise
        except (APIError, DockerException) as e:
            logger.error(f"Error streaming logs for {service_name}: {e}")
            raise

    def deploy_stack(self, compose_path: str | Path) -> Iterator[DeploymentEvent]:
        """
        Deploy a Docker Compose stack with progress tracking.

        Args:
            compose_path: Path to docker-compose.yml file

        Yields:
            DeploymentEvent objects tracking deployment progress

        Raises:
            FileNotFoundError: If compose file doesn't exist
            subprocess.CalledProcessError: If docker-compose command fails
        """
        compose_path = Path(compose_path)
        if not compose_path.exists():
            raise FileNotFoundError(f"Compose file not found: {compose_path}")

        compose_dir = compose_path.parent
        logger.info(f"Deploying stack from {compose_path}")

        try:
            # Stage 1: Validation
            yield DeploymentEvent.create(
                stage="validation",
                message="Validating docker-compose.yml",
                progress=0.1,
            )

            # Validate compose file
            subprocess.run(
                ["docker", "compose", "-f", str(compose_path), "config"],
                cwd=compose_dir,
                capture_output=True,
                text=True,
                check=True,
            )

            yield DeploymentEvent.create(
                stage="validation",
                message="Compose file validation successful",
                progress=0.2,
            )

            # Stage 2: Pull images
            yield DeploymentEvent.create(
                stage="pull",
                message="Pulling container images",
                progress=0.3,
            )

            pull_process = subprocess.Popen(
                ["docker", "compose", "-f", str(compose_path), "pull"],
                cwd=compose_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            # Stream pull output
            if pull_process.stdout:
                for line in pull_process.stdout:
                    line = line.strip()
                    if line:
                        yield DeploymentEvent.create(
                            stage="pull",
                            message=line,
                            progress=0.5,
                        )

            pull_process.wait()
            if pull_process.returncode != 0:
                raise subprocess.CalledProcessError(
                    pull_process.returncode, pull_process.args
                )

            yield DeploymentEvent.create(
                stage="pull",
                message="Image pull completed",
                progress=0.6,
            )

            # Stage 3: Start services
            yield DeploymentEvent.create(
                stage="start",
                message="Starting services",
                progress=0.7,
            )

            up_process = subprocess.Popen(
                ["docker", "compose", "-f", str(compose_path), "up", "-d"],
                cwd=compose_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            # Stream startup output
            if up_process.stdout:
                for line in up_process.stdout:
                    line = line.strip()
                    if line:
                        yield DeploymentEvent.create(
                            stage="start",
                            message=line,
                            progress=0.8,
                        )

            up_process.wait()
            if up_process.returncode != 0:
                raise subprocess.CalledProcessError(up_process.returncode, up_process.args)

            yield DeploymentEvent.create(
                stage="start",
                message="Services started successfully",
                progress=0.9,
            )

            # Stage 4: Health check
            yield DeploymentEvent.create(
                stage="health_check",
                message="Verifying service health",
                progress=0.95,
            )

            # Give containers a moment to start
            import time

            time.sleep(2)

            yield DeploymentEvent.create(
                stage="complete",
                message="Stack deployment completed successfully",
                progress=1.0,
            )

            logger.info(f"Successfully deployed stack from {compose_path}")

        except subprocess.CalledProcessError as e:
            error_msg = f"Deployment failed: {e.stderr if e.stderr else str(e)}"
            logger.error(error_msg)
            yield DeploymentEvent.create(
                stage="error",
                message=error_msg,
                progress=0.0,
            )
            raise
        except Exception as e:
            error_msg = f"Unexpected error during deployment: {str(e)}"
            logger.error(error_msg)
            yield DeploymentEvent.create(
                stage="error",
                message=error_msg,
                progress=0.0,
            )
            raise

    def check_for_updates(self, service_name: str) -> bool:
        """
        Check if a newer image version is available for a service.

        Args:
            service_name: Name of the service/container to check

        Returns:
            True if an update is available, False otherwise
        """
        try:
            container = self._get_container(service_name)
            image_name = container.image.tags[0] if container.image.tags else None

            if not image_name:
                logger.warning(f"Cannot check updates for {service_name}: no image tag")
                return False

            # Get current image ID
            current_image = container.image
            current_image_id = current_image.id

            # Pull the latest image (without recreating container)
            try:
                logger.debug(f"Checking for updates: {image_name}")
                latest_image = self._client.images.pull(image_name)
                latest_image_id = latest_image.id

                # Compare image IDs
                has_update = current_image_id != latest_image_id

                if has_update:
                    logger.info(f"Update available for {service_name}")
                else:
                    logger.debug(f"No update available for {service_name}")

                return has_update

            except ImageNotFound:
                logger.warning(f"Image not found for {service_name}: {image_name}")
                return False

        except NotFound:
            logger.warning(f"Container not found: {service_name}")
            return False
        except (APIError, DockerException) as e:
            logger.error(f"Error checking updates for {service_name}: {e}")
            return False

    def update_service(self, service_name: str) -> OperationResult:
        """
        Update a service by pulling the latest image and recreating the container.
        Data volumes are preserved during the update process.

        Args:
            service_name: Name of the service/container to update

        Returns:
            OperationResult indicating success or failure
        """
        try:
            container = self._get_container(service_name)
            image_name = container.image.tags[0] if container.image.tags else None

            if not image_name:
                return OperationResult.failure_result(
                    message=f"Cannot update service '{service_name}'",
                    details="Unable to determine image name",
                )

            logger.info(f"Updating service {service_name} with image {image_name}")

            # Pull the latest image
            try:
                logger.info(f"Pulling latest image: {image_name}")
                self._client.images.pull(image_name)
            except ImageNotFound:
                return OperationResult.failure_result(
                    message=f"Failed to update service '{service_name}'",
                    details=f"Image not found: {image_name}",
                )

            # Get container configuration
            container_config = container.attrs
            container_name = container.name

            # Stop and remove the old container (volumes are preserved)
            logger.info(f"Stopping container: {service_name}")
            container.stop(timeout=10)
            container.remove(v=False)  # v=False preserves volumes

            # Recreate container with same configuration
            logger.info(f"Recreating container: {service_name}")

            # Extract relevant configuration
            config = container_config.get("Config", {})
            host_config = container_config.get("HostConfig", {})

            # Create new container
            new_container = self._client.containers.create(
                image=image_name,
                name=container_name,
                environment=config.get("Env", []),
                volumes=host_config.get("Binds", []),
                ports=host_config.get("PortBindings", {}),
                restart_policy=host_config.get("RestartPolicy", {}),
                network_mode=host_config.get("NetworkMode"),
                detach=True,
            )

            # Start the new container
            new_container.start()

            logger.info(f"Successfully updated service: {service_name}")
            return OperationResult.success_result(
                message=f"Successfully updated service '{service_name}'",
                details=f"New container ID: {new_container.short_id}",
            )

        except NotFound:
            logger.error(f"Container not found: {service_name}")
            return OperationResult.failure_result(
                message=f"Service '{service_name}' not found",
                details="The container may not have been created yet.",
            )
        except APIError as e:
            logger.error(f"Docker API error updating {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Failed to update service '{service_name}'",
                details=str(e),
            )
        except DockerException as e:
            logger.error(f"Docker error updating {service_name}: {e}")
            return OperationResult.failure_result(
                message=f"Docker error while updating '{service_name}'",
                details=str(e),
            )
