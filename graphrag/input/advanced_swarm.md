# Swarm

Swarm implements a team in which agents can hand off task to other agents based on their capabilities. It is a multi-agent design pattern first introduced by OpenAI in Swarm. The key idea is to let agent delegate tasks to other agents using a special tool call, while all agents share the same message context. This enables agents to make local decisions about task planning, rather than relying on a central orchestrator such as in SelectorGroupChat.

> **Note**: Swarm is a high-level API. If you need more control and customization that is not supported by this API, you can take a look at the Handoff Pattern in the Core API documentation and implement your own version of the Swarm pattern.

## How Does It Work?

At its core, the Swarm team is a group chat where agents take turn to generate a response. Similar to `SelectorGroupChat` and `RoundRobinGroupChat`, participant agents broadcast their responses so all agents share the same message context.

Different from the other two group chat teams, at each turn, the speaker agent is selected based on the most recent `HandoffMessage` message in the context. This naturally requires each agent in the team to be able to generate `HandoffMessage` to signal which other agents that it hands off to.

For `AssistantAgent`, you can set the `handoffs` argument to specify which agents it can hand off to. You can use `Handoff` to customize the message content and handoff behavior.

The overall process can be summarized as follows:

1. Each agent has the ability to generate `HandoffMessage` to signal which other agents it can hand off to. For `AssistantAgent`, this means setting the `handoffs` argument.

2. When the team starts on a task, the first speaker agents operate on the task and make localized decision about whether to hand off and to whom.

3. When an agent generates a `HandoffMessage`, the receiving agent takes over the task with the same message context.

4. The process continues until a termination condition is met.

> **Note**: The `AssistantAgent` uses the tool calling capability of the model to generate handoffs. This means that the model must support tool calling. If the model does parallel tool calling, multiple handoffs may be generated at the same time. This can lead to unexpected behavior. To avoid this, you can disable parallel tool calling by configuring the model client. For `OpenAIChatCompletionClient` and `AzureOpenAIChatCompletionClient`, you can set `parallel_tool_calls=False` in the configuration.

In this section, we will show you two examples of how to use the Swarm team:

- A customer support team with human-in-the-loop handoff.
- An autonomous team for content generation.

## Customer Support Example

This system implements a flights refund scenario with two agents:

- **Travel Agent**: Handles general travel and refund coordination.
- **Flights Refunder**: Specializes in processing flight refunds with the `refund_flight` tool.

Additionally, we let the user interact with the agents, when agents handoff to "user".

### Workflow

1. The Travel Agent initiates the conversation and evaluates the user's request.
2. Based on the request:
   - For refund-related tasks, the Travel Agent hands off to the Flights Refunder.
   - For information needed from the customer, either agent can hand off to the "user".
3. The Flights Refunder processes refunds using the `refund_flight` tool when appropriate.
4. If an agent hands off to the "user", the team execution will stop and wait for the user to input a response.
5. When the user provides input, it's sent back to the team as a `HandoffMessage`. This message is directed to the agent that originally requested user input.
6. The process continues until the Travel Agent determines the task is complete and terminates the workflow.

```python
from typing import Any, Dict, List

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination
from autogen_agentchat.messages import HandoffMessage
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
```

### Tools

```python
def refund_flight(flight_id: str) -> str:
    """Refund a flight"""
    return f"Flight {flight_id} refunded"
```

### Agents

```python
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    # api_key="YOUR_API_KEY",
)

travel_agent = AssistantAgent(
    "travel_agent",
    model_client=model_client,
    handoffs=["flights_refunder", "user"],
    system_message="""You are a travel agent.
    The flights_refunder is in charge of refunding flights.
    If you need information from the user, you must first send your message, then you can handoff to the user.
    Use TERMINATE when the travel planning is complete.""",
)

flights_refunder = AssistantAgent(
    "flights_refunder",
    model_client=model_client,
    handoffs=["travel_agent", "user"],
    tools=[refund_flight],
    system_message="""You are an agent specialized in refunding flights.
    You only need flight reference numbers to refund a flight.
    You have the ability to refund a flight using the refund_flight tool.
    If you need information from the user, you must first send your message, then you can handoff to the user.
    When the transaction is complete, handoff to the travel agent to finalize.""",
)

termination = HandoffTermination(target="user") | TextMentionTermination("TERMINATE")
team = Swarm([travel_agent, flights_refunder], termination_condition=termination)
task = "I need to refund my flight."

async def run_team_stream() -> None:
    task_result = await Console(team.run_stream(task=task))
    last_message = task_result.messages[-1]

    while isinstance(last_message, HandoffMessage) and last_message.target == "user":
        user_message = input("User: ")

        task_result = await Console(
            team.run_stream(task=HandoffMessage(source="user", target=last_message.source, content=user_message))
        )
        last_message = task_result.messages[-1]

# Use asyncio.run(...) if you are running this in a script.
await run_team_stream()
await model_client.close()
```

