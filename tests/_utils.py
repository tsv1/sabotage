from typing import Optional
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from aiodocker import Docker as DockerClient
from aiodocker.containers import DockerContainer
from aiodocker.networks import DockerNetwork

__all__ = ("docker_client_", "create_container", "create_network",)


def create_network(docker_client: DockerClient, *,
                   network_id: str,
                   network_name: str) -> DockerNetwork:
    network_spec = {
        "Id": network_id,
        "Name": network_name,
    }
    network = DockerNetwork(docker_client, network_spec["Id"])

    docker_client.networks = Mock(
        list=AsyncMock(return_value=[network_spec]),
        get=AsyncMock(return_value=network),
    )

    return network


def create_container(docker_client: DockerClient, *,
                     container_id: str,
                     project_name: str,
                     service_name: str,
                     network_name: Optional[str] = None,
                     status: Optional[str] = "running") -> DockerContainer:
    container_spec = {
        "Id": container_id,
        "Config": {
            "Labels": {
                "com.docker.compose.project": project_name,
                "com.docker.compose.service": service_name
            }
        },
        "State": {
            "Status": status
        }
    }

    if network_name:
        container_spec["NetworkSettings"] = {"Networks": [network_name]}

    container = DockerContainer(docker_client, **container_spec)

    docker_client.containers = Mock(
        list=AsyncMock(return_value=[container]),
        get=AsyncMock(return_value=container),
    )

    return container


@pytest.fixture
def docker_client_() -> MagicMock:
    docker_client = MagicMock(spec=DockerClient)
    return docker_client
