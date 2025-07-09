# Selector Group Chat

`SelectorGroupChat` implements a team where participants take turns broadcasting messages to all other members. A generative model (e.g., an LLM) selects the next speaker based on the shared context, enabling dynamic, context-aware collaboration.

Key features include:

- Model-based speaker selection
- Configurable participant roles and descriptions
- Prevention of consecutive turns by the same speaker (optional)
- Customizable selection prompting
- Customizable selection function to override the default model-based selection
- Customizable candidate function to narrow-down the set of agents for selection using model

> **Note**: `SelectorGroupChat` is a high-level API. For more control and customization, refer to the Group Chat Pattern in the Core API documentation to implement your own group chat logic.

## How Does it Work?

`SelectorGroupChat` is a group chat similar to `RoundRobinGroupChat`, but with a model-based next speaker selection mechanism. When the team receives a task through `run()` or `run_stream()`, the following steps are executed:

1. The team analyzes the current conversation context, including the conversation history and participants' `name` and `description` attributes, to determine the next speaker using a model. By default, the team will not select the same speak consecutively unless it is the only agent available. This can be changed by setting `allow_repeated_speaker=True`. You can also override the model by providing a custom selection function.

2. The team prompts the selected speaker agent to provide a response, which is then broadcasted to all other participants.

3. The termination condition is checked to determine if the conversation should end, if not, the process repeats from step 1.

4. When the conversation ends, the team returns the `TaskResult` containing the conversation history from this task.

Once the team finishes the task, the conversation context is kept within the team and all participants, so the next task can continue from the previous conversation context. You can reset the conversation context by calling `reset()`.

In this section, we will demonstrate how to use `SelectorGroupChat` with a simple example for a web search and data analysis task.

## Example: Web Search/Analysis

```python
from typing import List, Sequence

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
```

### Agents

This system uses three specialized agents:

- **Planning Agent**: The strategic coordinator that breaks down complex tasks into manageable subtasks.
- **Web Search Agent**: An information retrieval specialist that interfaces with the `search_web_tool`.
- **Data Analyst Agent**: An agent specialist in performing calculations equipped with `percentage_change_tool`.

The tools `search_web_tool` and `percentage_change_tool` are external tools that the agents can use to perform their tasks.

```python
# Note: This example uses mock tools instead of real APIs for demonstration purposes
def search_web_tool(query: str) -> str:
    if "2006-2007" in query:
        return """Here are the total points scored by Miami Heat players in the 2006-2007 season:
        Udonis Haslem: 844 points
        Dwayne Wade: 1397 points
        James Posey: 550 points
        ...
        """
    elif "2007-2008" in query:
        return "The number of total rebounds for Dwayne Wade in the Miami Heat season 2007-2008 is 214."
    elif "2008-2009" in query:
        return "The number of total rebounds for Dwayne Wade in the Miami Heat season 2008-2009 is 398."
    return "No data found."


def percentage_change_tool(start: float, end: float) -> float:
    return ((end - start) / start) * 100
```

Let's create the specialized agents using the `AssistantAgent` class. It is important to note that the agents' `name` and `description` attributes are used by the model to determine the next speaker, so it is recommended to provide meaningful names and descriptions.

```python
model_client = OpenAIChatCompletionClient(model="gpt-4o")

planning_agent = AssistantAgent(
    "PlanningAgent",
    description="An agent for planning tasks, this agent should be the first to engage when given a new task.",
    model_client=model_client,
    system_message="""
    You are a planning agent.
    Your job is to break down complex tasks into smaller, manageable subtasks.
    Your team members are:
        WebSearchAgent: Searches for information
        DataAnalystAgent: Performs calculations

    You only plan and delegate tasks - you do not execute them yourself.

    When assigning tasks, use this format:
    1. <agent> : <task>

    After all tasks are complete, summarize the findings and end with "TERMINATE".
    """,
)

web_search_agent = AssistantAgent(
    "WebSearchAgent",
    description="An agent for searching information on the web.",
    tools=[search_web_tool],
    model_client=model_client,
    system_message="""
    You are a web search agent.
    Your only tool is search_tool - use it to find information.
    You make only one search call at a time.
    Once you have the results, you never do calculations based on them.
    """,
)

data_analyst_agent = AssistantAgent(
    "DataAnalystAgent",
    description="An agent for performing calculations.",
    model_client=model_client,
    tools=[percentage_change_tool],
    system_message="""
    You are a data analyst.
    Given the tasks you have been assigned, you should analyze the data and provide results using the tools provided.
    If you have not seen the data, ask for it.
    """,
)
```

