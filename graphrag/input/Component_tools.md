# Tools

Tools are code that can be executed by an agent to perform actions. A tool can be a simple function such as a calculator, or an API call to a third-party service such as stock price lookup or weather forecast. In the context of AI agents, tools are designed to be executed by agents in response to model-generated function calls.

AutoGen provides the autogen_core.tools module with a suite of built-in tools and utilities for creating and running custom tools.

## Built-in Tools

One of the built-in tools is the PythonCodeExecutionTool, which allows agents to execute Python code snippets.

Here is how you create the tool and use it.

```python
from autogen_core import CancellationToken
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool

# Create the tool.
code_executor = DockerCommandLineCodeExecutor()
await code_executor.start()
code_execution_tool = PythonCodeExecutionTool(code_executor)
cancellation_token = CancellationToken()

# Use the tool directly without an agent.
code = "print('Hello, world!')"
result = await code_execution_tool.run_json({"code": code}, cancellation_token)
print(code_execution_tool.return_value_as_string(result))
```

The DockerCommandLineCodeExecutor class is a built-in code executor that runs Python code snippets in a subprocess in the command line environment of a docker container. The PythonCodeExecutionTool class wraps the code executor and provides a simple interface to execute Python code snippets.

Examples of other built-in tools

- LocalSearchTool and GlobalSearchTool for using GraphRAG.
- mcp_server_tools for using Model Context Protocol (MCP) servers as tools.
- HttpTool for making HTTP requests to REST APIs.
- LangChainToolAdapter for using LangChain tools.

## Custom Function Tools

A tool can also be a simple Python function that performs a specific action. To create a custom function tool, you just need to create a Python function and use the FunctionTool class to wrap it.

The FunctionTool class uses descriptions and type annotations to inform the LLM when and how to use a given function. The description provides context about the function's purpose and intended use cases, while type annotations inform the LLM about the expected parameters and return type.

For example, a simple tool to obtain the stock price of a company might look like this:

```python
import random

from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool
from typing_extensions import Annotated


async def get_stock_price(ticker: str, date: Annotated[str, "Date in YYYY/MM/DD"]) -> float:
    # Returns a random stock price for demonstration purposes.
    return random.uniform(10, 200)


# Create a function tool.
stock_price_tool = FunctionTool(get_stock_price, description="Get the stock price.")

# Run the tool.
cancellation_token = CancellationToken()
result = await stock_price_tool.run_json({"ticker": "AAPL", "date": "2021/01/01"}, cancellation_token)

# Print the result.
print(stock_price_tool.return_value_as_string(result))
```

## Calling Tools with Model Clients

In AutoGen, every tool is a subclass of BaseTool, which automatically generates the JSON schema for the tool. For example, to get the JSON schema for the stock_price_tool, we can use the schema property.

```python
stock_price_tool.schema
```

Model clients use the JSON schema of the tools to generate tool calls.

Here is an example of how to use the FunctionTool class with a OpenAIChatCompletionClient. Other model client classes can be used in a similar way. See Model Clients for more details.

```python
import json

from autogen_core.models import AssistantMessage, FunctionExecutionResult, FunctionExecutionResultMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create the OpenAI chat completion client. Using OPENAI_API_KEY from environment variable.
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

# Create a user message.
user_message = UserMessage(content="What is the stock price of AAPL on 2021/01/01?", source="user")

# Run the chat completion with the stock_price_tool defined above.
cancellation_token = CancellationToken()
create_result = await model_client.create(
    messages=[user_message], tools=[stock_price_tool], cancellation_token=cancellation_token
)
create_result.content
```

What is actually going on under the hood of the call to the create method? The model client takes the list of tools and generates a JSON schema for the parameters of each tool. Then, it generates a request to the model API with the tool's JSON schema and the other messages to obtain a result.

Many models, such as OpenAI's GPT-4o and Llama-3.2, are trained to produce tool calls in the form of structured JSON strings that conform to the JSON schema of the tool. AutoGen's model clients then parse the model's response and extract the tool call from the JSON string.

The result is a list of FunctionCall objects, which can be used to run the corresponding tools.

We use json.loads to parse the JSON string in the arguments field into a Python dictionary. The run_json() method takes the dictionary and runs the tool with the provided arguments.

```python
assert isinstance(create_result.content, list)
arguments = json.loads(create_result.content[0].arguments)  # type: ignore
tool_result = await stock_price_tool.run_json(arguments, cancellation_token)
tool_result_str = stock_price_tool.return_value_as_string(tool_result)
tool_result_str
```

Now you can make another model client call to have the model generate a reflection on the result of the tool execution.

The result of the tool call is wrapped in a FunctionExecutionResult object, which contains the result of the tool execution and the ID of the tool that was called. The model client can use this information to generate a reflection on the result of the tool execution.

