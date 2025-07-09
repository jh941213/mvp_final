# Termination

In the previous section, we explored how to define agents, and organize them into teams that can solve tasks. However, a run can go on forever, and in many cases, we need to know when to stop them. This is the role of the termination condition.

AgentChat supports several termination condition by providing a base `TerminationCondition` class and several implementations that inherit from it.

A termination condition is a callable that takes a sequence of `BaseAgentEvent` or `BaseChatMessage` objects since the last time the condition was called, and returns a `StopMessage` if the conversation should be terminated, or `None` otherwise. Once a termination condition has been reached, it must be reset by calling `reset()` before it can be used again.

Some important things to note about termination conditions:

- They are stateful but reset automatically after each run (`run()` or `run_stream()`) is finished.
- They can be combined using the AND and OR operators.

> **Note**: For group chat teams (i.e., `RoundRobinGroupChat`, `SelectorGroupChat`, and `Swarm`), the termination condition is called after each agent responds. While a response may contain multiple inner messages, the team calls its termination condition just once for all the messages from a single response. So the condition is called with the "delta sequence" of messages since the last time it was called.

## Built-In Termination Conditions

- **MaxMessageTermination**: Stops after a specified number of messages have been produced, including both agent and task messages.
- **TextMentionTermination**: Stops when specific text or string is mentioned in a message (e.g., "TERMINATE").
- **TokenUsageTermination**: Stops when a certain number of prompt or completion tokens are used. This requires the agents to report token usage in their messages.
- **TimeoutTermination**: Stops after a specified duration in seconds.
- **HandoffTermination**: Stops when a handoff to a specific target is requested. Handoff messages can be used to build patterns such as Swarm. This is useful when you want to pause the run and allow application or user to provide input when an agent hands off to them.
- **SourceMatchTermination**: Stops after a specific agent responds.
- **ExternalTermination**: Enables programmatic control of termination from outside the run. This is useful for UI integration (e.g., "Stop" buttons in chat interfaces).
- **StopMessageTermination**: Stops when a `StopMessage` is produced by an agent.
- **TextMessageTermination**: Stops when a `TextMessage` is produced by an agent.
- **FunctionCallTermination**: Stops when a `ToolCallExecutionEvent` containing a `FunctionExecutionResult` with a matching name is produced by an agent.
- **FunctionalTermination**: Stop when a function expression is evaluated to True on the last delta sequence of messages. This is useful for quickly create custom termination conditions that are not covered by the built-in ones.

## Basic Usage

To demonstrate the characteristics of termination conditions, we'll create a team consisting of two agents: a primary agent responsible for text generation and a critic agent that reviews and provides feedback on the generated text.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    temperature=1,
    # api_key="sk-...", # Optional if you have an OPENAI_API_KEY env variable set.
)

# Create the primary agent.
primary_agent = AssistantAgent(
    "primary",
    model_client=model_client,
    system_message="You are a helpful AI assistant.",
)

# Create the critic agent.
critic_agent = AssistantAgent(
    "critic",
    model_client=model_client,
    system_message="Provide constructive feedback for every message. Respond with 'APPROVE' to when your feedbacks are addressed.",
)
```

Let's explore how termination conditions automatically reset after each run or run_stream call, allowing the team to resume its conversation from where it left off.

```python
max_msg_termination = MaxMessageTermination(max_messages=3)
round_robin_team = RoundRobinGroupChat([primary_agent, critic_agent], termination_condition=max_msg_termination)

# Use asyncio.run(...) if you are running this script as a standalone script.
await Console(round_robin_team.run_stream(task="Write a unique, Haiku about the weather in Paris"))
```

**출력:**
```
---------- user ----------
Write a unique, Haiku about the weather in Paris
---------- primary ----------
Gentle rain whispers,  
Cobblestones glisten softly—  
Paris dreams in gray.
[Prompt tokens: 30, Completion tokens: 19]
---------- critic ----------
The Haiku captures the essence of a rainy day in Paris beautifully, and the imagery is vivid. However, it's important to ensure the use of the traditional 5-7-5 syllable structure for Haikus. Your current Haiku lines are composed of 4-7-5 syllables, which slightly deviates from the form. Consider revising the first line to fit the structure.