> **Note**: By default, `AssistantAgent` returns the tool output as the response. If your tool does not return a well-formed string in natural language format, you may want to add a reflection step within the agent by setting `reflect_on_tool_use=True` when creating the agent. This will allow the agent to reflect on the tool output and provide a natural language response.

### Workflow

1. The task is received by the `SelectorGroupChat` which, based on agent descriptions, selects the most appropriate agent to handle the initial task (typically the Planning Agent).

2. The Planning Agent analyzes the task and breaks it down into subtasks, assigning each to the most appropriate agent using the format: `<agent> : <task>`

3. Based on the conversation context and agent descriptions, the `SelectorGroupChat` manager dynamically selects the next agent to handle their assigned subtask.

4. The Web Search Agent performs searches one at a time, storing results in the shared conversation history.

5. The Data Analyst processes the gathered information using available calculation tools when selected.

6. The workflow continues with agents being dynamically selected until either:
   - The Planning Agent determines all subtasks are complete and sends "TERMINATE"
   - An alternative termination condition is met (e.g., a maximum number of messages)

When defining your agents, make sure to include a helpful description since this is used to decide which agent to select next.

### Termination Conditions

Let's use two termination conditions: `TextMentionTermination` to end the conversation when the Planning Agent sends "TERMINATE", and `MaxMessageTermination` to limit the conversation to 25 messages to avoid infinite loop.

```python
text_mention_termination = TextMentionTermination("TERMINATE")
max_messages_termination = MaxMessageTermination(max_messages=25)
termination = text_mention_termination | max_messages_termination
```

### Selector Prompt

`SelectorGroupChat` uses a model to select the next speaker based on the conversation context. We will use a custom selector prompt to properly align with the workflow.

```python
selector_prompt = """Select an agent to perform task.

{roles}

Current conversation context:
{history}

Read the above conversation, then select an agent from {participants} to perform the next task.
Make sure the planner agent has assigned tasks before other agents start working.
Only select one agent.
"""
```

The string variables available in the selector prompt are:

- `{participants}`: The names of candidates for selection. The format is `["<name1>", "<name2>", ...]`.
- `{roles}`: A newline-separated list of names and descriptions of the candidate agents. The format for each line is: `"<name> : <description>"`.
- `{history}`: The conversation history formatted as a double newline separated of names and message content. The format for each message is: `"<name> : <message content>"`.

> **Tip**: Try not to overload the model with too much instruction in the selector prompt.
>
> What is too much? It depends on the capabilities of the model you are using. For GPT-4o and equivalents, you can use a selector prompt with a condition for when each speaker should be selected. For smaller models such as Phi-4, you should keep the selector prompt as simple as possible such as the one used in this example.
>
> Generally, if you find yourself writing multiple conditions for each agent, it is a sign that you should consider using a custom selection function, or breaking down the task into smaller, sequential tasks to be handled by separate agents or teams.

### Running the Team

Let's create the team with the agents, termination conditions, and custom selector prompt.

```python
team = SelectorGroupChat(
    [planning_agent, web_search_agent, data_analyst_agent],
    model_client=model_client,
    termination_condition=termination,
    selector_prompt=selector_prompt,
    allow_repeated_speaker=True,  # Allow an agent to speak multiple turns in a row.
)
```

Now we run the team with a task to find information about an NBA player.

```python
task = "Who was the Miami Heat player with the highest points in the 2006-2007 season, and what was the percentage change in his total rebounds between the 2007-2008 and 2008-2009 seasons?"
# Use asyncio.run(...) if you are running this in a script.
await Console(team.run_stream(task=task))
```

