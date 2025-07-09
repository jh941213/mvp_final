# Human-in-the-Loop

In the previous section Teams, we have seen how to create, observe, and control a team of agents. This section will focus on how to interact with the team from your application, and provide human feedback to the team.

There are two main ways to interact with the team from your application:

1. **During a team's run** – execution of `run()` or `run_stream()`, provide feedback through a `UserProxyAgent`.
2. **Once the run terminates**, provide feedback through input to the next call to `run()` or `run_stream()`.

We will cover both methods in this section.

To jump straight to code samples on integration with web and UI frameworks, see the following links:
- [AgentChat + FastAPI](./samples/fastapi)
- [AgentChat + ChainLit](./samples/chainlit)
- [AgentChat + Streamlit](./samples/streamlit)

## Providing Feedback During a Run

The `UserProxyAgent` is a special built-in agent that acts as a proxy for a user to provide feedback to the team.

To use the `UserProxyAgent`, you can create an instance of it and include it in the team before running the team. The team will decide when to call the `UserProxyAgent` to ask for feedback from the user.

For example in a `RoundRobinGroupChat` team, the `UserProxyAgent` is called in the order in which it is passed to the team, while in a `SelectorGroupChat` team, the selector prompt or selector function determines when the `UserProxyAgent` is called.

The following diagram illustrates how you can use `UserProxyAgent` to get feedback from the user during a team's run:

![human-in-the-loop-user-proxy](./images/human-in-the-loop-user-proxy.png)

The bold arrows indicates the flow of control during a team's run: when the team calls the `UserProxyAgent`, it transfers the control to the application/user, and waits for the feedback; once the feedback is provided, the control is transferred back to the team and the team continues its execution.

> **Note**: When `UserProxyAgent` is called during a run, it blocks the execution of the team until the user provides feedback or errors out. This will hold up the team's progress and put the team in an unstable state that cannot be saved or resumed.
>
> Due to the blocking nature of this approach, it is recommended to use it only for short interactions that require immediate feedback from the user, such as asking for approval or disapproval with a button click, or an alert requiring immediate attention otherwise failing the task.

Here is an example of how to use the `UserProxyAgent` in a `RoundRobinGroupChat` for a poetry generation task:

```python
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create the agents.
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
assistant = AssistantAgent("assistant", model_client=model_client)
user_proxy = UserProxyAgent("user_proxy", input_func=input)  # Use input() to get user input from console.

# Create the termination condition which will end the conversation when the user says "APPROVE".
termination = TextMentionTermination("APPROVE")

# Create the team.
team = RoundRobinGroupChat([assistant, user_proxy], termination_condition=termination)

# Run the conversation and stream to the console.
stream = team.run_stream(task="Write a 4-line poem about the ocean.")
# Use asyncio.run(...) when running in a script.
await Console(stream)
await model_client.close()
```

**출력:**
```
---------- user ----------
Write a 4-line poem about the ocean.
---------- assistant ----------
In endless blue where whispers play,  
The ocean's waves dance night and day.  
A world of depths, both calm and wild,  
Nature's heart, forever beguiled.  
TERMINATE
---------- user_proxy ----------
APPROVE
TaskResult(messages=[TextMessage(source='user', models_usage=None, metadata={}, content='Write a 4-line poem about the ocean.', type='TextMessage'), TextMessage(source='assistant', models_usage=RequestUsage(prompt_tokens=46, completion_tokens=43), metadata={}, content="In endless blue where whispers play,  \nThe ocean's waves dance night and day.  \nA world of depths, both calm and wild,  \nNature's heart, forever beguiled.  \nTERMINATE", type='TextMessage'), UserInputRequestedEvent(source='user_proxy', models_usage=None, metadata={}, request_id='2622a0aa-b776-4e54-9e8f-4ecbdf14b78d', content='', type='UserInputRequestedEvent'), TextMessage(source='user_proxy', models_usage=None, metadata={}, content='APPROVE', type='TextMessage')], stop_reason="Text 'APPROVE' mentioned")
```

From the console output, you can see the team solicited feedback from the user through `user_proxy` to approve the generated poem.

You can provide your own input function to the `UserProxyAgent` to customize the feedback process. For example, when the team is running as a web service, you can use a custom input function to wait for message from a web socket connection. The following code snippet shows an example of custom input function when using the FastAPI web framework:

