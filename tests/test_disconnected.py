import unittest
from uuid import uuid4

import docker

from sabotage import disconnected


class TestDisconnected(unittest.TestCase):
    IMAGE_ALPINE = "alpine:3.9.2"
    COMMAND_WAIT = "sh -c 'trap : TERM INT; sleep 3600 & wait'"
    COMMAND_PING = "sh -c 'ping -q -c 1 -w 1 {host} > /dev/null && echo -n OK || echo -n FAIL'"

    def _create_network(self, name=None, driver="bridge"):
        name = name or str(uuid4())
        return self.client.networks.create(name, driver=driver)

    def _create_container(self, network, name=None, image=IMAGE_ALPINE, command=COMMAND_WAIT, labels=None):
        name = name or str(uuid4())
        labels = labels or {}
        return self.client.containers.create(image, name=name, network=network, command=command, labels=labels)

    def _ping(self, container, host):
        command = self.COMMAND_PING.format(host=host)
        result = container.exec_run(command)
        if isinstance(result, bytes):
            return result.decode()
        return result.output.decode()

    def setUp(self):
        self.client = docker.from_env()
        self.network = self._create_network()
        self.containers = []

    def tearDown(self):
        for container in self.containers:
            container.stop()
        self.network.remove()
        self.client.api.close()

    def test_disconnected(self):
        container1 = self._create_container(network=self.network.id)
        container2 = self._create_container(network=self.network.id)
        self.containers += [container1]
        self.containers += [container2]
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
        service_name, project_name = str(uuid4()), str(uuid4())
        container1 = self._create_container(name=service_name, network=self.network.id, labels={
            "com.docker.compose.project": project_name,
            "com.docker.compose.service": service_name,
            "com.docker.compose.container-number": "1",
        })
        container2 = self._create_container(network=self.network.id)
        self.containers += [container1]
        self.containers += [container2]
        container1.start()
        container2.start()

        with disconnected(service_name, project_name=project_name):
            res = self._ping(container2, container1.name)
            self.assertEqual(res, "FAIL")

        res = self._ping(container2, container1.name)
        self.assertEqual(res, "OK")
