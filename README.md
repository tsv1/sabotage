# sabotage

[![Codecov](https://img.shields.io/codecov/c/github/tsv1/sabotage/master.svg?style=flat-square)](https://codecov.io/gh/tsv1/sabotage)
[![PyPI](https://img.shields.io/pypi/v/sabotage.svg?style=flat-square)](https://pypi.python.org/pypi/sabotage/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/sabotage?style=flat-square)](https://pypi.python.org/pypi/sabotage/)
[![Python Version](https://img.shields.io/pypi/pyversions/sabotage.svg?style=flat-square)](https://pypi.python.org/pypi/sabotage/)

`sabotage` is a package designed to assist developers in testing the resilience and fault tolerance of applications running in Docker containers. It offers functionality to simulate failures by either temporarily stopping containers (`sabotaged_container`) or disconnecting them from their networks (`sabotaged_network`). 

## Installation

```shell
$ pip3 install sabotage
```

## Usage

1. `sabotaged_container`

Temporarily stops a specified Docker container and restarts it after performing tasks within the context. Useful for testing how applications handle Docker container failures.

```python
import asyncio
from sabotage import sabotaged_container

async def test_container_restart():
    async with sabotaged_container(service_name="webapp"):
        # Perform actions while the container is stopped
        print("Container is temporarily stopped.")

    # Actions after the container restarts
    print("Container has restarted.")

asyncio.run(test_container_restart())
```

2. `sabotaged_network`

Disconnects and reconnects a container from its networks to simulate network issues.

```python
import asyncio
from sabotage import sabotaged_network

async def test_network_disruption():
    async with sabotaged_network(service_name="webapp"):
        # Perform actions while the network is disconnected
        print("Network is temporarily disconnected.")

    # Actions after the network is reconnected
    print("Network has been reconnected.")

asyncio.run(test_network_disruption())
```
