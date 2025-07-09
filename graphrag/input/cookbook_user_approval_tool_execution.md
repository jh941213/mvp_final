# User Approval for Tool Execution using Intervention Handler

This cookbook shows how to intercept the tool execution using an intervention handler, and prompt the user for permission to execute the tool.

```python
from dataclasses import dataclass
from typing import Any, List

from autogen_core import (
    AgentId,
    AgentType,
    DefaultInterventionHandler,
    DropMessage,
    FunctionCall,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    message_handler,
)
from autogen_core.models import (
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.tool_agent import ToolAgent, ToolException, tool_agent_caller_loop
from autogen_core.tools import ToolSchema
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.code_execution import PythonCodeExecutionTool
```

Let's define a simple message type that carries a string content.

```python
@dataclass
class Message:
    content: str
```

Let's create a simple tool use agent that is capable of using tools through a ToolAgent.

```python
class ToolUseAgent(RoutedAgent):
    """An agent that uses tools to perform tasks. It executes the tools
    by itself by sending the tool execution task to a ToolAgent."""

    def __init__(
        self,
        description: str,
        system_messages: List[SystemMessage],
        model_client: ChatCompletionClient,
        tool_schema: List[ToolSchema],
        tool_agent_type: AgentType,
    ) -> None:
        super().__init__(description)
        self._model_client = model_client
        self._system_messages = system_messages
        self._tool_schema = tool_schema
        self._tool_agent_id = AgentId(type=tool_agent_type, key=self.id.key)

    @message_handler
    async def handle_user_message(self, message: Message, ctx: MessageContext) -> Message:
        """Handle a user message, execute the model and tools, and returns the response."""
        session: List[LLMMessage] = [UserMessage(content=message.content, source="User")]
        # Use the tool agent to execute the tools, and get the output messages.
        output_messages = await tool_agent_caller_loop(
            self,
            tool_agent_id=self._tool_agent_id,
            model_client=self._model_client,
            input_messages=session,
            tool_schema=self._tool_schema,
            cancellation_token=ctx.cancellation_token,
        )
        # Extract the final response from the output messages.
        final_response = output_messages[-1].content
        assert isinstance(final_response, str)
        return Message(content=final_response)
```

The tool use agent sends tool call requests to the tool agent to execute tools, so we can intercept the messages sent by the tool use agent to the tool agent to prompt the user for permission to execute the tool.

Let's create an intervention handler that intercepts the messages and prompts user for before allowing the tool execution.

```python
class ToolInterventionHandler(DefaultInterventionHandler):
    async def on_send(
        self, message: Any, *, message_context: MessageContext, recipient: AgentId
    ) -> Any | type[DropMessage]:
        if isinstance(message, FunctionCall):
            # Request user prompt for tool execution.
            user_input = input(
                f"Function call: {message.name}\nArguments: {message.arguments}\nDo you want to execute the tool? (y/n): "
            )
            if user_input.strip().lower() != "y":
                raise ToolException(content="User denied tool execution.", call_id=message.id, name=message.name)
        return message
```

Now, we can create a runtime with the intervention handler registered.

```python
# Create the runtime with the intervention handler.
runtime = SingleThreadedAgentRuntime(intervention_handlers=[ToolInterventionHandler()])
```

In this example, we will use a tool for Python code execution. First, we create a Docker-based command-line code executor using `DockerCommandLineCodeExecutor`, and then use it to instantiate a built-in Python code execution tool `PythonCodeExecutionTool` that runs code in a Docker container.

```python
# Create the docker executor for the Python code execution tool.
docker_executor = DockerCommandLineCodeExecutor()

# Create the Python code execution tool.
python_tool = PythonCodeExecutionTool(executor=docker_executor)
```

Register the agents with tools and tool schema.

```python
# Register agents.
tool_agent_type = await ToolAgent.register(
    runtime,
    "tool_executor_agent",
    lambda: ToolAgent(
        description="Tool Executor Agent",
        tools=[python_tool],
    ),
)
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
await ToolUseAgent.register(
    runtime,
    "tool_enabled_agent",
    lambda: ToolUseAgent(
        description="Tool Use Agent",
        system_messages=[SystemMessage(content="You are a helpful AI Assistant. Use your tools to solve problems.")],
        model_client=model_client,
        tool_schema=[python_tool.schema],
        tool_agent_type=tool_agent_type,
    ),
)
```

Run the agents by starting the runtime and sending a message to the tool use agent. The intervention handler will prompt you for permission to execute the tool.

```python
# Start the runtime and the docker executor.
await docker_executor.start()
runtime.start()

# Send a task to the tool user.
response = await runtime.send_message(
    Message("Run the following Python code: print('Hello, World!')"), AgentId("tool_enabled_agent", "default")
)
print(response.content)

# Stop the runtime and the docker executor.
await runtime.stop()
await docker_executor.stop()

# Close the connection to the model client.
await model_client.close()
``` 