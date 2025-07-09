# Message and Communication

An agent in AutoGen core can react to, send, and publish messages, and messages are the only means through which agents can communicate with each other.

## Messages

Messages are serializable objects, they can be defined using:

- A subclass of Pydantic's `pydantic.BaseModel`, or
- A dataclass

For example:

```python
from dataclasses import dataclass


@dataclass
class TextMessage:
    content: str
    source: str


@dataclass
class ImageMessage:
    url: str
    source: str
```

> **Note**
> 
> Messages are purely data, and should not contain any logic.

## Message Handlers

When an agent receives a message the runtime will invoke the agent's message handler (`on_message()`) which should implement the agents message handling logic. If this message cannot be handled by the agent, the agent should raise a `CantHandleException`.

The base class `BaseAgent` provides no message handling logic and implementing the `on_message()` method directly is not recommended unless for the advanced use cases.

Developers should start with implementing the `RoutedAgent` base class which provides built-in message routing capability.

### Routing Messages by Type

The `RoutedAgent` base class provides a mechanism for associating message types with message handlers with the `message_handler()` decorator, so developers do not need to implement the `on_message()` method.

For example, the following type-routed agent responds to `TextMessage` and `ImageMessage` using different message handlers:

```python
from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler


class MyAgent(RoutedAgent):
    @message_handler
    async def on_text_message(self, message: TextMessage, ctx: MessageContext) -> None:
        print(f"Hello, {message.source}, you said {message.content}!")

    @message_handler
    async def on_image_message(self, message: ImageMessage, ctx: MessageContext) -> None:
        print(f"Hello, {message.source}, you sent me {message.url}!")
```

Create the agent runtime and register the agent type (see Agent and Agent Runtime):

```python
runtime = SingleThreadedAgentRuntime()
await MyAgent.register(runtime, "my_agent", lambda: MyAgent("My Agent"))
```

```
AgentType(type='my_agent')
```

Test this agent with `TextMessage` and `ImageMessage`.

```python
runtime.start()
agent_id = AgentId("my_agent", "default")
await runtime.send_message(TextMessage(content="Hello, World!", source="User"), agent_id)
await runtime.send_message(ImageMessage(url="https://example.com/image.jpg", source="User"), agent_id)
await runtime.stop_when_idle()
```

```
Hello, User, you said Hello, World!!
Hello, User, you sent me https://example.com/image.jpg!
```

The runtime automatically creates an instance of `MyAgent` with the agent ID `AgentId("my_agent", "default")` when delivering the first message.

### Routing Messages of the Same Type

In some scenarios, it is useful to route messages of the same type to different handlers. For examples, messages from different sender agents should be handled differently. You can use the `match` parameter of the `message_handler()` decorator.

The `match` parameter associates handlers for the same message type to a specific message – it is secondary to the message type routing. It accepts a callable that takes the message and `MessageContext` as arguments, and returns a boolean indicating whether the message should be handled by the decorated handler. The callable is checked in the alphabetical order of the handlers.

Here is an example of an agent that routes messages based on the sender agent using the `match` parameter:

```python
class RoutedBySenderAgent(RoutedAgent):
    @message_handler(match=lambda msg, ctx: msg.source.startswith("user1"))  # type: ignore
    async def on_user1_message(self, message: TextMessage, ctx: MessageContext) -> None:
        print(f"Hello from user 1 handler, {message.source}, you said {message.content}!")

    @message_handler(match=lambda msg, ctx: msg.source.startswith("user2"))  # type: ignore
    async def on_user2_message(self, message: TextMessage, ctx: MessageContext) -> None:
        print(f"Hello from user 2 handler, {message.source}, you said {message.content}!")

    @message_handler(match=lambda msg, ctx: msg.source.startswith("user2"))  # type: ignore
    async def on_image_message(self, message: ImageMessage, ctx: MessageContext) -> None:
        print(f"Hello, {message.source}, you sent me {message.url}!")
```

The above agent uses the `source` field of the message to determine the sender agent. You can also use the `sender` field of `MessageContext` to determine the sender agent using the agent ID if available.

Let's test this agent with messages with different source values:

```python
runtime = SingleThreadedAgentRuntime()
await RoutedBySenderAgent.register(runtime, "my_agent", lambda: RoutedBySenderAgent("Routed by sender agent"))
runtime.start()
agent_id = AgentId("my_agent", "default")
await runtime.send_message(TextMessage(content="Hello, World!", source="user1-test"), agent_id)
await runtime.send_message(TextMessage(content="Hello, World!", source="user2-test"), agent_id)
await runtime.send_message(ImageMessage(url="https://example.com/image.jpg", source="user1-test"), agent_id)
await runtime.send_message(ImageMessage(url="https://example.com/image.jpg", source="user2-test"), agent_id)
await runtime.stop_when_idle()
```

