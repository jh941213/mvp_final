# Serializing Components 

AutoGen provides a  {py:class}`~autogen_core.Component` configuration class that defines behaviours  to serialize/deserialize component into declarative specifications. We can accomplish this by calling `.dump_component()` and `.load_component()` respectively. This is useful for debugging, visualizing, and even for sharing your work with others. In this notebook, we will demonstrate how to serialize multiple components to a declarative specification like a JSON file.  

```{warning}
ONLY LOAD COMPONENTS FROM TRUSTED SOURCES.

With serilized components, each component implements the logic for how it is serialized and deserialized - i.e., how the declarative specification is generated and how it is converted back to an object. 

In some cases, creating an object may include executing code (e.g., a serialized function). ONLY LOAD COMPONENTS FROM TRUSTED SOURCES. 
```

```{note}
`selector_func` is not serializable and will be ignored during serialization and deserialization process.
```

### Termination Condition Example 

In the example below, we will define termination conditions (a part of an agent team) in python, export this to a dictionary/json and also demonstrate how the termination condition object can be loaded from the dictionary/json. 

## Agent Example 

In the example below, we will define an agent in python, export this to a dictionary/json and also demonstrate how the agent object can be loaded from the dictionary/json.

A similar approach can be used to serialize the `MultiModalWebSurfer` agent.

```python
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

agent = MultimodalWebSurfer(
    name="web_surfer",
    model_client=model_client,
    headless=False,
)

web_surfer_config = agent.dump_component()  # dump component
print(web_surfer_config.model_dump_json())

```python
## Team Example

In the example below, we will define a team in python, export this to a dictionary/json and also demonstrate how the team object can be loaded from the dictionary/json.

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create an agent that uses the OpenAI GPT-4o model.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    # api_key="YOUR_API_KEY",
)
agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    handoffs=["flights_refunder", "user"],
    # tools=[], # serializing tools is not yet supported
    system_message="Use tools to solve tasks.",
)

team = RoundRobinGroupChat(participants=[agent], termination_condition=MaxMessageTermination(2))

team_config = team.dump_component()  # dump component
print(team_config.model_dump_json())

await model_client.close()
```