**출력:**
```
---------- user ----------
Who was the Miami Heat player with the highest points in the 2006-2007 season, and what was the percentage change in his total rebounds between the 2007-2008 and 2008-2009 seasons?
---------- PlanningAgent ----------
To complete this task, we need to perform the following subtasks:

1. Find out which Miami Heat player had the highest points in the 2006-2007 season.
2. Gather data on this player's total rebounds for the 2007-2008 season.
3. Gather data on this player's total rebounds for the 2008-2009 season.
4. Calculate the percentage change in the player's total rebounds between the 2007-2008 and 2008-2009 seasons.

I'll assign these tasks accordingly:

1. WebSearchAgent: Search for the Miami Heat player with the highest points in the 2006-2007 NBA season.
2. WebSearchAgent: Find the total rebounds for this player in the 2007-2008 NBA season.
3. WebSearchAgent: Find the total rebounds for this player in the 2008-2009 NBA season.
4. DataAnalystAgent: Calculate the percentage change in total rebounds from the 2007-2008 season to the 2008-2009 season for this player.
---------- WebSearchAgent ----------
[FunctionCall(id='call_89tUNHaAM0kKQYPJLleGUKK7', arguments='{"query":"Miami Heat player highest points 2006-2007 season"}', name='search_web_tool')]
---------- WebSearchAgent ----------
[FunctionExecutionResult(content='Here are the total points scored by Miami Heat players in the 2006-2007 season:\n        Udonis Haslem: 844 points\n        Dwayne Wade: 1397 points\n        James Posey: 550 points\n        ...\n        ', name='search_web_tool', call_id='call_89tUNHaAM0kKQYPJLleGUKK7', is_error=False)]
---------- WebSearchAgent ----------
Here are the total points scored by Miami Heat players in the 2006-2007 season:
        Udonis Haslem: 844 points
        Dwayne Wade: 1397 points
        James Posey: 550 points
        ...
---------- WebSearchAgent ----------
The Miami Heat player with the highest points in the 2006-2007 season was Dwyane Wade, with 1,397 points.

Next, I will search for Dwyane Wade's total rebounds for the 2007-2008 season.
---------- WebSearchAgent ----------
[FunctionCall(id='call_RC55TkSjG3JXRuVOTPrcE1RL', arguments='{"query":"Dwyane Wade total rebounds 2007-2008 season"}', name='search_web_tool')]
---------- WebSearchAgent ----------
[FunctionExecutionResult(content='The number of total rebounds for Dwayne Wade in the Miami Heat season 2007-2008 is 214.', name='search_web_tool', call_id='call_RC55TkSjG3JXRuVOTPrcE1RL', is_error=False)]
---------- WebSearchAgent ----------
The number of total rebounds for Dwayne Wade in the Miami Heat season 2007-2008 is 214.
---------- WebSearchAgent ----------
[FunctionCall(id='call_pBXoABrErDow0rZjw3tjOZol', arguments='{"query":"Dwyane Wade total rebounds 2008-2009 season"}', name='search_web_tool')]
---------- WebSearchAgent ----------
[FunctionExecutionResult(content='The number of total rebounds for Dwayne Wade in the Miami Heat season 2008-2009 is 398.', name='search_web_tool', call_id='call_pBXoABrErDow0rZjw3tjOZol', is_error=False)]
---------- WebSearchAgent ----------
The number of total rebounds for Dwayne Wade in the Miami Heat season 2008-2009 is 398.
---------- DataAnalystAgent ----------
[FunctionCall(id='call_qMxxXtcJsiK8KFSSCx3zm0is', arguments='{"start":214,"end":398}', name='percentage_change_tool')]
---------- DataAnalystAgent ----------
[FunctionExecutionResult(content='85.98130841121495', name='percentage_change_tool', call_id='call_qMxxXtcJsiK8KFSSCx3zm0is', is_error=False)]
---------- DataAnalystAgent ----------
85.98130841121495
---------- PlanningAgent ----------
The player with the highest points for the Miami Heat in the 2006-2007 NBA season was Dwyane Wade, who scored 1,397 points. The percentage change in Dwyane Wade's total rebounds from 214 in the 2007-2008 season to 398 in the 2008-2009 season is approximately 85.98%.

TERMINATE
```

