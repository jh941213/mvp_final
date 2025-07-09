# Reflection

Reflection is a design pattern where an LLM generation is followed by a reflection, which in itself is another LLM generation conditioned on the output of the first one. For example, given a task to write code, the first LLM can generate a code snippet, and the second LLM can generate a critique of the code snippet.

In the context of AutoGen and agents, reflection can be implemented as a pair of agents, where the first agent generates a message and the second agent generates a response to the message. The two agents continue to interact until they reach a stopping condition, such as a maximum number of iterations or an approval from the second agent.

Let's implement a simple reflection design pattern using AutoGen agents. There will be two agents: a coder agent and a reviewer agent, the coder agent will generate a code snippet, and the reviewer agent will generate a critique of the code snippet.

## Message Protocol

Before we define the agents, we need to first define the message protocol for the agents.

```python
from dataclasses import dataclass


@dataclass
class CodeWritingTask:
    task: str


@dataclass
class CodeWritingResult:
    task: str
    code: str
    review: str


@dataclass
class CodeReviewTask:
    session_id: str
    code_writing_task: str
    code_writing_scratchpad: str
    code: str


@dataclass
class CodeReviewResult:
    review: str
    session_id: str
    approved: bool
```

The above set of messages defines the protocol for our example reflection design pattern:

1. The application sends a `CodeWritingTask` message to the coder agent
2. The coder agent generates a `CodeReviewTask` message, which is sent to the reviewer agent
3. The reviewer agent generates a `CodeReviewResult` message, which is sent back to the coder agent
4. Depending on the `CodeReviewResult` message, if the code is approved, the coder agent sends a `CodeWritingResult` message back to the application, otherwise, the coder agent sends another `CodeReviewTask` message to the reviewer agent, and the process continues.

We can visualize the message protocol using a data flow diagram:

coder-reviewer data flow

## Agents

Now, let's define the agents for the reflection design pattern.

```python
import json
import re
import uuid
from typing import Dict, List, Union

from autogen_core import MessageContext, RoutedAgent, TopicId, default_subscription, message_handler
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
```

We use the Broadcast API to implement the design pattern. The agents implements the pub/sub model. The coder agent subscribes to the `CodeWritingTask` and `CodeReviewResult` messages, and publishes the `CodeReviewTask` and `CodeWritingResult` messages.

```python
@default_subscription
class CoderAgent(RoutedAgent):
    """An agent that performs code writing tasks."""

    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A code writing agent.")
        self._system_messages: List[LLMMessage] = [
            SystemMessage(
                content="""You are a proficient coder. You write code to solve problems.
Work with the reviewer to improve your code.
Always put all finished code in a single Markdown code block.
For example:
```python
def hello_world():
    print("Hello, World!")
```

Respond using the following format:

Thoughts: <Your comments>
Code: <Your code>
""",
            )
        ]
        self._model_client = model_client
        self._session_memory: Dict[str, List[CodeWritingTask | CodeReviewTask | CodeReviewResult]] = {}

    @message_handler
    async def handle_code_writing_task(self, message: CodeWritingTask, ctx: MessageContext) -> None:
        # Store the messages in a temporary memory for this request only.
        session_id = str(uuid.uuid4())
        self._session_memory.setdefault(session_id, []).append(message)
        # Generate a response using the chat completion API.
        response = await self._model_client.create(
            self._system_messages + [UserMessage(content=message.task, source=self.metadata["type"])],
            cancellation_token=ctx.cancellation_token,
        )
        assert isinstance(response.content, str)
        # Extract the code block from the response.
        code_block = self._extract_code_block(response.content)
        if code_block is None:
            raise ValueError("Code block not found.")
        # Create a code review task.
        code_review_task = CodeReviewTask(
            session_id=session_id,
            code_writing_task=message.task,
            code_writing_scratchpad=response.content,
            code=code_block,
        )
        # Store the code review task in the session memory.
        self._session_memory[session_id].append(code_review_task)
        # Publish a code review task.
        await self.publish_message(code_review_task, topic_id=TopicId("default", self.id.key))

    @message_handler
    async def handle_code_review_result(self, message: CodeReviewResult, ctx: MessageContext) -> None:
        # Store the review result in the session memory.
        self._session_memory[message.session_id].append(message)
        # Obtain the request from previous messages.
        review_request = next(
            m for m in reversed(self._session_memory[message.session_id]) if isinstance(m, CodeReviewTask)
        )
        assert review_request is not None
        # Check if the code is approved.
        if message.approved:
            # Publish the code writing result.
            await self.publish_message(
                CodeWritingResult(
                    code=review_request.code,
                    task=review_request.code_writing_task,
                    review=message.review,
                ),
                topic_id=TopicId("default", self.id.key),
            )
            print("Code Writing Result:")
            print("-" * 80)
            print(f"Task:\n{review_request.code_writing_task}")
            print("-" * 80)
            print(f"Code:\n{review_request.code}")
            print("-" * 80)
            print(f"Review:\n{message.review}")
            print("-" * 80)
        else:
            # Create a list of LLM messages to send to the model.
            messages: List[LLMMessage] = [*self._system_messages]
            for m in self._session_memory[message.session_id]:
                if isinstance(m, CodeReviewResult):
                    messages.append(UserMessage(content=m.review, source="Reviewer"))
                elif isinstance(m, CodeReviewTask):
                    messages.append(AssistantMessage(content=m.code_writing_scratchpad, source="Coder"))
                elif isinstance(m, CodeWritingTask):
                    messages.append(UserMessage(content=m.task, source="User"))
                else:
                    raise ValueError(f"Unexpected message type: {m}")
            # Generate a revision using the chat completion API.
            response = await self._model_client.create(messages, cancellation_token=ctx.cancellation_token)
            assert isinstance(response.content, str)
            # Extract the code block from the response.
            code_block = self._extract_code_block(response.content)
            if code_block is None:
                raise ValueError("Code block not found.")
            # Create a new code review task.
            code_review_task = CodeReviewTask(
                session_id=message.session_id,
                code_writing_task=review_request.code_writing_task,
                code_writing_scratchpad=response.content,
                code=code_block,
            )
            # Store the code review task in the session memory.
            self._session_memory[message.session_id].append(code_review_task)
            # Publish a new code review task.
            await self.publish_message(code_review_task, topic_id=TopicId("default", self.id.key))

    def _extract_code_block(self, markdown_text: str) -> Union[str, None]:
        pattern = r"```(\w+)\n(.*?)\n```"
        # Search for the pattern in the markdown text
        match = re.search(pattern, markdown_text, re.DOTALL)
        # Extract the language and code block if a match is found
        if match:
            return match.group(2)
        return None
```

