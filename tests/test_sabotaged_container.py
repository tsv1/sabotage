from unittest.mock import Mock, call

from sabotage import sabotaged_container

from ._utils import create_container, docker_client_

__all__ = ("docker_client_",)  # fixtures


async def test_sabotaged_container(docker_client_: Mock):
    container_id = "<container_id>"
    service_name, project_name = "<service_name>", "<project_name>"
    create_container(docker_client_, container_id=container_id,
                     service_name=service_name, project_name=project_name)

    async with sabotaged_container(service_name, project_name,
                                   docker_client_factory=lambda: docker_client_):
        stop_call = call._query(f"containers/{container_id}/stop", method="POST", params={})
        assert stop_call in docker_client_.mock_calls

    start_call = call._query(f"containers/{container_id}/start", method="POST",
                             headers={"content-type": "application/json"}, data={})
    assert start_call in docker_client_.mock_calls