As we can see, after the Web Search Agent conducts the necessary searches and the Data Analyst Agent completes the necessary calculations, we find that Dwayne Wade was the Miami Heat player with the highest points in the 2006-2007 season, and the percentage change in his total rebounds between the 2007-2008 and 2008-2009 seasons is 85.98%!

## Custom Selector Function

Often times we want better control over the selection process. To this end, we can set the `selector_func` argument with a custom selector function to override the default model-based selection. This allows us to implement more complex selection logic and state-based transitions.

For instance, we want the Planning Agent to speak immediately after any specialized agent to check the progress.

> **Note**: Returning `None` from the custom selector function will use the default model-based selection.

> **Note**: Custom selector functions are not serialized when `.dump_component()` is called on the `SelectorGroupChat` team. If you need to serialize team configurations with custom selector functions, consider implementing custom workflows and serialization logic.

```python
def selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
    if messages[-1].source != planning_agent.name:
        return planning_agent.name
    return None


# Reset the previous team and run the chat again with the selector function.
await team.reset()
team = SelectorGroupChat(
    [planning_agent, web_search_agent, data_analyst_agent],
    model_client=model_client,
    termination_condition=termination,
    selector_prompt=selector_prompt,
    allow_repeated_speaker=True,
    selector_func=selector_func,
)

await Console(team.run_stream(task=task))
```

You can see from the conversation log that the Planning Agent always speaks immediately after the specialized agents.

> **Tip**: Each participant agent only makes one step (executing tools, generating a response, etc.) on each turn. If you want an `AssistantAgent` to repeat until it stop returning a `ToolCallSummaryMessage` when it has finished running all the tools it needs to run, you can do so by checking the last message and returning the agent if it is a `ToolCallSummaryMessage`.

## Custom Candidate Function

One more possible requirement might be to automatically select the next speaker from a filtered list of agents. For this, we can set `candidate_func` parameter with a custom candidate function to filter down the list of potential agents for speaker selection for each turn of groupchat.

This allow us to restrict speaker selection to a specific set of agents after a given agent.

> **Note**: The `candidate_func` is only valid if `selector_func` is not set. Returning `None` or an empty list `[]` from the custom candidate function will raise a `ValueError`.

```python
def candidate_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> List[str]:
    # keep planning_agent first one to plan out the tasks
    if messages[-1].source == "user":
        return [planning_agent.name]

    # if previous agent is planning_agent and if it explicitely asks for web_search_agent
    # or data_analyst_agent or both (in-case of re-planning or re-assignment of tasks)
    # then return those specific agents
    last_message = messages[-1]
    if last_message.source == planning_agent.name:
        participants = []
        if web_search_agent.name in last_message.to_text():
            participants.append(web_search_agent.name)
        if data_analyst_agent.name in last_message.to_text():
            participants.append(data_analyst_agent.name)
        if participants:
            return participants  # SelectorGroupChat will select from the remaining two agents.

    # we can assume that the task is finished once the web_search_agent
    # and data_analyst_agent have took their turns, thus we send
    # in planning_agent to terminate the chat
    previous_set_of_agents = set(message.source for message in messages)
    if web_search_agent.name in previous_set_of_agents and data_analyst_agent.name in previous_set_of_agents:
        return [planning_agent.name]

    # if no-conditions are met then return all the agents
    return [planning_agent.name, web_search_agent.name, data_analyst_agent.name]


# Reset the previous team and run the chat again with the selector function.
await team.reset()
team = SelectorGroupChat(
    [planning_agent, web_search_agent, data_analyst_agent],
    model_client=model_client,
    termination_condition=termination,
    candidate_func=candidate_func,
)

await Console(team.run_stream(task=task))
```