## Stock Research Example

This system is designed to perform stock research tasks by leveraging four agents:

- **Planner**: The central coordinator that delegates specific tasks to specialized agents based on their expertise.
- **Financial Analyst**: A specialized agent responsible for analyzing financial metrics and stock data using tools such as `get_stock_data`.
- **News Analyst**: An agent focused on gathering and summarizing recent news articles relevant to the stock, using tools such as `get_news`.
- **Writer**: An agent tasked with compiling the findings from the stock and news analysis into a cohesive final report.

### Workflow

1. The Planner initiates the research process by delegating tasks to the appropriate agents in a step-by-step manner.
2. Each agent performs its task independently and appends their work to the shared message thread/history.
3. Once an agent completes its task, it hands off control back to the planner.
4. The process continues until the planner determines that all necessary tasks have been completed and decides to terminate the workflow.

### Tools

```python
async def get_stock_data(symbol: str) -> Dict[str, Any]:
    """Get stock market data for a given symbol"""
    return {"price": 180.25, "volume": 1000000, "pe_ratio": 65.4, "market_cap": "700B"}

async def get_news(query: str) -> List[Dict[str, str]]:
    """Get recent news articles about a company"""
    return [
        {
            "title": "Tesla Expands Cybertruck Production",
            "date": "2024-03-20",
            "summary": "Tesla ramps up Cybertruck manufacturing capacity at Gigafactory Texas, aiming to meet strong demand.",
        },
        {
            "title": "Tesla FSD Beta Shows Promise",
            "date": "2024-03-19",
            "summary": "Latest Full Self-Driving beta demonstrates significant improvements in urban navigation and safety features.",
        },
        {
            "title": "Model Y Dominates Global EV Sales",
            "date": "2024-03-18",
            "summary": "Tesla's Model Y becomes best-selling electric vehicle worldwide, capturing significant market share.",
        },
    ]
```

### Agents

```python
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    # api_key="YOUR_API_KEY",
)

planner = AssistantAgent(
    "planner",
    model_client=model_client,
    handoffs=["financial_analyst", "news_analyst", "writer"],
    system_message="""You are a research planning coordinator.
    Coordinate market research by delegating to specialized agents:
    - Financial Analyst: For stock data analysis
    - News Analyst: For news gathering and analysis
    - Writer: For compiling final report
    Always send your plan first, then handoff to appropriate agent.
    Always handoff to a single agent at a time.
    Use TERMINATE when research is complete.""",
)

financial_analyst = AssistantAgent(
    "financial_analyst",
    model_client=model_client,
    handoffs=["planner"],
    tools=[get_stock_data],
    system_message="""You are a financial analyst.
    Analyze stock market data using the get_stock_data tool.
    Provide insights on financial metrics.
    Always handoff back to planner when analysis is complete.""",
)

news_analyst = AssistantAgent(
    "news_analyst",
    model_client=model_client,
    handoffs=["planner"],
    tools=[get_news],
    system_message="""You are a news analyst.
    Gather and analyze relevant news using the get_news tool.
    Summarize key market insights from news.
    Always handoff back to planner when analysis is complete.""",
)

writer = AssistantAgent(
    "writer",
    model_client=model_client,
    handoffs=["planner"],
    system_message="""You are a financial report writer.
    Compile research findings into clear, concise reports.
    Always handoff back to planner when writing is complete.""",
)

# Define termination condition
text_termination = TextMentionTermination("TERMINATE")
termination = text_termination

research_team = Swarm(
    participants=[planner, financial_analyst, news_analyst, writer], 
    termination_condition=termination
)

task = "Conduct market research for TSLA stock"
await Console(research_team.run_stream(task=task))
await model_client.close()
```

---

**Navigation:**
- Previous: [Selector Group Chat](./selector-group-chat.md)
- Next: [Magentic-One](./magentic-one.md)

**On this page:**
- How Does It Work?
- Customer Support Example
- Stock Research Example

