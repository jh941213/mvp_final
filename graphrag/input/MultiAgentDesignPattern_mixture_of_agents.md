# Mixture of Agents

Mixture of Agents is a multi-agent design pattern that models after the feed-forward neural network architecture.

The pattern consists of two types of agents: worker agents and a single orchestrator agent. Worker agents are organized into multiple layers, with each layer consisting of a fixed number of worker agents. Messages from the worker agents in a previous layer are concatenated and sent to all the worker agents in the next layer.

This example implements the Mixture of Agents pattern using the core library following the original implementation of multi-layer mixture of agents.

Here is a high-level procedure overview of the pattern:

1. The orchestrator agent takes input a user task and first dispatches it to the worker agents in the first layer.
2. The worker agents in the first layer process the task and return the results to the orchestrator agent.
3. The orchestrator agent then synthesizes the results from the first layer and dispatches an updated task with the previous results to the worker agents in the second layer.
4. The process continues until the final layer is reached.
5. In the final layer, the orchestrator agent aggregates the results from previous layer and returns a single final result to the user.

We use the direct messaging API `send_message()` to implement this pattern. This makes it easier to add more features like worker task cancellation and error handling in the future.

```python
import asyncio
from dataclasses import dataclass
from typing import List

from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
```

## Message Protocol

The agents communicate using the following messages:

```python
@dataclass
class WorkerTask:
    task: str
    previous_results: List[str]


@dataclass
class WorkerTaskResult:
    result: str


@dataclass
class UserTask:
    task: str


@dataclass
class FinalResult:
    result: str
```

## Worker Agent

Each worker agent receives a task from the orchestrator agent and processes them indepedently. Once the task is completed, the worker agent returns the result.

```python
class WorkerAgent(RoutedAgent):
    def __init__(
        self,
        model_client: ChatCompletionClient,
    ) -> None:
        super().__init__(description="Worker Agent")
        self._model_client = model_client

    @message_handler
    async def handle_task(self, message: WorkerTask, ctx: MessageContext) -> WorkerTaskResult:
        if message.previous_results:
            # If previous results are provided, we need to synthesize them to create a single prompt.
            system_prompt = "You have been provided with a set of responses from various open-source models to the latest user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.\n\nResponses from models:"
            system_prompt += "\n" + "\n\n".join([f"{i+1}. {r}" for i, r in enumerate(message.previous_results)])
            model_result = await self._model_client.create(
                [SystemMessage(content=system_prompt), UserMessage(content=message.task, source="user")]
            )
        else:
            # If no previous results are provided, we can simply pass the user query to the model.
            model_result = await self._model_client.create([UserMessage(content=message.task, source="user")])
        assert isinstance(model_result.content, str)
        print(f"{'-'*80}\nWorker-{self.id}:\n{model_result.content}")
        return WorkerTaskResult(result=model_result.content)
```

## Orchestrator Agent

The orchestrator agent receives tasks from the user and distributes them to the worker agents, iterating over multiple layers of worker agents. Once all worker agents have processed the task, the orchestrator agent aggregates the results and publishes the final result.

```python
class OrchestratorAgent(RoutedAgent):
    def __init__(
        self,
        model_client: ChatCompletionClient,
        worker_agent_types: List[str],
        num_layers: int,
    ) -> None:
        super().__init__(description="Aggregator Agent")
        self._model_client = model_client
        self._worker_agent_types = worker_agent_types
        self._num_layers = num_layers

    @message_handler
    async def handle_task(self, message: UserTask, ctx: MessageContext) -> FinalResult:
        print(f"{'-'*80}\nOrchestrator-{self.id}:\nReceived task: {message.task}")
        # Create task for the first layer.
        worker_task = WorkerTask(task=message.task, previous_results=[])
        # Iterate over layers.
        for i in range(self._num_layers - 1):
            # Assign workers for this layer.
            worker_ids = [
                AgentId(worker_type, f"{self.id.key}/layer_{i}/worker_{j}")
                for j, worker_type in enumerate(self._worker_agent_types)
            ]
            # Dispatch tasks to workers.
            print(f"{'-'*80}\nOrchestrator-{self.id}:\nDispatch to workers at layer {i}")
            results = await asyncio.gather(*[self.send_message(worker_task, worker_id) for worker_id in worker_ids])
            print(f"{'-'*80}\nOrchestrator-{self.id}:\nReceived results from workers at layer {i}")
            # Prepare task for the next layer.
            worker_task = WorkerTask(task=message.task, previous_results=[r.result for r in results])
        # Perform final aggregation.
        print(f"{'-'*80}\nOrchestrator-{self.id}:\nPerforming final aggregation")
        system_prompt = "You have been provided with a set of responses from various open-source models to the latest user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.\n\nResponses from models:"
        system_prompt += "\n" + "\n\n".join([f"{i+1}. {r}" for i, r in enumerate(worker_task.previous_results)])
        model_result = await self._model_client.create(
            [SystemMessage(content=system_prompt), UserMessage(content=message.task, source="user")]
        )
        assert isinstance(model_result.content, str)
        return FinalResult(result=model_result.content)
```

## Running Mixture of Agents

Let's run the mixture of agents on a math task. You can change the task to make it more challenging, for example, by trying tasks from the International Mathematical Olympiad.

```python
task = (
    "I have 432 cookies, and divide them 3:4:2 between Alice, Bob, and Charlie. How many cookies does each person get?"
)
```

Let's set up the runtime with 3 layers of worker agents, each layer consisting of 3 worker agents. We only need to register a single worker agent types, "worker", because we are using the same model client configuration (i.e., gpt-4o-mini) for all worker agents. If you want to use different models, you will need to register multiple worker agent types, one for each model, and update the worker_agent_types list in the orchestrator agent's factory function.

The instances of worker agents are automatically created when the orchestrator agent dispatches tasks to them. See Agent Identity and Lifecycle for more information on agent lifecycle.

```python
runtime = SingleThreadedAgentRuntime()
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
await WorkerAgent.register(runtime, "worker", lambda: WorkerAgent(model_client=model_client))
await OrchestratorAgent.register(
    runtime,
    "orchestrator",
    lambda: OrchestratorAgent(model_client=model_client, worker_agent_types=["worker"] * 3, num_layers=3),
)

runtime.start()
result = await runtime.send_message(UserTask(task=task), AgentId("orchestrator", "default"))

await runtime.stop_when_idle()
await model_client.close()

print(f"{'-'*80}\nFinal result:\n{result.result}") 