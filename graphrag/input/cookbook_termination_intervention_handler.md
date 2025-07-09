# Termination using Intervention Handler

> **Note**
> 
> This method is valid when using `SingleThreadedAgentRuntime`.

There are many different ways to handle termination in `autogen_core`. Ultimately, the goal is to detect that the runtime no longer needs to be executed and you can proceed to finalization tasks. One way to do this is to use an `autogen_core.base.intervention.InterventionHandler` to detect a termination message and then act on it.

```python
from dataclasses import dataclass
from typing import Any

from autogen_core import (
    DefaultInterventionHandler,
    DefaultTopicId,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    default_subscription,
    message_handler,
)
```

First, we define a dataclass for regular message and message that will be used to signal termination.

```python
@dataclass
class Message:
    content: Any


@dataclass
class Termination:
    reason: str
```

We code our agent to publish a termination message when it decides it is time to terminate.

```python
@default_subscription
class AnAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("MyAgent")
        self.received = 0

    @message_handler
    async def on_new_message(self, message: Message, ctx: MessageContext) -> None:
        self.received += 1
        if self.received > 3:
            await self.publish_message(Termination(reason="Reached maximum number of messages"), DefaultTopicId())
```

Next, we create an `InterventionHandler` that will detect the termination message and act on it. This one hooks into publishes and when it encounters `Termination` it alters its internal state to indicate that termination has been requested.

```python
class TerminationHandler(DefaultInterventionHandler):
    def __init__(self) -> None:
        self._termination_value: Termination | None = None

    async def on_publish(self, message: Any, *, message_context: MessageContext) -> Any:
        if isinstance(message, Termination):
            self._termination_value = message
        return message

    @property
    def termination_value(self) -> Termination | None:
        return self._termination_value

    @property
    def has_terminated(self) -> bool:
        return self._termination_value is not None
```

Finally, we add this handler to the runtime and use it to detect termination and stop the runtime when the termination message is received.

```python
termination_handler = TerminationHandler()
runtime = SingleThreadedAgentRuntime(intervention_handlers=[termination_handler])

await AnAgent.register(runtime, "my_agent", AnAgent)

runtime.start()

# Publish more than 3 messages to trigger termination.
await runtime.publish_message(Message("hello"), DefaultTopicId())
await runtime.publish_message(Message("hello"), DefaultTopicId())
await runtime.publish_message(Message("hello"), DefaultTopicId())
await runtime.publish_message(Message("hello"), DefaultTopicId())

# Wait for termination.
await runtime.stop_when(lambda: termination_handler.has_terminated)

print(termination_handler.termination_value)
``` 