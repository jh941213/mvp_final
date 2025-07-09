# Multi-Agent Debate

Multi-Agent Debate is a multi-agent design pattern that simulates a multi-turn interaction where in each turn, agents exchange their responses with each other, and refine their responses based on the responses from other agents.

This example shows an implementation of the multi-agent debate pattern for solving math problems from the GSM8K benchmark.

There are of two types of agents in this pattern: solver agents and an aggregator agent. The solver agents are connected in a sparse manner following the technique described in Improving Multi-Agent Debate with Sparse Communication Topology. The solver agents are responsible for solving math problems and exchanging responses with each other. The aggregator agent is responsible for distributing math problems to the solver agents, waiting for their final responses, and aggregating the responses to get the final answer.

The pattern works as follows:

1. User sends a math problem to the aggregator agent.
2. The aggregator agent distributes the problem to the solver agents.
3. Each solver agent processes the problem, and publishes a response to its neighbors.
4. Each solver agent uses the responses from its neighbors to refine its response, and publishes a new response.
5. Repeat step 4 for a fixed number of rounds. In the final round, each solver agent publishes a final response.
6. The aggregator agent uses majority voting to aggregate the final responses from all solver agents to get a final answer, and publishes the answer.

We will be using the broadcast API, i.e., `publish_message()`, and we will be using topic and subscription to implement the communication topology. Read about Topics and Subscriptions to understand how they work.

```python
import re
from dataclasses import dataclass
from typing import Dict, List

from autogen_core import (
    DefaultTopicId,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    TypeSubscription,
    default_subscription,
    message_handler,
)
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
```

## Message Protocol

First, we define the messages used by the agents. `IntermediateSolverResponse` is the message exchanged among the solver agents in each round, and `FinalSolverResponse` is the message published by the solver agents in the final round.

```python
@dataclass
class Question:
    content: str


@dataclass
class Answer:
    content: str


@dataclass
class SolverRequest:
    content: str
    question: str


@dataclass
class IntermediateSolverResponse:
    content: str
    question: str
    answer: str
    round: int


@dataclass
class FinalSolverResponse:
    answer: str
```

## Solver Agent

The solver agent is responsible for solving math problems and exchanging responses with other solver agents. Upon receiving a `SolverRequest`, the solver agent uses an LLM to generate an answer. Then, it publishes a `IntermediateSolverResponse` or a `FinalSolverResponse` based on the round number.

The solver agent is given a topic type, which is used to indicate the topic to which the agent should publish intermediate responses. This topic is subscribed to by its neighbors to receive responses from this agent – we will show how this is done later.

We use `default_subscription()` to let solver agents subscribe to the default topic, which is used by the aggregator agent to collect the final responses from the solver agents.

```python
@default_subscription
class MathSolver(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, topic_type: str, num_neighbors: int, max_round: int) -> None:
        super().__init__("A debator.")
        self._topic_type = topic_type
        self._model_client = model_client
        self._num_neighbors = num_neighbors
        self._history: List[LLMMessage] = []
        self._buffer: Dict[int, List[IntermediateSolverResponse]] = {}
        self._system_messages = [
            SystemMessage(
                content=(
                    "You are a helpful assistant with expertise in mathematics and reasoning. "
                    "Your task is to assist in solving a math reasoning problem by providing "
                    "a clear and detailed solution. Limit your output within 100 words, "
                    "and your final answer should be a single numerical number, "
                    "in the form of {{answer}}, at the end of your response. "
                    "For example, 'The answer is {{42}}.'"
                )
            )
        ]
        self._round = 0
        self._max_round = max_round

    @message_handler
    async def handle_request(self, message: SolverRequest, ctx: MessageContext) -> None:
        # Add the question to the memory.
        self._history.append(UserMessage(content=message.content, source="user"))
        # Make an inference using the model.
        model_result = await self._model_client.create(self._system_messages + self._history)
        assert isinstance(model_result.content, str)
        # Add the response to the memory.
        self._history.append(AssistantMessage(content=model_result.content, source=self.metadata["type"]))
        print(f"{'-'*80}\nSolver {self.id} round {self._round}:\n{model_result.content}")
        # Extract the answer from the response.
        match = re.search(r"\{\{(\-?\d+(\.\d+)?)\}\}", model_result.content)
        if match is None:
            raise ValueError("The model response does not contain the answer.")
        answer = match.group(1)
        # Increment the counter.
        self._round += 1
        if self._round == self._max_round:
            # If the counter reaches the maximum round, publishes a final response.
            await self.publish_message(FinalSolverResponse(answer=answer), topic_id=DefaultTopicId())
        else:
            # Publish intermediate response to the topic associated with this solver.
            await self.publish_message(
                IntermediateSolverResponse(
                    content=model_result.content,
                    question=message.question,
                    answer=answer,
                    round=self._round,
                ),
                topic_id=DefaultTopicId(type=self._topic_type),
            )

    @message_handler
    async def handle_response(self, message: IntermediateSolverResponse, ctx: MessageContext) -> None:
        # Add neighbor's response to the buffer.
        self._buffer.setdefault(message.round, []).append(message)
        # Check if all neighbors have responded.
        if len(self._buffer[message.round]) == self._num_neighbors:
            print(
                f"{'-'*80}\nSolver {self.id} round {message.round}:\nReceived all responses from {self._num_neighbors} neighbors."
            )
            # Prepare the prompt for the next question.
            prompt = "These are the solutions to the problem from other agents:\n"
            for resp in self._buffer[message.round]:
                prompt += f"One agent solution: {resp.content}\n"
            prompt += (
                "Using the solutions from other agents as additional information, "
                "can you provide your answer to the math problem? "
                f"The original math problem is {message.question}. "
                "Your final answer should be a single numerical number, "
                "in the form of {{answer}}, at the end of your response."
            )
            # Send the question to the agent itself to solve.
            await self.send_message(SolverRequest(content=prompt, question=message.question), self.id)
            # Clear the buffer.
            self._buffer.pop(message.round)
```

