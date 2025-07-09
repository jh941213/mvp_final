# Managing State

So far, we have discussed how to build components in a multi-agent application - agents, teams, termination conditions. In many cases, it is useful to save the state of these components to disk and load them back later. This is particularly useful in a web application where stateless endpoints respond to requests and need to load the state of the application from persistent storage.

In this notebook, we will discuss how to save and load the state of agents, teams, and termination conditions.

## Saving and Loading Agents

We can get the state of an agent by calling `save_state()` method on an `AssistantAgent`.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(model="gpt-4o-2024-08-06")

assistant_agent = AssistantAgent(
    name="assistant_agent",
    system_message="You are a helpful assistant",
    model_client=model_client,
)

# Use asyncio.run(...) when running in a script.
response = await assistant_agent.on_messages(
    [TextMessage(content="Write a 3 line poem on lake tangayika", source="user")], CancellationToken()
)
print(response.chat_message)
await model_client.close()
```

**출력:**
```
In Tanganyika's embrace so wide and deep,  
Ancient waters cradle secrets they keep,  
Echoes of time where horizons sleep.  
```

```python
agent_state = await assistant_agent.save_state()
print(agent_state)
```

**출력:**
```python
{'type': 'AssistantAgentState', 'version': '1.0.0', 'llm_messages': [{'content': 'Write a 3 line poem on lake tangayika', 'source': 'user', 'type': 'UserMessage'}, {'content': "In Tanganyika's embrace so wide and deep,  \nAncient waters cradle secrets they keep,  \nEchoes of time where horizons sleep.  ", 'source': 'assistant_agent', 'type': 'AssistantMessage'}]}
```

```python
model_client = OpenAIChatCompletionClient(model="gpt-4o-2024-08-06")

new_assistant_agent = AssistantAgent(
    name="assistant_agent",
    system_message="You are a helpful assistant",
    model_client=model_client,
)
await new_assistant_agent.load_state(agent_state)

# Use asyncio.run(...) when running in a script.
response = await new_assistant_agent.on_messages(
    [TextMessage(content="What was the last line of the previous poem you wrote", source="user")], CancellationToken()
)
print(response.chat_message)
await model_client.close()
```

**출력:**
```
The last line of the poem was: "Echoes of time where horizons sleep."
```

> **Note**: For `AssistantAgent`, its state consists of the `model_context`. If you write your own custom agent, consider overriding the `save_state()` and `load_state()` methods to customize the behavior. The default implementations save and load an empty state.

## Saving and Loading Teams

We can get the state of a team by calling `save_state` method on the team and load it back by calling `load_state` method on the team.

When we call `save_state` on a team, it saves the state of all the agents in the team.

We will begin by creating a simple `RoundRobinGroupChat` team with a single agent and ask it to write a poem.

```python
model_client = OpenAIChatCompletionClient(model="gpt-4o-2024-08-06")

# Define a team.
assistant_agent = AssistantAgent(
    name="assistant_agent",
    system_message="You are a helpful assistant",
    model_client=model_client,
)
agent_team = RoundRobinGroupChat([assistant_agent], termination_condition=MaxMessageTermination(max_messages=2))

# Run the team and stream messages to the console.
stream = agent_team.run_stream(task="Write a beautiful poem 3-line about lake tangayika")

# Use asyncio.run(...) when running in a script.
await Console(stream)

# Save the state of the agent team.
team_state = await agent_team.save_state()
```

**출력:**
```
---------- user ----------
Write a beautiful poem 3-line about lake tangayika
---------- assistant_agent ----------
In Tanganyika's gleam, beneath the azure skies,  
Whispers of ancient waters, in tranquil guise,  
Nature's mirror, where dreams and serenity lie.
[Prompt tokens: 29, Completion tokens: 34]
---------- Summary ----------
Number of messages: 2
Finish reason: Maximum number of messages 2 reached, current message count: 2
Total prompt tokens: 29
Total completion tokens: 34
Duration: 0.71 seconds
```

If we reset the team (simulating instantiation of the team), and ask the question "What was the last line of the poem you wrote?", we see that the team is unable to accomplish this as there is no reference to the previous run.

```python
await agent_team.reset()
stream = agent_team.run_stream(task="What was the last line of the poem you wrote?")
await Console(stream)
```

**출력:**
```
---------- user ----------
What was the last line of the poem you wrote?
---------- assistant_agent ----------
I'm sorry, but I am unable to recall or access previous interactions, including any specific poem I may have composed in our past conversations. If you like, I can write a new poem for you.
[Prompt tokens: 28, Completion tokens: 40]
---------- Summary ----------
Number of messages: 2
Finish reason: Maximum number of messages 2 reached, current message count: 2
Total prompt tokens: 28
Total completion tokens: 40
Duration: 0.70 seconds
```

Next, we load the state of the team and ask the same question. We see that the team is able to accurately return the last line of the poem it wrote.

```python
print(team_state)