```
Hello from user 1 handler, user1-test, you said Hello, World!!
Hello from user 2 handler, user2-test, you said Hello, World!!
Hello, user2-test, you sent me https://example.com/image.jpg!
```

In the above example, the first `ImageMessage` is not handled because the `source` field of the message does not match the handler's match condition.

## Direct Messaging

There are two types of communication in AutoGen core:

1. **Direct Messaging**: sends a direct message to another agent.
2. **Broadcast**: publishes a message to a topic.

Let's first look at direct messaging. To send a direct message to another agent, within a message handler use the `autogen_core.BaseAgent.send_message()` method, from the runtime use the `autogen_core.AgentRuntime.send_message()` method. Awaiting calls to these methods will return the return value of the receiving agent's message handler. When the receiving agent's handler returns `None`, `None` will be returned.

> **Note**
> 
> If the invoked agent raises an exception while the sender is awaiting, the exception will be propagated back to the sender.

### Request/Response

Direct messaging can be used for request/response scenarios, where the sender expects a response from the receiver. The receiver can respond to the message by returning a value from its message handler. You can think of this as a function call between agents.

For example, consider the following agents:

```python
from dataclasses import dataclass

from autogen_core import MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler


@dataclass
class Message:
    content: str


class InnerAgent(RoutedAgent):
    @message_handler
    async def on_my_message(self, message: Message, ctx: MessageContext) -> Message:
        return Message(content=f"Hello from inner, {message.content}")


class OuterAgent(RoutedAgent):
    def __init__(self, description: str, inner_agent_type: str):
        super().__init__(description)
        self.inner_agent_id = AgentId(inner_agent_type, self.id.key)

    @message_handler
    async def on_my_message(self, message: Message, ctx: MessageContext) -> None:
        print(f"Received message: {message.content}")
        # Send a direct message to the inner agent and receives a response.
        response = await self.send_message(Message(f"Hello from outer, {message.content}"), self.inner_agent_id)
        print(f"Received inner response: {response.content}")
```

Upone receving a message, the `OuterAgent` sends a direct message to the `InnerAgent` and receives a message in response.

We can test these agents by sending a `Message` to the `OuterAgent`.

```python
runtime = SingleThreadedAgentRuntime()
await InnerAgent.register(runtime, "inner_agent", lambda: InnerAgent("InnerAgent"))
await OuterAgent.register(runtime, "outer_agent", lambda: OuterAgent("OuterAgent", "inner_agent"))
runtime.start()
outer_agent_id = AgentId("outer_agent", "default")
await runtime.send_message(Message(content="Hello, World!"), outer_agent_id)
await runtime.stop_when_idle()
```

```
Received message: Hello, World!
Received inner response: Hello from inner, Hello from outer, Hello, World!
```

Both outputs are produced by the `OuterAgent`'s message handler, however the second output is based on the response from the `InnerAgent`.

Generally speaking, direct messaging is appropriate for scenarios when the sender and recipient are tightly coupled – they are created together and the sender is linked to a specific instance of the recipient. For example, an agent executes tool calls by sending direct messages to an instance of `ToolAgent`, and uses the responses to form an action-observation loop.

## Broadcast

Broadcast is effectively the publish/subscribe model with topic and subscription. Read Topic and Subscription to learn the core concepts.

The key difference between direct messaging and broadcast is that broadcast cannot be used for request/response scenarios. When an agent publishes a message it is one way only, it cannot receive a response from any other agent, even if a receiving agent's handler returns a value.

> **Note**
> 
> If a response is given to a published message, it will be thrown away.

> **Note**
> 
> If an agent publishes a message type for which it is subscribed it will not receive the message it published. This is to prevent infinite loops.

### Subscribe and Publish to Topics

Type-based subscription maps messages published to topics of a given topic type to agents of a given agent type. To make an agent that subsclasses `RoutedAgent` subscribe to a topic of a given topic type, you can use the `type_subscription()` class decorator.

The following example shows a `ReceiverAgent` class that subscribes to topics of "default" topic type using the `type_subscription()` decorator. and prints the received messages.

