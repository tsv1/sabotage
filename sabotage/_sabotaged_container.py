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
