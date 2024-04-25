import json
from unittest.mock import Mock, call

from sabotage import sabotaged_network

from ._utils import create_container, create_network, docker_client_

__all__ = ("docker_client_",)  # fixtures


async def test_sabotaged_network(docker_client_: Mock):
    network_id, network_name = "<network_id>", "<network_name>"
    create_network(docker_client_, network_id=network_id, network_name=network_name)

    container_id = "<container_id>"
    service_name, project_name = "<service_name>", "<project_name>"
    create_container(docker_client_, container_id=container_id, service_name=service_name,
                     project_name=project_name, network_name=network_name)

    async with sabotaged_network(service_name, project_name,
                                 docker_client_factory=lambda: docker_client_):
        disconnect_call = call._query_json(f"networks/{network_id}/disconnect", method="POST",
                                           data=json.dumps({"Container": container_id}).encode())
        assert disconnect_call in docker_client_.mock_calls

    connect_call = call._query_json(f"networks/{network_id}/connect", method="POST",
                                    data=json.dumps({"Container": container_id}).encode())
    assert connect_call in docker_client_.mock_calls
