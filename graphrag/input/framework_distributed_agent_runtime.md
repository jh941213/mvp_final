# Distributed Agent Runtime

> **Attention**
> 
> The distributed agent runtime is an experimental feature. Expect breaking changes to the API.

A distributed agent runtime facilitates communication and agent lifecycle management across process boundaries. It consists of a host service and at least one worker runtime.

The host service maintains connections to all active worker runtimes, facilitates message delivery, and keeps sessions for all direct messages (i.e., RPCs). A worker runtime processes application code (agents) and connects to the host service. It also advertises the agents which they support to the host service, so the host service can deliver messages to the correct worker.

> **Note**
> 
> The distributed agent runtime requires extra dependencies, install them using:
> 
> ```bash
> pip install "autogen-ext[grpc]"
> ```

We can start a host service using `GrpcWorkerAgentRuntimeHost`.

```python
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost

host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
host.start()  # Start a host service in the background.
```

The above code starts the host service in the background and accepts worker connections on port 50051.

Before running worker runtimes, let's define our agent. The agent will publish a new message on every message it receives. It also keeps track of how many messages it has published, and stops publishing new messages once it has published 5 messages.

```python
from dataclasses import dataclass

from autogen_core import DefaultTopicId, MessageContext, RoutedAgent, default_subscription, message_handler


@dataclass
class MyMessage:
    content: str


@default_subscription
class MyAgent(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__("My agent")
        self._name = name
        self._counter = 0

    @message_handler
    async def my_message_handler(self, message: MyMessage, ctx: MessageContext) -> None:
        self._counter += 1
        if self._counter > 5:
            return
        content = f"{self._name}: Hello x {self._counter}"
        print(content)
        await self.publish_message(MyMessage(content=content), DefaultTopicId())
```

Now we can set up the worker agent runtimes. We use `GrpcWorkerAgentRuntime`. We set up two worker runtimes. Each runtime hosts one agent. All agents publish and subscribe to the default topic, so they can see all messages being published.

To run the agents, we publish a message from a worker.

```python
import asyncio

from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime

worker1 = GrpcWorkerAgentRuntime(host_address="localhost:50051")
await worker1.start()
await MyAgent.register(worker1, "worker1", lambda: MyAgent("worker1"))

worker2 = GrpcWorkerAgentRuntime(host_address="localhost:50051")
await worker2.start()
await MyAgent.register(worker2, "worker2", lambda: MyAgent("worker2"))

await worker2.publish_message(MyMessage(content="Hello!"), DefaultTopicId())

# Let the agents run for a while.
await asyncio.sleep(5)
```

```
worker1: Hello x 1
worker2: Hello x 1
worker2: Hello x 2
worker1: Hello x 2
worker1: Hello x 3
worker2: Hello x 3
worker2: Hello x 4
worker1: Hello x 4
worker1: Hello x 5
worker2: Hello x 5
```

We can see each agent published exactly 5 messages.

To stop the worker runtimes, we can call `stop()`.

```python
await worker1.stop()
await worker2.stop()

# To keep the worker running until a termination signal is received (e.g., SIGTERM).
# await worker1.stop_when_signal()
```

We can call `stop()` to stop the host service.

```python
await host.stop()

# To keep the host service running until a termination signal (e.g., SIGTERM)
# await host.stop_when_signal()
```

## Cross-Language Runtimes

The process described above is largely the same, however all message types MUST use shared protobuf schemas for all cross-agent message types.
