from os import environ
from typing import List, Optional

from aiodocker import Docker as DockerClient
from aiodocker.containers import DockerContainer

__all__ = ("find_container", "start_container", "stop_container",)


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


async def start_container(container: DockerContainer) -> None:
    await container.start()  # type: ignore


async def stop_container(container: DockerContainer) -> None:
    await container.stop()  # type: ignore


async def _search_containers(docker_client: DockerClient, *,
                             service_name: Optional[str],
                             project_name: Optional[str] = None) -> List[DockerContainer]:
    result = []

    containers = await docker_client.containers.list()  # type: ignore
    for container in containers:
        await container.show()

        labels = container["Config"].get("Labels", {})

        dc_project = labels.get("com.docker.compose.project")
        if project_name and project_name != dc_project:
            continue

        dc_service = labels.get("com.docker.compose.service")
        if service_name and service_name != dc_service:
            continue

        result.append(container)

    return result