You can see from the conversation log that the Planning Agent returns to conversation once the Web Search Agent and Data Analyst Agent took their turns and it finds that the task was not finished as expected so it called the WebSearchAgent again to get rebound values and then called DataAnalysetAgent to get the percentage change.

## User Feedback

We can add `UserProxyAgent` to the team to provide user feedback during a run. See [Human-in-the-Loop](./human-in-the-loop.md) for more details about `UserProxyAgent`.

To use the `UserProxyAgent` in the web search example, we simply add it to the team and update the selector function to always check for user feedback after the planning agent speaks. If the user responds with "APPROVE", the conversation continues, otherwise, the planning agent tries again, until the user approves.

```python
user_proxy_agent = UserProxyAgent("UserProxyAgent", description="A proxy for the user to approve or disapprove tasks.")


def selector_func_with_user_proxy(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
    if messages[-1].source != planning_agent.name and messages[-1].source != user_proxy_agent.name:
        # Planning agent should be the first to engage when given a new task, or check progress.
        return planning_agent.name
    if messages[-1].source == planning_agent.name:
        if messages[-2].source == user_proxy_agent.name and "APPROVE" in messages[-1].content.upper():  # type: ignore
            # User has approved the plan, proceed to the next agent.
            return None
        # Use the user proxy agent to get the user's approval to proceed.
        return user_proxy_agent.name
    if messages[-1].source == user_proxy_agent.name:
        # If the user does not approve, return to the planning agent.
        if "APPROVE" not in messages[-1].content.upper():  # type: ignore
            return planning_agent.name
    return None


# Reset the previous agents and run the chat again with the user proxy agent and selector function.
await team.reset()
team = SelectorGroupChat(
    [planning_agent, web_search_agent, data_analyst_agent, user_proxy_agent],
    model_client=model_client,
    termination_condition=termination,
    selector_prompt=selector_prompt,
    selector_func=selector_func_with_user_proxy,
    allow_repeated_speaker=True,
)

await Console(team.run_stream(task=task))
```

Now, the user's feedback is incorporated into the conversation flow, and the user can approve or reject the planning agent's decisions.

## Using Reasoning Models

So far in the examples, we have used a gpt-4o model. Models like gpt-4o and gemini-1.5-flash are great at following instructions, so you can have relatively detailed instructions in the selector prompt for the team and the system messages for each agent to guide their behavior.

However, if you are using a reasoning model like o3-mini, you will need to keep the selector prompt and system messages as simple and to the point as possible. This is because the reasoning models are already good at coming up with their own instructions given the context provided to them.

This also means that we don't need a planning agent to break down the task anymore, since the `SelectorGroupChat` that uses a reasoning model can do that on its own.

In the following example, we will use o3-mini as the model for the agents and the team, and we will not use a planning agent. Also, we are keeping the selector prompt and system messages as simple as possible.

```python
model_client = OpenAIChatCompletionClient(model="o3-mini")

web_search_agent = AssistantAgent(
    "WebSearchAgent",
    description="An agent for searching information on the web.",
    tools=[search_web_tool],
    model_client=model_client,
    system_message="""Use web search tool to find information.""",
)

data_analyst_agent = AssistantAgent(
    "DataAnalystAgent",
    description="An agent for performing calculations.",
    model_client=model_client,
    tools=[percentage_change_tool],
    system_message="""Use tool to perform calculation. If you have not seen the data, ask for it.""",
)

user_proxy_agent = UserProxyAgent(
    "UserProxyAgent",
    description="A user to approve or disapprove tasks.",
)

selector_prompt = """Select an agent to perform task.

{roles}

Current conversation context:
{history}

Read the above conversation, then select an agent from {participants} to perform the next task.
When the task is complete, let the user approve or disapprove the task.
"""

team = SelectorGroupChat(
    [web_search_agent, data_analyst_agent, user_proxy_agent],
    model_client=model_client,
    termination_condition=termination,  # Use the same termination condition as before.
    selector_prompt=selector_prompt,
    allow_repeated_speaker=True,
)
await Console(team.run_stream(task=task))
```

