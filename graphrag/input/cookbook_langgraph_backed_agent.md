# Using LangGraph-Backed Agent

This example demonstrates how to create an AI agent using LangGraph. Based on the example in the LangGraph documentation: https://langchain-ai.github.io/langgraph/.

First install the dependencies:

```bash
# pip install langgraph langchain-openai azure-identity
```

Let's import the modules.

```python
from dataclasses import dataclass
from typing import Any, Callable, List, Literal

from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool  # pyright: ignore
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
```

Define our message type that will be used to communicate with the agent.

```python
@dataclass
class Message:
    content: str
```

Define the tools the agent will use.

```python
@tool  # pyright: ignore
def get_weather(location: str) -> str:
    """Call to surf the web."""
    # This is a placeholder, but don't tell the LLM that...
    if "sf" in location.lower() or "san francisco" in location.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."
```

Define the agent using LangGraph's API.

```python
class LangGraphToolUseAgent(RoutedAgent):
    def __init__(self, description: str, model: ChatOpenAI, tools: List[Callable[..., Any]]) -> None:  # pyright: ignore
        super().__init__(description)
        self._model = model.bind_tools(tools)  # pyright: ignore

        # Define the function that determines whether to continue or not
        def should_continue(state: MessagesState) -> Literal["tools", END]:  # type: ignore
            messages = state["messages"]
            last_message = messages[-1]
            # If the LLM makes a tool call, then we route to the "tools" node
            if last_message.tool_calls:  # type: ignore
                return "tools"
            # Otherwise, we stop (reply to the user)
            return END

        # Define the function that calls the model
        async def call_model(state: MessagesState):  # type: ignore
            messages = state["messages"]
            response = await self._model.ainvoke(messages)
            # We return a list, because this will get added to the existing list
            return {"messages": [response]}

        tool_node = ToolNode(tools)  # pyright: ignore

        # Define a new graph
        self._workflow = StateGraph(MessagesState)

        # Define the two nodes we will cycle between
        self._workflow.add_node("agent", call_model)  # pyright: ignore
        self._workflow.add_node("tools", tool_node)  # pyright: ignore

        # Set the entrypoint as `agent`
        # This means that this node is the first one called
        self._workflow.set_entry_point("agent")

        # We now add a conditional edge
        self._workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            should_continue,  # type: ignore
        )

        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        self._workflow.add_edge("tools", "agent")

        # Finally, we compile it!
        # This compiles it into a LangChain Runnable,
        # meaning you can use it as you would any other runnable.
        # Note that we're (optionally) passing the memory when compiling the graph
        self._app = self._workflow.compile()

    @message_handler
    async def handle_user_message(self, message: Message, ctx: MessageContext) -> Message:
        # Use the Runnable
        final_state = await self._app.ainvoke(
            {
                "messages": [
                    SystemMessage(
                        content="You are a helpful AI assistant. You can use tools to help answer questions."
                    ),
                    HumanMessage(content=message.content),
                ]
            },
            config={"configurable": {"thread_id": 42}},
        )
        response = Message(content=final_state["messages"][-1].content)
        return response
```

Now let's test the agent. First we need to create an agent runtime and register the agent, by providing the agent's name and a factory function that will create the agent.

```python
runtime = SingleThreadedAgentRuntime()
await LangGraphToolUseAgent.register(
    runtime,
    "langgraph_tool_use_agent",
    lambda: LangGraphToolUseAgent(
        "Tool use agent",
        ChatOpenAI(
            model="gpt-4o",
            # api_key=os.getenv("OPENAI_API_KEY"),
        ),
        # AzureChatOpenAI(
        #     azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        #     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        #     api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        #     # Using Azure Active Directory authentication.
        #     azure_ad_token_provider=get_bearer_token_provider(DefaultAzureCredential()),
        #     # Using API key.
        #     # api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        # ),
        [get_weather],
    ),
)
agent = AgentId("langgraph_tool_use_agent", key="default")
```

Start the agent runtime.

```python
runtime.start()
```

Send a direct message to the agent, and print the response.

```python
response = await runtime.send_message(Message("What's the weather in SF?"), agent)
print(response.content)
```

Stop the agent runtime.

```python
await runtime.stop()
``` 