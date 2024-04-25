from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Optional

from aiodocker import Docker as DockerClient

from ._docker_utils import find_container, start_container, stop_container, wait_for_container

__all__ = ("sabotaged_container",)


@asynccontextmanager
async def sabotaged_container(service_name: str,
                              project_name: Optional[str] = None,
                              *,
                              wait_timeout: float = 30.0,
                              wait_interval: float = 0.01,
                              docker_client_factory: Callable[[], DockerClient] = DockerClient
                              ) -> AsyncGenerator[None, None]:
    """
    Context manager to temporarily stop and then restart a container.

    :param service_name: The name of the service for which to sabotage the container.
    :param project_name: The project name within which to find the container. If not specified,
        attempts to derive from environment.
    :param wait_timeout: The time in seconds to wait for the container to become healthy upon
        restart.
    :param wait_interval: The interval in seconds between health checks when waiting for container
        restart.
    :param docker_client_factory: A callable that returns a DockerClient instance.
    :yields: None
    """
    docker_client = docker_client_factory()

    container = None
    try:
        container = await find_container(docker_client,
                                         service_name=service_name,
                                         project_name=project_name)
        await stop_container(docker_client, container)
        yield
    finally:
        try:
            if container:
                await start_container(docker_client, container)
                await wait_for_container(docker_client, container,
                                         timeout=wait_timeout, interval=wait_interval)
        finally:
            await docker_client.close()