```python
# Create a function execution result
exec_result = FunctionExecutionResult(
    call_id=create_result.content[0].id,  # type: ignore
    content=tool_result_str,
    is_error=False,
    name=stock_price_tool.name,
)

# Make another chat completion with the history and function execution result message.
messages = [
    user_message,
    AssistantMessage(content=create_result.content, source="assistant"),  # assistant message with tool call
    FunctionExecutionResultMessage(content=[exec_result]),  # function execution result message
]
create_result = await model_client.create(messages=messages, cancellation_token=cancellation_token)  # type: ignore
print(create_result.content)
await model_client.close()
```

## Tool-Equipped Agent

Putting the model client and the tools together, you can create a tool-equipped agent that can use tools to perform actions, and reflect on the results of those actions.

> **Note**
> 
> The Core API is designed to be minimal and you need to build your own agent logic around model clients and tools. For "pre-built" agents that can use tools, please refer to the AgentChat API.

```python
import asyncio
import json
from dataclasses import dataclass
from typing import List

from autogen_core import (
    AgentId,
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
from autogen_core.tools import FunctionTool, Tool
from autogen_ext.models.openai import OpenAIChatCompletionClient


@dataclass
class Message:
    content: str


class ToolUseAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, tool_schema: List[Tool]) -> None:
        super().__init__("An agent with tools")
        self._system_messages: List[LLMMessage] = [SystemMessage(content="You are a helpful AI assistant.")]
        self._model_client = model_client
        self._tools = tool_schema

    @message_handler
    async def handle_user_message(self, message: Message, ctx: MessageContext) -> Message:
        # Create a session of messages.
        session: List[LLMMessage] = self._system_messages + [UserMessage(content=message.content, source="user")]

        # Run the chat completion with the tools.
        create_result = await self._model_client.create(
            messages=session,
            tools=self._tools,
            cancellation_token=ctx.cancellation_token,
        )

        # If there are no tool calls, return the result.
        if isinstance(create_result.content, str):
            return Message(content=create_result.content)
        assert isinstance(create_result.content, list) and all(
            isinstance(call, FunctionCall) for call in create_result.content
        )

        # Add the first model create result to the session.
        session.append(AssistantMessage(content=create_result.content, source="assistant"))

        # Execute the tool calls.
        results = await asyncio.gather(
            *[self._execute_tool_call(call, ctx.cancellation_token) for call in create_result.content]
        )

        # Add the function execution results to the session.
        session.append(FunctionExecutionResultMessage(content=results))

        # Run the chat completion again to reflect on the history and function execution results.
        create_result = await self._model_client.create(
            messages=session,
            cancellation_token=ctx.cancellation_token,
        )
        assert isinstance(create_result.content, str)

        # Return the result as a message.
        return Message(content=create_result.content)

    async def _execute_tool_call(
        self, call: FunctionCall, cancellation_token: CancellationToken
    ) -> FunctionExecutionResult:
        # Find the tool by name.
        tool = next((tool for tool in self._tools if tool.name == call.name), None)
        assert tool is not None

        # Run the tool and capture the result.
        try:
            arguments = json.loads(call.arguments)
            result = await tool.run_json(arguments, cancellation_token)
            return FunctionExecutionResult(
                call_id=call.id, content=tool.return_value_as_string(result), is_error=False, name=tool.name
            )
        except Exception as e:
            return FunctionExecutionResult(call_id=call.id, content=str(e), is_error=True, name=tool.name)
```

When handling a user message, the ToolUseAgent class first use the model client to generate a list of function calls to the tools, and then run the tools and generate a reflection on the results of the tool execution. The reflection is then returned to the user as the agent's response.

To run the agent, let's create a runtime and register the agent with the runtime.

```python
# Create the model client.
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
# Create a runtime.
runtime = SingleThreadedAgentRuntime()
# Create the tools.
tools: List[Tool] = [FunctionTool(get_stock_price, description="Get the stock price.")]
# Register the agents.
await ToolUseAgent.register(
    runtime,
    "tool_use_agent",
    lambda: ToolUseAgent(
        model_client=model_client,
        tool_schema=tools,
    ),
)
```

This example uses the OpenAIChatCompletionClient, for Azure OpenAI and other clients, see Model Clients. Let's test the agent with a question about stock price.

```python
# Start processing messages.
runtime.start()
# Send a direct message to the tool agent.
tool_use_agent = AgentId("tool_use_agent", "default")
response = await runtime.send_message(Message("What is the stock price of NVDA on 2024/06/01?"), tool_use_agent)
print(response.content)
# Stop processing messages.
await runtime.stop()
await model_client.close()
```