A few things to note about `CoderAgent`:

- It uses chain-of-thought prompting in its system message.
- It stores message histories for different `CodeWritingTask` in a dictionary, so each task has its own history.
- When making an LLM inference request using its model client, it transforms the message history into a list of `autogen_core.models.LLMMessage` objects to pass to the model client.

The reviewer agent subscribes to the `CodeReviewTask` message and publishes the `CodeReviewResult` message.

```python
@default_subscription
class ReviewerAgent(RoutedAgent):
    """An agent that performs code review tasks."""

    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A code reviewer agent.")
        self._system_messages: List[LLMMessage] = [
            SystemMessage(
                content="""You are a code reviewer. You focus on correctness, efficiency and safety of the code.
Respond using the following JSON format:
{
    "correctness": "<Your comments>",
    "efficiency": "<Your comments>",
    "safety": "<Your comments>",
    "approval": "<APPROVE or REVISE>",
    "suggested_changes": "<Your comments>"
}
""",
            )
        ]
        self._session_memory: Dict[str, List[CodeReviewTask | CodeReviewResult]] = {}
        self._model_client = model_client

    @message_handler
    async def handle_code_review_task(self, message: CodeReviewTask, ctx: MessageContext) -> None:
        # Format the prompt for the code review.
        # Gather the previous feedback if available.
        previous_feedback = ""
        if message.session_id in self._session_memory:
            previous_review = next(
                (m for m in reversed(self._session_memory[message.session_id]) if isinstance(m, CodeReviewResult)),
                None,
            )
            if previous_review is not None:
                previous_feedback = previous_review.review
        # Store the messages in a temporary memory for this request only.
        self._session_memory.setdefault(message.session_id, []).append(message)
        prompt = f"""The problem statement is: {message.code_writing_task}
The code is:
```
{message.code}
```

Previous feedback:
{previous_feedback}

Please review the code. If previous feedback was provided, see if it was addressed.
"""
        # Generate a response using the chat completion API.
        response = await self._model_client.create(
            self._system_messages + [UserMessage(content=prompt, source=self.metadata["type"])],
            cancellation_token=ctx.cancellation_token,
            json_output=True,
        )
        assert isinstance(response.content, str)
        # TODO: use structured generation library e.g. guidance to ensure the response is in the expected format.
        # Parse the response JSON.
        review = json.loads(response.content)
        # Construct the review text.
        review_text = "Code review:\n" + "\n".join([f"{k}: {v}" for k, v in review.items()])
        approved = review["approval"].lower().strip() == "approve"
        result = CodeReviewResult(
            review=review_text,
            session_id=message.session_id,
            approved=approved,
        )
        # Store the review result in the session memory.
        self._session_memory[message.session_id].append(result)
        # Publish the review result.
        await self.publish_message(result, topic_id=TopicId("default", self.id.key))
```

The `ReviewerAgent` uses JSON-mode when making an LLM inference request, and also uses chain-of-thought prompting in its system message.

## Logging

Turn on logging to see the messages exchanged between the agents.

```python
import logging

logging.basicConfig(level=logging.WARNING)
logging.getLogger("autogen_core").setLevel(logging.DEBUG)
```

## Running the Design Pattern

Let's test the design pattern with a coding task. Since all the agents are decorated with the `default_subscription()` class decorator, the agents when created will automatically subscribe to the default topic. We publish a `CodeWritingTask` message to the default topic to start the reflection process.

```python
from autogen_core import DefaultTopicId, SingleThreadedAgentRuntime
from autogen_ext.models.openai import OpenAIChatCompletionClient

runtime = SingleThreadedAgentRuntime()
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
await ReviewerAgent.register(runtime, "ReviewerAgent", lambda: ReviewerAgent(model_client=model_client))
await CoderAgent.register(runtime, "CoderAgent", lambda: CoderAgent(model_client=model_client))
runtime.start()
await runtime.publish_message(
    message=CodeWritingTask(task="Write a function to find the sum of all even numbers in a list."),
    topic_id=DefaultTopicId(),
)

# Keep processing messages until idle.
await runtime.stop_when_idle()
# Close the model client.
await model_client.close()
```

The log messages show the interaction between the coder and reviewer agents. The final output shows the code snippet generated by the coder agent and the critique generated by the reviewer agent. 