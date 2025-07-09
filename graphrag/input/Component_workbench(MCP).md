# Workbench (and MCP)

A Workbench provides a collection of tools that share state and resources. Different from Tool, which provides an interface to a single tool, a workbench provides an interface to call different tools and receive results as the same types.

## Using Workbench

Here is an example of how to create an agent using Workbench.

```python
import json
from dataclasses import dataclass
from typing import List

from autogen_core import (
    FunctionCall,
    MessageContext,
    RoutedAgent,
    message_handler,
)
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.tools import ToolResult, Workbench

@dataclass
class Message:
    content: str


class WorkbenchAgent(RoutedAgent):
    def __init__(
        self, model_client: ChatCompletionClient, model_context: ChatCompletionContext, workbench: Workbench
    ) -> None:
        super().__init__("An agent with a workbench")
        self._system_messages: List[LLMMessage] = [SystemMessage(content="You are a helpful AI assistant.")]
        self._model_client = model_client
        self._model_context = model_context
        self._workbench = workbench

    @message_handler
    async def handle_user_message(self, message: Message, ctx: MessageContext) -> Message:
        # Add the user message to the model context.
        await self._model_context.add_message(UserMessage(content=message.content, source="user"))
        print("---------User Message-----------")
        print(message.content)

        # Run the chat completion with the tools.
        create_result = await self._model_client.create(
            messages=self._system_messages + (await self._model_context.get_messages()),
            tools=(await self._workbench.list_tools()),
            cancellation_token=ctx.cancellation_token,
        )

        # Run tool call loop.
        while isinstance(create_result.content, list) and all(
            isinstance(call, FunctionCall) for call in create_result.content
        ):
            print("---------Function Calls-----------")
            for call in create_result.content:
                print(call)

            # Add the function calls to the model context.
            await self._model_context.add_message(AssistantMessage(content=create_result.content, source="assistant"))

            # Call the tools using the workbench.
            print("---------Function Call Results-----------")
            results: List[ToolResult] = []
            for call in create_result.content:
                result = await self._workbench.call_tool(
                    call.name, arguments=json.loads(call.arguments), cancellation_token=ctx.cancellation_token
                )
                results.append(result)
                print(result)

            # Add the function execution results to the model context.
            await self._model_context.add_message(
                FunctionExecutionResultMessage(
                    content=[
                        FunctionExecutionResult(
                            call_id=call.id,
                            content=result.to_text(),
                            is_error=result.is_error,
                            name=result.name,
                        )
                        for call, result in zip(create_result.content, results, strict=False)
                    ]
                )
            )

            # Run the chat completion again to reflect on the history and function execution results.
            create_result = await self._model_client.create(
                messages=self._system_messages + (await self._model_context.get_messages()),
                tools=(await self._workbench.list_tools()),
                cancellation_token=ctx.cancellation_token,
            )

        # Now we have a single message as the result.
        assert isinstance(create_result.content, str)

        print("---------Final Response-----------")
        print(create_result.content)

        # Add the assistant message to the model context.
        await self._model_context.add_message(AssistantMessage(content=create_result.content, source="assistant"))

        # Return the result as a message.
        return Message(content=create_result.content)
```

In this example, the agent calls the tools provided by the workbench in a loop until the model returns a final answer.

## MCP Workbench

Model Context Protocol (MCP) is a protocol for providing tools and resources to language models. An MCP server hosts a set of tools and manages their state, while an MCP client operates from the side of the language model and communicates with the server to access the tools, and to provide the language model with the context it needs to use the tools effectively.

In AutoGen, we provide McpWorkbench that implements an MCP client. You can use it to create an agent that uses tools provided by MCP servers.

### Web Browsing Agent using Playwright MCP

Here is an example of how we can use the Playwright MCP server and the WorkbenchAgent class to create a web browsing agent.

You may need to install the browser dependencies for Playwright.

```bash
# npx playwright install chrome
```

Start the Playwright MCP server in a terminal.

```bash
# npx @playwright/mcp@latest --port 8931
```

Then, create the agent using the WorkbenchAgent class and McpWorkbench with the Playwright MCP server URL.

```python
from autogen_core import AgentId, SingleThreadedAgentRuntime
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, SseServerParams

playwright_server_params = SseServerParams(
    url="http://localhost:8931/sse",
)

# Start the workbench in a context manager.
# You can also start and stop the workbench using `workbench.start()` and `workbench.stop()`.
async with McpWorkbench(playwright_server_params) as workbench:  # type: ignore
    # Create a single-threaded agent runtime.
    runtime = SingleThreadedAgentRuntime()

    # Register the agent with the runtime.
    await WorkbenchAgent.register(
        runtime=runtime,
        type="WebAgent",
        factory=lambda: WorkbenchAgent(
            model_client=OpenAIChatCompletionClient(model="gpt-4.1-nano"),
            model_context=BufferedChatCompletionContext(buffer_size=10),
            workbench=workbench,
        ),
    )

    # Start the runtime.
    runtime.start()

    # Send a message to the agent.
    await runtime.send_message(
        Message(content="Use Bing to find out the address of Microsoft Building 99"),
        recipient=AgentId("WebAgent", "default"),
    )

    # Stop the runtime.
    await runtime.stop()
```
