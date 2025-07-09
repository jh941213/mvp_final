# Quick Start

> **Note:** See [here](installation.md) for installation instructions.

Before diving into the core APIs, let's start with a simple example of two agents that count down from 10 to 1.

We first define the agent classes and their respective procedures for handling messages. We create two agent classes: Modifier and Checker. The Modifier agent modifies a number that is given and the Check agent checks the value against a condition. We also create a Message data class, which defines the messages that are passed between the agents.

```python
from dataclasses import dataclass
from typing import Callable

from autogen_core import DefaultTopicId, MessageContext, RoutedAgent, default_subscription, message_handler


@dataclass
class Message:
    content: int


@default_subscription
class Modifier(RoutedAgent):
    def __init__(self, modify_val: Callable[[int], int]) -> None:
        super().__init__("A modifier agent.")
        self._modify_val = modify_val

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        val = self._modify_val(message.content)
        print(f"{'-'*80}\nModifier:\nModified {message.content} to {val}")
        await self.publish_message(Message(content=val), DefaultTopicId())  # type: ignore


@default_subscription
class Checker(RoutedAgent):
    def __init__(self, run_until: Callable[[int], bool]) -> None:
        super().__init__("A checker agent.")
        self._run_until = run_until

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        if not self._run_until(message.content):
            print(f"{'-'*80}\nChecker:\n{message.content} passed the check, continue.")
            await self.publish_message(Message(content=message.content), DefaultTopicId())
        else:
            print(f"{'-'*80}\nChecker:\n{message.content} failed the check, stopping.")
```

You might have already noticed, the agents' logic, whether it is using model or code executor, is completely decoupled from how messages are delivered. This is the core idea: the framework provides a communication infrastructure, and the agents are responsible for their own logic. We call the communication infrastructure an **Agent Runtime**.

Agent runtime is a key concept of this framework. Besides delivering messages, it also manages agents' lifecycle. So the creation of agents are handled by the runtime.

The following code shows how to register and run the agents using `SingleThreadedAgentRuntime`, a local embedded agent runtime implementation.

> **Note:** If you are using VSCode or other Editor remember to import `asyncio` and wrap the code with `async def main() -> None:` and run the code with `asyncio.run(main())` function.

```python
from autogen_core import AgentId, SingleThreadedAgentRuntime

# Create a local embedded runtime.
runtime = SingleThreadedAgentRuntime()

# Register the modifier and checker agents by providing
# their agent types, the factory functions for creating instance and subscriptions.
await Modifier.register(
    runtime,
    "modifier",
    # Modify the value by subtracting 1
    lambda: Modifier(modify_val=lambda x: x - 1),
)

await Checker.register(
    runtime,
    "checker",
    # Run until the value is less than or equal to 1
    lambda: Checker(run_until=lambda x: x <= 1),
)

# Start the runtime and send a direct message to the checker.
runtime.start()
await runtime.send_message(Message(10), AgentId("checker", "default"))
await runtime.stop_when_idle()
```

**Output:**
```
--------------------------------------------------------------------------------
Checker:
10 passed the check, continue.
--------------------------------------------------------------------------------
Modifier:
Modified 10 to 9
--------------------------------------------------------------------------------
Checker:
9 passed the check, continue.
--------------------------------------------------------------------------------
Modifier:
Modified 9 to 8
--------------------------------------------------------------------------------
Checker:
8 passed the check, continue.
--------------------------------------------------------------------------------
Modifier:
Modified 8 to 7
--------------------------------------------------------------------------------
Checker:
7 passed the check, continue.
--------------------------------------------------------------------------------
Modifier:
Modified 7 to 6
--------------------------------------------------------------------------------
Checker:
6 passed the check, continue.
--------------------------------------------------------------------------------
Modifier:
Modified 6 to 5
--------------------------------------------------------------------------------
Checker:
5 passed the check, continue.
--------------------------------------------------------------------------------
Modifier:
Modified 5 to 4
--------------------------------------------------------------------------------
Checker:
4 passed the check, continue.
--------------------------------------------------------------------------------
Modifier:
Modified 4 to 3
--------------------------------------------------------------------------------
Checker:
3 passed the check, continue.
--------------------------------------------------------------------------------
Modifier:
Modified 3 to 2
--------------------------------------------------------------------------------
Checker:
2 passed the check, continue.
--------------------------------------------------------------------------------
Modifier:
Modified 2 to 1
--------------------------------------------------------------------------------
Checker:
1 failed the check, stopping.
```

From the agent's output, we can see the value was successfully decremented from 10 to 1 as the modifier and checker conditions dictate.

AutoGen also supports a distributed agent runtime, which can host agents running on different processes or machines, with different identities, languages and dependencies.

To learn how to use agent runtime, communication, message handling, and subscription, please continue reading the sections following this quick start.