## Aggregator Agent

The aggregator agent is responsible for handling user question and distributing math problems to the solver agents.

The aggregator subscribes to the default topic using `default_subscription()`. The default topic is used to recieve user question, receive the final responses from the solver agents, and publish the final answer back to the user.

In a more complex application when you want to isolate the multi-agent debate into a sub-component, you should use `type_subscription()` to set a specific topic type for the aggregator-solver communication, and have the both the solver and aggregator publish and subscribe to that topic type.

```python
@default_subscription
class MathAggregator(RoutedAgent):
    def __init__(self, num_solvers: int) -> None:
        super().__init__("Math Aggregator")
        self._num_solvers = num_solvers
        self._buffer: List[FinalSolverResponse] = []

    @message_handler
    async def handle_question(self, message: Question, ctx: MessageContext) -> None:
        print(f"{'-'*80}\nAggregator {self.id} received question:\n{message.content}")
        prompt = (
            f"Can you solve the following math problem?\n{message.content}\n"
            "Explain your reasoning. Your final answer should be a single numerical number, "
            "in the form of {{answer}}, at the end of your response."
        )
        print(f"{'-'*80}\nAggregator {self.id} publishes initial solver request.")
        await self.publish_message(SolverRequest(content=prompt, question=message.content), topic_id=DefaultTopicId())

    @message_handler
    async def handle_final_solver_response(self, message: FinalSolverResponse, ctx: MessageContext) -> None:
        self._buffer.append(message)
        if len(self._buffer) == self._num_solvers:
            print(f"{'-'*80}\nAggregator {self.id} received all final answers from {self._num_solvers} solvers.")
            # Find the majority answer.
            answers = [resp.answer for resp in self._buffer]
            majority_answer = max(set(answers), key=answers.count)
            # Publish the aggregated response.
            await self.publish_message(Answer(content=majority_answer), topic_id=DefaultTopicId())
            # Clear the responses.
            self._buffer.clear()
            print(f"{'-'*80}\nAggregator {self.id} publishes final answer:\n{majority_answer}")
```

## Setting Up a Debate

We will now set up a multi-agent debate with 4 solver agents and 1 aggregator agent. The solver agents will be connected in a sparse manner as illustrated in the figure below:

```
A --- B
|     |
|     |
D --- C
```

Each solver agent is connected to two other solver agents. For example, agent A is connected to agents B and C.

Let's first create a runtime and register the agent types.

```python
runtime = SingleThreadedAgentRuntime()

model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

await MathSolver.register(
    runtime,
    "MathSolverA",
    lambda: MathSolver(
        model_client=model_client,
        topic_type="MathSolverA",
        num_neighbors=2,
        max_round=3,
    ),
)
await MathSolver.register(
    runtime,
    "MathSolverB",
    lambda: MathSolver(
        model_client=model_client,
        topic_type="MathSolverB",
        num_neighbors=2,
        max_round=3,
    ),
)
await MathSolver.register(
    runtime,
    "MathSolverC",
    lambda: MathSolver(
        model_client=model_client,
        topic_type="MathSolverC",
        num_neighbors=2,
        max_round=3,
    ),
)
await MathSolver.register(
    runtime,
    "MathSolverD",
    lambda: MathSolver(
        model_client=model_client,
        topic_type="MathSolverD",
        num_neighbors=2,
        max_round=3,
    ),
)
await MathAggregator.register(runtime, "MathAggregator", lambda: MathAggregator(num_solvers=4))
```

Now we will create the solver agent topology using `TypeSubscription`, which maps each solver agent's publishing topic type to its neighbors' agent types.

```python
# Subscriptions for topic published to by MathSolverA.
await runtime.add_subscription(TypeSubscription("MathSolverA", "MathSolverD"))
await runtime.add_subscription(TypeSubscription("MathSolverA", "MathSolverB"))

# Subscriptions for topic published to by MathSolverB.
await runtime.add_subscription(TypeSubscription("MathSolverB", "MathSolverA"))
await runtime.add_subscription(TypeSubscription("MathSolverB", "MathSolverC"))

# Subscriptions for topic published to by MathSolverC.
await runtime.add_subscription(TypeSubscription("MathSolverC", "MathSolverB"))
await runtime.add_subscription(TypeSubscription("MathSolverC", "MathSolverD"))

# Subscriptions for topic published to by MathSolverD.
await runtime.add_subscription(TypeSubscription("MathSolverD", "MathSolverC"))
await runtime.add_subscription(TypeSubscription("MathSolverD", "MathSolverA"))

# All solvers and the aggregator subscribe to the default topic.
```

## Solving Math Problems

Now let's run the debate to solve a math problem. We publish a `SolverRequest` to the default topic, and the aggregator agent will start the debate.

```python
question = "Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether in April and May?"
runtime.start()
await runtime.publish_message(Question(content=question), DefaultTopicId())
# Wait for the runtime to stop when idle.
await runtime.stop_when_idle()
# Close the connection to the model client.
await model_client.close()
``` 