```python
@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()

    async def _user_input(prompt: str, cancellation_token: CancellationToken | None) -> str:
        data = await websocket.receive_json() # Wait for user message from websocket.
        message = TextMessage.model_validate(data) # Assume user message is a TextMessage.
        return message.content
    
    # Create user proxy with custom input function
    # Run the team with the user proxy
    # ...
```

See the [AgentChat FastAPI sample](./samples/fastapi) for a complete example.

For ChainLit integration with `UserProxyAgent`, see the [AgentChat ChainLit sample](./samples/chainlit).

## Providing Feedback to the Next Run

Often times, an application or a user interacts with the team of agents in an interactive loop: the team runs until termination, the application or user provides feedback, and the team runs again with the feedback.

This approach is useful in a persisted session with asynchronous communication between the team and the application/user: Once a team finishes a run, the application saves the state of the team, puts it in a persistent storage, and resumes the team when the feedback arrives.

> **Note**: For how to save and load the state of a team, please refer to [Managing State](./managing-state.md). This section will focus on the feedback mechanisms.

The following diagram illustrates the flow of control in this approach:

![human-in-the-loop-termination](./images/human-in-the-loop-termination.png)

There are two ways to implement this approach:

1. **Set the maximum number of turns** so that the team always stops after the specified number of turns.
2. **Use termination conditions** such as `TextMentionTermination` and `HandoffTermination` to allow the team to decide when to stop and give control back, given the team's internal state.

You can use both methods together to achieve your desired behavior.

### Using Max Turns

This method allows you to pause the team for user input by setting a maximum number of turns. For instance, you can configure the team to stop after the first agent responds by setting `max_turns` to 1. This is particularly useful in scenarios where continuous user engagement is required, such as in a chatbot.

To implement this, set the `max_turns` parameter in the `RoundRobinGroupChat()` constructor.

```python
team = RoundRobinGroupChat([...], max_turns=1)
```

Once the team stops, the turn count will be reset. When you resume the team, it will start from 0 again. However, the team's internal state will be preserved, for example, the `RoundRobinGroupChat` will resume from the next agent in the list with the same conversation history.

> **Note**: `max_turn` is specific to the team class and is currently only supported by `RoundRobinGroupChat`, `SelectorGroupChat`, and `Swarm`. When used with termination conditions, the team will stop when either condition is met.

Here is an example of how to use `max_turns` in a `RoundRobinGroupChat` for a poetry generation task with a maximum of 1 turn:

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create the agents.
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
assistant = AssistantAgent("assistant", model_client=model_client)

# Create the team setting a maximum number of turns to 1.
team = RoundRobinGroupChat([assistant], max_turns=1)

task = "Write a 4-line poem about the ocean."
while True:
    # Run the conversation and stream to the console.
    stream = team.run_stream(task=task)
    # Use asyncio.run(...) when running in a script.
    await Console(stream)
    # Get the user response.
    task = input("Enter your feedback (type 'exit' to leave): ")
    if task.lower().strip() == "exit":
        break
