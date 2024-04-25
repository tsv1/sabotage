from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Optional

from aiodocker import Docker as DockerClient

from ._docker_utils import connect_container, disconnect_container, find_container

__all__ = ("sabotaged_network",)


@asynccontextmanager
async def sabotaged_network(service_name: str,
                            project_name: Optional[str] = None,
                            *,
                            docker_client_factory: Callable[[], DockerClient] = DockerClient
                            ) -> AsyncGenerator[None, None]:
    """
    Context manager to temporarily disconnect and then reconnect a container from its networks.

    :param service_name: The name of the service for which to sabotage the network connections.
    :param project_name: The project name within which to find the container. If not specified,
        attempts to derive from environment.
    :param docker_client_factory: A callable that returns a DockerClient instance.
    :yields: None
    """
    docker_client = docker_client_factory()

    container = None
    try:
        container = await find_container(docker_client,
                                         service_name=service_name,
                                         project_name=project_name)
        await disconnect_container(docker_client, container)
        yield
    finally:
        try:
            if container:
                await connect_container(docker_client, container)
        finally:
            await docker_client.close()