```python
from autogen_core import RoutedAgent, message_handler, type_subscription


@type_subscription(topic_type="default")
class ReceivingAgent(RoutedAgent):
    @message_handler
    async def on_my_message(self, message: Message, ctx: MessageContext) -> None:
        print(f"Received a message: {message.content}")
```

To publish a message from an agent's handler, use the `publish_message()` method and specify a `TopicId`. This call must still be awaited to allow the runtime to schedule delivery of the message to all subscribers, but it will always return `None`. If an agent raises an exception while handling a published message, this will be logged but will not be propagated back to the publishing agent.

The following example shows a `BroadcastingAgent` that publishes a message to a topic upon receiving a message.

```python
from autogen_core import TopicId


class BroadcastingAgent(RoutedAgent):
    @message_handler
    async def on_my_message(self, message: Message, ctx: MessageContext) -> None:
        await self.publish_message(
            Message("Publishing a message from broadcasting agent!"),
            topic_id=TopicId(type="default", source=self.id.key),
        )
```

`BroadcastingAgent` publishes message to a topic with type "default" and source assigned to the agent instance's agent key.

Subscriptions are registered with the agent runtime, either as part of agent type's registration or through a separate API method. Here is how we register `TypeSubscription` for the receiving agent with the `type_subscription()` decorator, and for the broadcasting agent without the decorator.

```python
from autogen_core import TypeSubscription

runtime = SingleThreadedAgentRuntime()

# Option 1: with type_subscription decorator
# The type_subscription class decorator automatically adds a TypeSubscription to
# the runtime when the agent is registered.
await ReceivingAgent.register(runtime, "receiving_agent", lambda: ReceivingAgent("Receiving Agent"))

# Option 2: with TypeSubscription
await BroadcastingAgent.register(runtime, "broadcasting_agent", lambda: BroadcastingAgent("Broadcasting Agent"))
await runtime.add_subscription(TypeSubscription(topic_type="default", agent_type="broadcasting_agent"))

# Start the runtime and publish a message.
runtime.start()
await runtime.publish_message(
    Message("Hello, World! From the runtime!"), topic_id=TopicId(type="default", source="default")
)
await runtime.stop_when_idle()
```

```
Received a message: Hello, World! From the runtime!
Received a message: Publishing a message from broadcasting agent!
```

As shown in the above example, you can also publish directly to a topic through the runtime's `publish_message()` method without the need to create an agent instance.

From the output, you can see two messages were received by the receiving agent: one was published through the runtime, and the other was published by the broadcasting agent.

### Default Topic and Subscriptions

In the above example, we used `TopicId` and `TypeSubscription` to specify the topic and subscriptions respectively. This is the appropriate way for many scenarios. However, when there is a single scope of publishing, that is, all agents publish and subscribe to all broadcasted messages, we can use the convenience classes `DefaultTopicId` and `default_subscription()` to simplify our code.

`DefaultTopicId` is for creating a topic that uses "default" as the default value for the topic type and the publishing agent's key as the default value for the topic source. `default_subscription()` is for creating a type subscription that subscribes to the default topic. We can simplify `BroadcastingAgent` by using `DefaultTopicId` and `default_subscription()`.

```python
from autogen_core import DefaultTopicId, default_subscription


@default_subscription
class BroadcastingAgentDefaultTopic(RoutedAgent):
    @message_handler
    async def on_my_message(self, message: Message, ctx: MessageContext) -> None:
        # Publish a message to all agents in the same namespace.
        await self.publish_message(
            Message("Publishing a message from broadcasting agent!"),
            topic_id=DefaultTopicId(),
        )
```

When the runtime calls `register()` to register the agent type, it creates a `TypeSubscription` whose topic type uses "default" as the default value and agent type uses the same agent type that is being registered in the same context.

```python
runtime = SingleThreadedAgentRuntime()
await BroadcastingAgentDefaultTopic.register(
    runtime, "broadcasting_agent", lambda: BroadcastingAgentDefaultTopic("Broadcasting Agent")
)
await ReceivingAgent.register(runtime, "receiving_agent", lambda: ReceivingAgent("Receiving Agent"))
runtime.start()
await runtime.publish_message(Message("Hello, World! From the runtime!"), topic_id=DefaultTopicId())
await runtime.stop_when_idle()
```

```
Received a message: Hello, World! From the runtime!
Received a message: Publishing a message from broadcasting agent!
```

> **Note**
> 
> If your scenario allows all agents to publish and subscribe to all broadcasted messages, use `DefaultTopicId` and `default_subscription()` to decorate your agent classes.