For example:
Soft rain whispers down,  
Cobblestones glisten softly —  
Paris dreams in gray.

This revision maintains the essence of your original lines while adhering to the traditional Haiku structure.
[Prompt tokens: 70, Completion tokens: 120]
---------- Summary ----------
Number of messages: 3
Finish reason: Maximum number of messages 3 reached, current message count: 3
Total prompt tokens: 100
Total completion tokens: 139
Duration: 3.34 seconds
```

The conversation stopped after reaching the maximum message limit. Since the primary agent didn't get to respond to the feedback, let's continue the conversation.

```python
# Use asyncio.run(...) if you are running this script as a standalone script.
await Console(round_robin_team.run_stream())
```

**출력:**
```
---------- primary ----------
Thank you for your feedback. Here is the revised Haiku:

Soft rain whispers down,  
Cobblestones glisten softly —  
Paris dreams in gray.
[Prompt tokens: 181, Completion tokens: 32]
---------- critic ----------
The revised Haiku now follows the traditional 5-7-5 syllable pattern, and it still beautifully captures the atmospheric mood of Paris in the rain. The imagery and flow are both clear and evocative. Well done on making the adjustment! 

APPROVE
[Prompt tokens: 234, Completion tokens: 54]
---------- primary ----------
Thank you for your kind words and approval. I'm glad the revision meets your expectations and captures the essence of Paris. If you have any more requests or need further assistance, feel free to ask!
[Prompt tokens: 279, Completion tokens: 39]
---------- Summary ----------
Number of messages: 3
Finish reason: Maximum number of messages 3 reached, current message count: 3
Total prompt tokens: 694
Total completion tokens: 125
Duration: 6.43 seconds
```

The team continued from where it left off, allowing the primary agent to respond to the feedback.

## Combining Termination Conditions

Let's show how termination conditions can be combined using the AND (`&`) and OR (`|`) operators to create more complex termination logic. For example, we'll create a team that stops either after 10 messages are generated or when the critic agent approves a message.

```python
max_msg_termination = MaxMessageTermination(max_messages=10)
text_termination = TextMentionTermination("APPROVE")
combined_termination = max_msg_termination | text_termination

round_robin_team = RoundRobinGroupChat([primary_agent, critic_agent], termination_condition=combined_termination)

# Use asyncio.run(...) if you are running this script as a standalone script.
await Console(round_robin_team.run_stream(task="Write a unique, Haiku about the weather in Paris"))
```

**출력:**
```
---------- user ----------
Write a unique, Haiku about the weather in Paris
---------- primary ----------
Spring breeze gently hums,  
Cherry blossoms in full bloom—  
Paris wakes to life.
[Prompt tokens: 467, Completion tokens: 19]
---------- critic ----------
The Haiku beautifully captures the awakening of Paris in the spring. The imagery of a gentle spring breeze and cherry blossoms in full bloom effectively conveys the rejuvenating feel of the season. The final line, "Paris wakes to life," encapsulates the renewed energy and vibrancy of the city. The Haiku adheres to the 5-7-5 syllable structure and portrays a vivid seasonal transformation in a concise and poetic manner. Excellent work!

APPROVE
[Prompt tokens: 746, Completion tokens: 93]
---------- Summary ----------
Number of messages: 3
Finish reason: Text 'APPROVE' mentioned
Total prompt tokens: 1213
Total completion tokens: 112
Duration: 2.75 seconds
```

The conversation stopped after the critic agent approved the message, although it could have also stopped if 10 messages were generated.

Alternatively, if we want to stop the run only when both conditions are met, we can use the AND (`&`) operator.

```python
combined_termination = max_msg_termination & text_termination
```

## Custom Termination Condition

The built-in termination conditions are sufficient for most use cases. However, there may be cases where you need to implement a custom termination condition that doesn't fit into the existing ones. You can do this by subclassing the `TerminationCondition` class.

In this example, we create a custom termination condition that stops the conversation when a specific function call is made.

```python
from typing import Sequence

from autogen_agentchat.base import TerminatedException, TerminationCondition
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, StopMessage, ToolCallExecutionEvent
from autogen_core import Component
from pydantic import BaseModel
from typing_extensions import Self


