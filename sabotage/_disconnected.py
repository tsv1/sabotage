import os
from typing import Any, Type, Optional, Dict, Callable
from types import TracebackType
from unittest.mock import sentinel as nil

from docker import DockerClient


__all__ = ("Disconnected",)


class Disconnected:
    def __init__(self, name: str, *,
                 project_name: Optional[str] = nil,
                 docker_factory: Callable[[], DockerClient] = DockerClient.from_env) -> None:
        self._environment = os.environ
        self._client = docker_factory(version="auto",  # type: ignore
                                      environment=self._environment)
        self._name = name
        self._project_name = project_name
        if self._project_name is nil:
            self._project_name = self._environment.get("COMPOSE_PROJECT_NAME")

    def __enter__(self) -> None:
        filters: Dict[str, Any] = {"status": "running"}
        if self._project_name is None:
            filters["name"] = self._name
        else:
            filters["label"] = [
                "com.docker.compose.project=" + self._project_name,
                "com.docker.compose.service=" + self._name,
            ]

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
