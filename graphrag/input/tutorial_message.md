# Messages

In AutoGen AgentChat, *messages* facilitate communication and information exchange with other agents, orchestrators, and applications. AgentChat supports various message types, each designed for specific purposes.

## Types of Messages

At a high level, messages in AgentChat can be categorized into two types: agent-agent messages and an agent's internal events and messages.

### Agent-Agent Messages

AgentChat supports many message types for agent-to-agent communication. They belong to subclasses of the base class `BaseChatMessage`. Concrete subclasses covers basic text and multimodal communication, such as `TextMessage` and `MultiModalMessage`.

For example, the following code snippet demonstrates how to create a text message, which accepts a string content and a string source:

```python
from autogen_agentchat.messages import TextMessage

text_message = TextMessage(content="Hello, world!", source="User")
```

Similarly, the following code snippet demonstrates how to create a multimodal message, which accepts a list of strings or `Image` objects:

```python
from io import BytesIO

import requests
from autogen_agentchat.messages import MultiModalMessage
from autogen_core import Image as AGImage
from PIL import Image

pil_image = Image.open(BytesIO(requests.get("https://picsum.photos/300/200").content))
img = AGImage(pil_image)
multi_modal_message = MultiModalMessage(content=["Can you describe the content of this image?", img], source="User")
img
```

The `TextMessage` and `MultiModalMessage` we have created can be passed to agents directly via the `on_messages` method, or as tasks given to a team `run()` method. Messages are also used in the responses of an agent. We will explain these in more detail in Agents and Teams.

### Internal Events

AgentChat also supports the concept of `events` - messages that are internal to an agent. These messages are used to communicate events and information on actions *within* the agent itself, and belong to subclasses of the base class `BaseAgentEvent`.

Examples of these include `ToolCallRequestEvent`, which indicates that a request was made to call a tool, and `ToolCallExecutionEvent`, which contains the results of tool calls.

Typically, events are created by the agent itself and are contained in the `inner_messages` field of the `Response` returned from `on_messages`. If you are building a custom agent and have events that you want to communicate to other entities (e.g., a UI), you can include these in the `inner_messages` field of the `Response`. We will show examples of this in Custom Agents.

You can read about the full set of messages supported in AgentChat in the `messages` module.

## Custom Message Types

You can create custom message types by subclassing the base class `BaseChatMessage` or `BaseAgentEvent`. This allows you to define your own message formats and behaviors, tailored to your application. Custom message types are useful when you write custom agents.