**출력:**
```
---------- user ----------
Who was the Miami Heat player with the highest points in the 2006-2007 season, and what was the percentage change in his total rebounds between the 2007-2008 and 2008-2009 seasons?
---------- WebSearchAgent ----------
[FunctionCall(id='call_hl7EP6Lp5jj5wEdxeNHTwUVG', arguments='{"query": "Who was the Miami Heat player with the highest points in the 2006-2007 season Miami Heat statistics Dwyane Wade rebounds percentage change 2007-2008 2008-2009 seasons"}', name='search_web_tool')]
---------- WebSearchAgent ----------
[FunctionExecutionResult(content='Here are the total points scored by Miami Heat players in the 2006-2007 season:\n        Udonis Haslem: 844 points\n        Dwayne Wade: 1397 points\n        James Posey: 550 points\n        ...\n        ', call_id='call_hl7EP6Lp5jj5wEdxeNHTwUVG', is_error=False)]
---------- WebSearchAgent ----------
Here are the total points scored by Miami Heat players in the 2006-2007 season:
        Udonis Haslem: 844 points
        Dwayne Wade: 1397 points
        James Posey: 550 points
        ...
---------- DataAnalystAgent ----------
I found that in the 2006–2007 season the player with the highest points was Dwyane Wade (with 1,397 points). Could you please provide Dwyane Wade's total rebounds for the 2007–2008 and the 2008–2009 seasons so I can calculate the percentage change?
---------- WebSearchAgent ----------
[FunctionCall(id='call_lppGTILXDvO9waPwKO66ehK6', arguments='{"query": "Dwyane Wade total rebounds 2007-2008 and 2008-2009 seasons for Miami Heat"}', name='search_web_tool')]
---------- WebSearchAgent ----------
[FunctionExecutionResult(content='The number of total rebounds for Dwayne Wade in the Miami Heat season 2007-2008 is 214.', call_id='call_lppGTILXDvO9waPwKO66ehK6', is_error=False)]
---------- WebSearchAgent ----------
The number of total rebounds for Dwayne Wade in the Miami Heat season 2007-2008 is 214.
---------- DataAnalystAgent ----------
Could you please provide Dwyane Wade's total rebounds in the 2008-2009 season?
---------- WebSearchAgent ----------
[FunctionCall(id='call_r8DBcbJtQfdtugLtyTrqOvoK', arguments='{"query": "Dwyane Wade total rebounds 2008-2009 season Miami Heat"}', name='search_web_tool')]
---------- WebSearchAgent ----------
[FunctionExecutionResult(content='The number of total rebounds for Dwayne Wade in the Miami Heat season 2008-2009 is 398.', call_id='call_r8DBcbJtQfdtugLtyTrqOvoK', is_error=False)]
---------- WebSearchAgent ----------
The number of total rebounds for Dwayne Wade in the Miami Heat season 2008-2009 is 398.
---------- DataAnalystAgent ----------
[FunctionCall(id='call_4jejv1wM7V1osbBCxJze8aQM', arguments='{"start": 214, "end": 398}', name='percentage_change_tool')]
---------- DataAnalystAgent ----------
[FunctionExecutionResult(content='85.98130841121495', call_id='call_4jejv1wM7V1osbBCxJze8aQM', is_error=False)]
---------- DataAnalystAgent ----------
85.98130841121495
---------- DataAnalystAgent ----------
Dwyane Wade was the Miami Heat player with the highest total points (1,397) during the 2006-2007 season. His total rebounds increased by approximately 86% from 214 in the 2007-2008 season to 398 in the 2008-2009 season.
---------- UserProxyAgent ----------
Approve. TERMINATE
```

> **Tip**: For more guidance on how to prompt reasoning models, see the [Azure AI Services Blog on Prompt Engineering for OpenAI's O1 and O3-mini Reasoning Models](https://techcommunity.microsoft.com/blog/aiplatformblog/prompt-engineering-for-openai's-o1-and-o3-mini-reasoning-models/4298476)

