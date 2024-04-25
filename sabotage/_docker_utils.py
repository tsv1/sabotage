import asyncio
from os import environ
from time import monotonic
from typing import List, Optional

from aiodocker import Docker as DockerClient
from aiodocker.containers import DockerContainer

__all__ = ("find_container", "start_container", "stop_container", "wait_for_container",
           "connect_container", "disconnect_container")


class DockerError(Exception):
    """Base class for Docker-related errors."""
    pass


class NoContainersFoundError(DockerError):
    """Exception raised when no containers match the given criteria."""
    pass


class MultipleContainersFoundError(DockerError):
    """Exception raised when multiple containers match the given criteria
    when only one was expected."""
    pass


class ContainerNotRunningError(DockerError):
    """Exception raised when the found container is not running."""
    pass


class ContainerUnhealthyError(DockerError):
    """Exception raised when the found container is not healthy."""
    pass


class HealthCheckTimeoutError(DockerError):
    """Exception raised when a container does not become healthy within the specified timeout."""
    pass


class ProjectNameNotFoundError(DockerError):
    """Exception raised when the project name cannot be resolved."""
    pass


async def find_container(docker_client: DockerClient, *,
                         service_name: str, project_name: Optional[str] = None) -> DockerContainer:
    project_name = project_name or environ.get("COMPOSE_PROJECT_NAME", "")
    if not project_name:
        raise ProjectNameNotFoundError(
            "No project name specified and environment variable COMPOSE_PROJECT_NAME is not set"
        )

    containers = await _search_containers(docker_client,
                                          service_name=service_name,
                                          project_name=project_name)

    if len(containers) == 0:
        raise NoContainersFoundError(
            f"No containers found for service '{service_name}' in project '{project_name}'"
        )

    if len(containers) > 1:
        raise MultipleContainersFoundError(
            f"Multiple containers found for service '{service_name}' in project '{project_name}'"
            ", expected only one"
        )

    container = containers[0]
    if container["State"]["Status"] != "running":
        raise ContainerNotRunningError(f"Container for service '{service_name}' is not running")

    health = container["State"].get("Health", {})
    if health and health["Status"] != "healthy":
        raise ContainerUnhealthyError(f"Container for service '{service_name}' is unhealthy")

    return container


async def start_container(docker_client: DockerClient, container: DockerContainer) -> None:
    """
    Start a specified Docker container.

    :param docker_client: The Docker client instance to use for API requests.
    :param container: The Docker container to start.
    """
    await container.start()  # type: ignore


async def stop_container(docker_client: DockerClient, container: DockerContainer) -> None:
    """
    Stop a specified Docker container.

    :param docker_client: The Docker client instance to use for API requests.
    :param container: The Docker container to stop.
    """
    await container.stop()  # type: ignore


async def wait_for_container(docker_client: DockerClient, container: DockerContainer, *,
                             timeout: float = 30.0, interval: float = 0.01) -> None:
    """
    Wait for a Docker container to become healthy within a given timeout.

    :param docker_client: The Docker client instance to use for API requests.
    :param container: The Docker container to monitor.
    :param timeout: The maximum time in seconds to wait for the container to become healthy.
    :param interval: The time interval in seconds between health checks.
    :raises HealthCheckTimeoutError: If the container does not become healthy within the timeout.
    """
    start_time = monotonic()
    while (monotonic() - start_time) < timeout:
        container = await docker_client.containers.get(container.id)  # type: ignore

        health = container["State"].get("Health", {})
        if health:
            if health["Status"] == "healthy":
                return
        else:
            if container["State"]["Status"] == "running":
                return

        await asyncio.sleep(interval)

    raise HealthCheckTimeoutError(f"Container did not become healthy within {timeout} seconds")


async def connect_container(docker_client: DockerClient, container: DockerContainer) -> None:
    """
    Connect a specified Docker container to its networks.

    :param docker_client: The Docker client instance to use for API requests.
    :param container: The Docker container to connect.
    """
    container_networks = set(container["NetworkSettings"]["Networks"])
    for network_name in container_networks:
        network = await docker_client.networks.get(network_name)
        await network.connect({"Container": container["Id"]})


async def disconnect_container(docker_client: DockerClient, container: DockerContainer) -> None:
    """
    Disconnect a specified Docker container from its networks.

    :param docker_client: The Docker client instance to use for API requests.
    :param container: The Docker container to disconnect.
    """
    container_networks = set(container["NetworkSettings"]["Networks"])

    networks = await docker_client.networks.list()
    for net in networks:
        network_id, network_name = net["Id"], net["Name"]
        if network_name in container_networks:
            network = await docker_client.networks.get(network_id)
            await network.disconnect({"Container": container["Id"]})


async def _search_containers(docker_client: DockerClient, *,
                             service_name: Optional[str],
                             project_name: Optional[str] = None) -> List[DockerContainer]:
    result = []

    containers = await docker_client.containers.list()  # type: ignore

    for cont in containers:
        container = await docker_client.containers.get(cont.id)  # type: ignore

        labels = container["Config"].get("Labels", {})

        dc_project = labels.get("com.docker.compose.project")
        if project_name and project_name != dc_project:
            continue

        dc_service = labels.get("com.docker.compose.service")
        if service_name and service_name != dc_service:
            continue

        result.append(container)

    return result