# Load team state.
await agent_team.load_state(team_state)
stream = agent_team.run_stream(task="What was the last line of the poem you wrote?")
await Console(stream)
```

**출력:**
```python
{'type': 'TeamState', 'version': '1.0.0', 'agent_states': {'group_chat_manager/a55364ad-86fd-46ab-9449-dcb5260b1e06': {'type': 'RoundRobinManagerState', 'version': '1.0.0', 'message_thread': [{'source': 'user', 'models_usage': None, 'content': 'Write a beautiful poem 3-line about lake tangayika', 'type': 'TextMessage'}, {'source': 'assistant_agent', 'models_usage': {'prompt_tokens': 29, 'completion_tokens': 34}, 'content': "In Tanganyika's gleam, beneath the azure skies,  \nWhispers of ancient waters, in tranquil guise,  \nNature's mirror, where dreams and serenity lie.", 'type': 'TextMessage'}], 'current_turn': 0, 'next_speaker_index': 0}, 'collect_output_messages/a55364ad-86fd-46ab-9449-dcb5260b1e06': {}, 'assistant_agent/a55364ad-86fd-46ab-9449-dcb5260b1e06': {'type': 'ChatAgentContainerState', 'version': '1.0.0', 'agent_state': {'type': 'AssistantAgentState', 'version': '1.0.0', 'llm_messages': [{'content': 'Write a beautiful poem 3-line about lake tangayika', 'source': 'user', 'type': 'UserMessage'}, {'content': "In Tanganyika's gleam, beneath the azure skies,  \nWhispers of ancient waters, in tranquil guise,  \nNature's mirror, where dreams and serenity lie.", 'source': 'assistant_agent', 'type': 'AssistantMessage'}]}, 'message_buffer': []}}, 'team_id': 'a55364ad-86fd-46ab-9449-dcb5260b1e06'}
```

```
---------- user ----------
What was the last line of the poem you wrote?
---------- assistant_agent ----------
The last line of the poem I wrote is:  
"Nature's mirror, where dreams and serenity lie."
[Prompt tokens: 86, Completion tokens: 22]
---------- Summary ----------
Number of messages: 2
Finish reason: Maximum number of messages 2 reached, current message count: 2
Total prompt tokens: 86
Total completion tokens: 22
Duration: 0.96 seconds
```

## Persisting State (File or Database)

In many cases, we may want to persist the state of the team to disk (or a database) and load it back later. State is a dictionary that can be serialized to a file or written to a database.

```python
import json

## save state to disk

with open("coding/team_state.json", "w") as f:
    json.dump(team_state, f)

## load state from disk
with open("coding/team_state.json", "r") as f:
    team_state = json.load(f)

new_agent_team = RoundRobinGroupChat([assistant_agent], termination_condition=MaxMessageTermination(max_messages=2))
await new_agent_team.load_state(team_state)
stream = new_agent_team.run_stream(task="What was the last line of the poem you wrote?")
await Console(stream)
await model_client.close()
```

**출력:**
```
---------- user ----------
What was the last line of the poem you wrote?
---------- assistant_agent ----------
The last line of the poem I wrote is:  
"Nature's mirror, where dreams and serenity lie."
[Prompt tokens: 86, Completion tokens: 22]
---------- Summary ----------
Number of messages: 2
Finish reason: Maximum number of messages 2 reached, current message count: 2
Total prompt tokens: 86
Total completion tokens: 22
Duration: 0.72 seconds
```