class FunctionCallTerminationConfig(BaseModel):
    """Configuration for the termination condition to allow for serialization
    and deserialization of the component.
    """

    function_name: str


class FunctionCallTermination(TerminationCondition, Component[FunctionCallTerminationConfig]):
    """Terminate the conversation if a FunctionExecutionResult with a specific name is received."""

    component_config_schema = FunctionCallTerminationConfig
    component_provider_override = "autogen_agentchat.conditions.FunctionCallTermination"
    """The schema for the component configuration."""

    def __init__(self, function_name: str) -> None:
        self._terminated = False
        self._function_name = function_name

    @property
    def terminated(self) -> bool:
        return self._terminated

    async def __call__(self, messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> StopMessage | None:
        if self._terminated:
            raise TerminatedException("Termination condition has already been reached")
        for message in messages:
            if isinstance(message, ToolCallExecutionEvent):
                for execution in message.content:
                    if execution.name == self._function_name:
                        self._terminated = True
                        return StopMessage(
                            content=f"Function '{self._function_name}' was executed.",
                            source="FunctionCallTermination",
                        )
        return None

    async def reset(self) -> None:
        self._terminated = False

    def _to_config(self) -> FunctionCallTerminationConfig:
        return FunctionCallTerminationConfig(
            function_name=self._function_name,
        )

    @classmethod
    def _from_config(cls, config: FunctionCallTerminationConfig) -> Self:
        return cls(
            function_name=config.function_name,
        )
```

Let's use this new termination condition to stop the conversation when the critic agent approves a message using the approve function call.

First we create a simple function that will be called when the critic agent approves a message.

```python
def approve() -> None:
    """Approve the message when all feedbacks have been addressed."""
    pass
```

Then we create the agents. The critic agent is equipped with the approve tool.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    temperature=1,
    # api_key="sk-...", # Optional if you have an OPENAI_API_KEY env variable set.
)

# Create the primary agent.
primary_agent = AssistantAgent(
    "primary",
    model_client=model_client,
    system_message="You are a helpful AI assistant.",
)

# Create the critic agent with the approve function as a tool.
critic_agent = AssistantAgent(
    "critic",
    model_client=model_client,
    tools=[approve],  # Register the approve function as a tool.
    system_message="Provide constructive feedback. Use the approve tool to approve when all feedbacks are addressed.",
)
```

Now, we create the termination condition and the team. We run the team with the poem-writing task.

```python
function_call_termination = FunctionCallTermination(function_name="approve")
round_robin_team = RoundRobinGroupChat([primary_agent, critic_agent], termination_condition=function_call_termination)

# Use asyncio.run(...) if you are running this script as a standalone script.
await Console(round_robin_team.run_stream(task="Write a unique, Haiku about the weather in Paris"))
await model_client.close()
```

**출력:**
```
---------- user ----------
Write a unique, Haiku about the weather in Paris
---------- primary ----------
Raindrops gently fall,  
Cobblestones shine in dim light—  
Paris dreams in grey.  
---------- critic ----------
This Haiku beautifully captures a melancholic yet romantic image of Paris in the rain. The use of sensory imagery like "Raindrops gently fall" and "Cobblestones shine" effectively paints a vivid picture. It could be interesting to experiment with more distinct seasonal elements of Paris, such as incorporating the Seine River or iconic landmarks in the context of the weather. Overall, it successfully conveys the atmosphere of Paris in subtle, poetic imagery.
---------- primary ----------
Thank you for your feedback! I'm glad you enjoyed the imagery. Here's another Haiku that incorporates iconic Parisian elements:

Eiffel stands in mist,  
Seine's ripple mirrors the sky—  
Spring whispers anew.  
---------- critic ----------
[FunctionCall(id='call_QEWJZ873EG4UIEpsQHi1HsAu', arguments='{}', name='approve')]
---------- critic ----------
[FunctionExecutionResult(content='None', name='approve', call_id='call_QEWJZ873EG4UIEpsQHi1HsAu', is_error=False)]
---------- critic ----------
None
TaskResult(messages=[...], stop_reason="Function 'approve' was executed.")
```

You can see that the conversation stopped when the critic agent approved the message using the approve function call.

