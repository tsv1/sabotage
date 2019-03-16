from typing import Any, Type, Optional, Dict, Callable
from types import TracebackType

from docker import DockerClient, from_env


__all__ = ("DisconnectedNetwork",)


class DisconnectedNetwork:
    def __init__(self, name: str, *,
                 project_name: str = None,
                 docker_factory: Callable[[], DockerClient] = from_env) -> None:
        self._name = name
        self._project_name = project_name
        self._docker_factory = docker_factory

    def __enter__(self) -> None:
        filters: Dict[str, Any] = {"status": "running"}
        if self._project_name is None:
            filters["name"] = self._name
        else:
            filters["label"] = [
                "com.docker.compose.project=" + self._project_name,
                "com.docker.compose.service=" + self._name,
            ]

        self._client = self._docker_factory()
        self._containers = self._client.containers.list(filters=filters)
        assert len(self._containers) > 0

        self._networks = self._client.networks.list()
        for network in self._networks:
            for container in self._containers:
                networks = container.attrs["NetworkSettings"]["Networks"]
                if network.name not in networks:
                    continue
                network.disconnect(container)

    def __exit__(self,
                 exception_type: Optional[Type[Exception]],
                 exception_value: Optional[Exception],
                 traceback: Optional[TracebackType]) -> bool:
        for network in self._networks:
            for container in self._containers:
                networks = container.attrs["NetworkSettings"]["Networks"]
                if network.name not in networks:
                    continue
                network.connect(container, aliases=networks[network.name]["Aliases"])
        self._client.api.close()
        return True
