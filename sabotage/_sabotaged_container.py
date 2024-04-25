from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Optional

from aiodocker import Docker as DockerClient

from ._docker_utils import find_container, start_container, stop_container

__all__ = ("sabotaged_container",)


@asynccontextmanager
async def sabotaged_container(service_name: str,
                              project_name: Optional[str] = None,
                              *,
                              docker_client_factory: Callable[[], DockerClient] = DockerClient
                              ) -> AsyncGenerator[None, None]:
    docker_client = docker_client_factory()

    try:
        container = await find_container(docker_client,
                                         service_name=service_name,
                                         project_name=project_name)
        await stop_container(container)
        yield
        await start_container(container)
    finally:
        await docker_client.close()