await model_client.close()
```

**출력:**
```
---------- user ----------
Write a 4-line poem about the ocean.
---------- assistant ----------
Endless waves in a dance with the shore,  
Whispers of secrets in tales from the roar,  
Beneath the vast sky, where horizons blend,  
The ocean's embrace is a timeless friend.  
TERMINATE
[Prompt tokens: 46, Completion tokens: 48]
---------- Summary ----------
Number of messages: 2
Finish reason: Maximum number of turns 1 reached.
Total prompt tokens: 46
Total completion tokens: 48
Duration: 1.63 seconds
---------- user ----------
Can you make it about a person and its relationship with the ocean
---------- assistant ----------
She walks along the tide, where dreams intertwine,  
With every crashing wave, her heart feels aligned,  
In the ocean's embrace, her worries dissolve,  
A symphony of solace, where her spirit evolves.  
TERMINATE
[Prompt tokens: 117, Completion tokens: 49]
---------- Summary ----------
Number of messages: 2
Finish reason: Maximum number of turns 1 reached.
Total prompt tokens: 117
Total completion tokens: 49
Duration: 1.21 seconds
```

You can see that the team stopped immediately after one agent responded.

### Using Termination Conditions

We have already seen several examples of termination conditions in the previous sections. In this section, we focus on `HandoffTermination` which stops the team when an agent sends a `HandoffMessage` message.

Let's create a team with a single `AssistantAgent` agent with a handoff setting, and run the team with a task that requires additional input from the user because the agent doesn't have relevant tools to continue processing the task.

> **Note**: The model used with `AssistantAgent` must support tool call to use the handoff feature.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    # api_key="sk-...", # Optional if you have an OPENAI_API_KEY env variable set.
)

# Create a lazy assistant agent that always hands off to the user.
lazy_agent = AssistantAgent(
    "lazy_assistant",
    model_client=model_client,
    handoffs=[Handoff(target="user", message="Transfer to user.")],
    system_message="If you cannot complete the task, transfer to user. Otherwise, when finished, respond with 'TERMINATE'.",
)

# Define a termination condition that checks for handoff messages.
handoff_termination = HandoffTermination(target="user")
# Define a termination condition that checks for a specific text mention.
text_termination = TextMentionTermination("TERMINATE")

# Create a single-agent team with the lazy assistant and both termination conditions.
lazy_agent_team = RoundRobinGroupChat([lazy_agent], termination_condition=handoff_termination | text_termination)

# Run the team and stream to the console.
task = "What is the weather in New York?"
await Console(lazy_agent_team.run_stream(task=task), output_stats=True)
```

**출력:**
```
---------- user ----------
What is the weather in New York?
---------- lazy_assistant ----------
[FunctionCall(id='call_EAcMgrLGHdLw0e7iJGoMgxuu', arguments='{}', name='transfer_to_user')]
[Prompt tokens: 69, Completion tokens: 12]
---------- lazy_assistant ----------
[FunctionExecutionResult(content='Transfer to user.', call_id='call_EAcMgrLGHdLw0e7iJGoMgxuu')]
---------- lazy_assistant ----------
Transfer to user.
---------- Summary ----------
Number of messages: 4
Finish reason: Handoff to user from lazy_assistant detected.
Total prompt tokens: 69
Total completion tokens: 12
Duration: 0.69 seconds
TaskResult(messages=[TextMessage(source='user', models_usage=None, content='What is the weather in New York?', type='TextMessage'), ToolCallRequestEvent(source='lazy_assistant', models_usage=RequestUsage(prompt_tokens=69, completion_tokens=12), content=[FunctionCall(id='call_EAcMgrLGHdLw0e7iJGoMgxuu', arguments='{}', name='transfer_to_user')], type='ToolCallRequestEvent'), ToolCallExecutionEvent(source='lazy_assistant', models_usage=None, content=[FunctionExecutionResult(content='Transfer to user.', call_id='call_EAcMgrLGHdLw0e7iJGoMgxuu')], type='ToolCallExecutionEvent'), HandoffMessage(source='lazy_assistant', models_usage=None, target='user', content='Transfer to user.', context=[], type='HandoffMessage')], stop_reason='Handoff to user from lazy_assistant detected.')
```

You can see the team stopped due to the handoff message was detected. Let's continue the team by providing the information the agent needs.

```python
await Console(lazy_agent_team.run_stream(task="The weather in New York is sunny."))
```

**출력:**
```
---------- user ----------
The weather in New York is sunny.
---------- lazy_assistant ----------
Great! Enjoy the sunny weather in New York! Is there anything else you'd like to know?
---------- lazy_assistant ----------
TERMINATE
TaskResult(messages=[TextMessage(source='user', models_usage=None, content='The weather in New York is sunny.', type='TextMessage'), TextMessage(source='lazy_assistant', models_usage=RequestUsage(prompt_tokens=110, completion_tokens=21), content="Great! Enjoy the sunny weather in New York! Is there anything else you'd like to know?", type='TextMessage'), TextMessage(source='lazy_assistant', models_usage=RequestUsage(prompt_tokens=137, completion_tokens=5), content='TERMINATE', type='TextMessage')], stop_reason="Text 'TERMINATE' mentioned")
```

You can see the team continued after the user provided the information.

> **Note**: If you are using Swarm team with `HandoffTermination` targeting user, to resume the team, you need to set the task to a `HandoffMessage` with the target set to the next agent you want to run. See [Swarm](./swarm.md) for more details.

