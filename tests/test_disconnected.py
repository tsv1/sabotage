import unittest
from uuid import uuid4

import docker

from sabotage import disconnected


class TestDisconnected(unittest.TestCase):
    def _create_network(self, name=None, driver="bridge"):
        network = self.client.networks.create(name if name else str(uuid4()), driver=driver)
        self.networks += [network]
        return network

    def _create_container(self, network, name=None, labels=None):
        container = self.client.containers.create("alpine:3.9.2",
                                                  name=name if name else str(uuid4()),
                                                  network=network,
                                                  command="sh -c 'trap : TERM INT; sleep 3600 & wait'",
                                                  labels=labels if labels else {})
        self.containers += [container]
        return container

    def _ping(self, container, host):
        command = f"sh -c 'ping -q -c 1 -w 1 {host} > /dev/null && echo -n OK || echo -n FAIL'"
        result = container.exec_run(command)
        if isinstance(result, bytes):
            return result.decode()
        return result.output.decode()

    def setUp(self):
        self.client = docker.from_env()
        self.networks = []
        self.containers = []

    def tearDown(self):
        for container in self.containers:
            container.stop()
        for network in self.networks:
            network.remove()
        self.client.api.close()

    def test_disconnected(self):
        network = self._create_network()
        container1 = self._create_container(network.id)
        container2 = self._create_container(network.id)
        container1.start()
        container2.start()

        res = self._ping(container2, container1.name)
        self.assertEqual(res, "OK")

        with disconnected(container1.name):
            res = self._ping(container2, container1.name)
            self.assertEqual(res, "FAIL")

        res = self._ping(container2, container1.name)
        self.assertEqual(res, "OK")

    def test_disconnected_with_compose_labels(self):
        network = self._create_network()
        service_name, project_name = str(uuid4()), str(uuid4())
        container1 = self._create_container(name=service_name, network=network.id, labels={
            "com.docker.compose.project": project_name,
            "com.docker.compose.service": service_name,
            "com.docker.compose.container-number": "1",
        })
        container2 = self._create_container(network=network.id)
        container1.start()
        container2.start()

        with disconnected(service_name, project_name=project_name):
            res = self._ping(container2, container1.name)
            self.assertEqual(res, "FAIL")

        res = self._ping(container2, container1.name)
        self.assertEqual(res, "OK")
