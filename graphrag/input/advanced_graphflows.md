# GraphFlow (Workflows)

In this section you'll learn how to create an multi-agent workflow using GraphFlow, or simply "flow" for short. It uses structured execution and precisely controls how agents interact to accomplish a task.

We'll first show you how to create and run a flow. We'll then explain how to observe and debug flow behavior, and discuss important operations for managing execution.

AutoGen AgentChat provides a team for directed graph execution:

**GraphFlow**: A team that follows a DiGraph to control the execution flow between agents. Supports sequential, parallel, conditional, and looping behaviors.

> **Note**: When should you use GraphFlow?
>
> Use Graph when you need strict control over the order in which agents act, or when different outcomes must lead to different next steps. Start with a simple team such as `RoundRobinGroupChat` or `SelectorGroupChat` if ad-hoc conversation flow is sufficient. Transition to a structured workflow when your task requires deterministic control, conditional branching, or handling complex multi-step processes with cycles.

> **Warning**: GraphFlow is an experimental feature. Its API, behavior, and capabilities are subject to change in future releases.

## Creating and Running a Flow

`DiGraphBuilder` is a fluent utility that lets you easily construct execution graphs for workflows. It supports building:

- Sequential chains
- Parallel fan-outs
- Conditional branching
- Loops with safe exit conditions

Each node in the graph represents an agent, and edges define the allowed execution paths. Edges can optionally have conditions based on agent messages.

### Sequential Flow

We will begin by creating a simple workflow where a writer drafts a paragraph and a reviewer provides feedback. This graph terminates after the reviewer comments on the writer.

Note, the flow automatically computes all the source and leaf nodes of the graph and the execution starts at all the source nodes in the graph and completes execution when no nodes are left to execute.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create an OpenAI model client
client = OpenAIChatCompletionClient(model="gpt-4.1-nano")

# Create the writer agent
writer = AssistantAgent("writer", model_client=client, system_message="Draft a short paragraph on climate change.")

# Create the reviewer agent
reviewer = AssistantAgent("reviewer", model_client=client, system_message="Review the draft and suggest improvements.")

# Build the graph
builder = DiGraphBuilder()
builder.add_node(writer).add_node(reviewer)
builder.add_edge(writer, reviewer)

# Build and validate the graph
graph = builder.build()

# Create the flow
flow = GraphFlow([writer, reviewer], graph=graph)
# Use `asyncio.run(...)` and wrap the below in a async function when running in a script.
stream = flow.run_stream(task="Write a short paragraph about climate change.")
async for event in stream:  # type: ignore
    print(event)
# Use Console(flow.run_stream(...)) for better formatting in console.
```

### Parallel Flow with Join

We now create a slightly more complex flow:

1. A writer drafts a paragraph.
2. Two editors independently edit for grammar and style (parallel fan-out).
3. A final reviewer consolidates their edits (join).

Execution starts at the writer, fans out to editor1 and editor2 simultaneously, and then both feed into the final reviewer.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create an OpenAI model client
client = OpenAIChatCompletionClient(model="gpt-4.1-nano")

# Create the writer agent
writer = AssistantAgent("writer", model_client=client, system_message="Draft a short paragraph on climate change.")

# Create two editor agents
editor1 = AssistantAgent("editor1", model_client=client, system_message="Edit the paragraph for grammar.")

editor2 = AssistantAgent("editor2", model_client=client, system_message="Edit the paragraph for style.")

# Create the final reviewer agent
final_reviewer = AssistantAgent(
    "final_reviewer",
    model_client=client,
    system_message="Consolidate the grammar and style edits into a final version.",
)

# Build the workflow graph
builder = DiGraphBuilder()
builder.add_node(writer).add_node(editor1).add_node(editor2).add_node(final_reviewer)

# Fan-out from writer to editor1 and editor2
builder.add_edge(writer, editor1)
builder.add_edge(writer, editor2)

# Fan-in both editors into final reviewer
builder.add_edge(editor1, final_reviewer)
builder.add_edge(editor2, final_reviewer)

# Build and validate the graph
graph = builder.build()

# Create the flow
flow = GraphFlow(
    participants=builder.get_participants(),
    graph=graph,
)

# Run the workflow
await Console(flow.run_stream(task="Write a short paragraph about climate change."))
```

## Message Filtering

### Execution Graph vs. Message Graph

In GraphFlow, the execution graph is defined using DiGraph, which controls the order in which agents execute. However, the execution graph does not control what messages an agent receives from other agents. By default, all messages are sent to all agents in the graph.

Message filtering is a separate feature that allows you to filter the messages received by each agent and limiting their model context to only the relevant information. The set of message filters defines the message graph in the flow.

Specifying the message graph can help with:

- Reduce hallucinations
- Control memory load
- Focus agents only on relevant information

You can use `MessageFilterAgent` together with `MessageFilterConfig` and `PerSourceFilter` to define these rules.

```python
from autogen_agentchat.agents import AssistantAgent, MessageFilterAgent, MessageFilterConfig, PerSourceFilter
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Model client
client = OpenAIChatCompletionClient(model="gpt-4.1-nano")

# Create agents
researcher = AssistantAgent(
    "researcher", model_client=client, system_message="Summarize key facts about climate change."
)
analyst = AssistantAgent("analyst", model_client=client, system_message="Review the summary and suggest improvements.")
presenter = AssistantAgent(
    "presenter", model_client=client, system_message="Prepare a presentation slide based on the final summary."
)

# Apply message filtering
filtered_analyst = MessageFilterAgent(
    name="analyst",
    wrapped_agent=analyst,
    filter=MessageFilterConfig(per_source=[PerSourceFilter(source="researcher", position="last", count=1)]),
)

filtered_presenter = MessageFilterAgent(
    name="presenter",
    wrapped_agent=presenter,
    filter=MessageFilterConfig(per_source=[PerSourceFilter(source="analyst", position="last", count=1)]),
)

# Build the flow
builder = DiGraphBuilder()
builder.add_node(researcher).add_node(filtered_analyst).add_node(filtered_presenter)
builder.add_edge(researcher, filtered_analyst).add_edge(filtered_analyst, filtered_presenter)

# Create the flow
flow = GraphFlow(
    participants=builder.get_participants(),
    graph=builder.build(),
)

# Run the flow
await Console(flow.run_stream(task="Summarize key facts about climate change."))
```

## 🔁 Advanced Example: Conditional Loop + Filtered Summary

This example demonstrates:

- A loop between generator and reviewer (which exits when reviewer says "APPROVE")
- A summarizer agent that only sees the first user input and the last reviewer message

```python
from autogen_agentchat.agents import AssistantAgent, MessageFilterAgent, MessageFilterConfig, PerSourceFilter
from autogen_agentchat.teams import (
    DiGraphBuilder,
    GraphFlow,
)
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

# Agents
generator = AssistantAgent("generator", model_client=model_client, system_message="Generate a list of creative ideas.")
reviewer = AssistantAgent(
    "reviewer",
    model_client=model_client,
    system_message="Review ideas and provide feedbacks, or just 'APPROVE' for final approval.",
)
summarizer_core = AssistantAgent(
    "summary", model_client=model_client, system_message="Summarize the user request and the final feedback."
)

# Filtered summarizer
filtered_summarizer = MessageFilterAgent(
    name="summary",
    wrapped_agent=summarizer_core,
    filter=MessageFilterConfig(
        per_source=[
            PerSourceFilter(source="user", position="first", count=1),
            PerSourceFilter(source="reviewer", position="last", count=1),
        ]
    ),
)

# Build graph with conditional loop
builder = DiGraphBuilder()
builder.add_node(generator).add_node(reviewer).add_node(filtered_summarizer)
builder.add_edge(generator, reviewer)
builder.add_edge(reviewer, filtered_summarizer, condition=lambda msg: "APPROVE" in msg.to_model_text())
builder.add_edge(reviewer, generator, condition=lambda msg: "APPROVE" not in msg.to_model_text())
builder.set_entry_point(generator)  # Set entry point to generator. Required if there are no source nodes.
graph = builder.build()

# Create the flow
flow = GraphFlow(
    participants=builder.get_participants(),
    graph=graph,
)

# Run the flow and pretty print the output in the console
await Console(flow.run_stream(task="Brainstorm ways to reduce plastic waste."))
```

## 🔁 Advanced Example: Cycles With Activation Group Examples

The following examples demonstrate how to use `activation_group` and `activation_condition` to handle complex dependency patterns in cyclic graphs, especially when multiple paths lead to the same target node.

### Example 1: Loop with Multiple Paths - "All" Activation (A→B→C→B)

In this scenario, we have A → B → C → B, where B has two incoming edges (from A and from C). By default, B requires all its dependencies to be satisfied before executing.

This example shows a review loop where both the initial input (A) and the feedback (C) must be processed before B can execute again.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Model client
client = OpenAIChatCompletionClient(model="gpt-4o-mini")

# Create agents for A→B→C→B→E scenario
agent_a = AssistantAgent("A", model_client=client, system_message="Start the process and provide initial input.")
agent_b = AssistantAgent(
    "B",
    model_client=client,
    system_message="Process input from A or feedback from C. Say 'CONTINUE' if it's from A or 'STOP' if it's from C.",
)
agent_c = AssistantAgent("C", model_client=client, system_message="Review B's output and provide feedback.")
agent_e = AssistantAgent("E", model_client=client, system_message="Finalize the process.")

# Build the graph with activation groups
builder = DiGraphBuilder()
builder.add_node(agent_a).add_node(agent_b).add_node(agent_c).add_node(agent_e)

# A → B (initial path)
builder.add_edge(agent_a, agent_b, activation_group="initial")

# B → C
builder.add_edge(agent_b, agent_c, condition="CONTINUE")

# C → B (loop back - different activation group)
builder.add_edge(agent_c, agent_b, activation_group="feedback")

# B → E (exit condition)
builder.add_edge(agent_b, agent_e, condition="STOP")

# Build and create flow
graph = builder.build()
flow = GraphFlow(participants=[agent_a, agent_b, agent_c], graph=graph)

print("=== Example 1: A→B→C→B with 'All' Activation ===")
print("B will exit when it receives a message from C")
# await Console(flow.run_stream(task="Start a review process for a document."))
```

### Example 2: Loop with Multiple Paths - "Any" Activation (A→B→(C1,C2)→B)

In this more complex scenario, we have A → B → (C1, C2) → B, where:

- B fans out to both C1 and C2 in parallel
- Both C1 and C2 feed back to B
- B uses "any" activation, meaning it executes as soon as either C1 or C2 completes

This is useful for scenarios where you want the fastest response to trigger the next step.

```python
# Create agents for A→B→(C1,C2)→B scenario
agent_a2 = AssistantAgent("A", model_client=client, system_message="Initiate a task that needs parallel processing.")
agent_b2 = AssistantAgent(
    "B",
    model_client=client,
    system_message="Coordinate parallel tasks. Say 'PROCESS' to start parallel work or 'DONE' to finish.",
)
agent_c1 = AssistantAgent("C1", model_client=client, system_message="Handle task type 1. Say 'C1_COMPLETE' when done.")
agent_c2 = AssistantAgent("C2", model_client=client, system_message="Handle task type 2. Say 'C2_COMPLETE' when done.")
agent_e = AssistantAgent("E", model_client=client, system_message="Finalize the process.")

# Build the graph with "any" activation
builder2 = DiGraphBuilder()
builder2.add_node(agent_a2).add_node(agent_b2).add_node(agent_c1).add_node(agent_c2).add_node(agent_e)

# A → B (initial)
builder2.add_edge(agent_a2, agent_b2)

# B → C1 and B → C2 (parallel fan-out)
builder2.add_edge(agent_b2, agent_c1, condition="PROCESS")
builder2.add_edge(agent_b2, agent_c2, condition="PROCESS")

# B → E (exit condition)
builder2.add_edge(agent_b2, agent_e, condition=lambda msg: "DONE" in msg.to_model_text())

# C1 → B and C2 → B (both in same activation group with "any" condition)
builder2.add_edge(
    agent_c1, agent_b2, activation_group="loop_back_group", activation_condition="any", condition="C1_COMPLETE"
)

builder2.add_edge(
    agent_c2, agent_b2, activation_group="loop_back_group", activation_condition="any", condition="C2_COMPLETE"
)

# Build and create flow
graph2 = builder2.build()
flow2 = GraphFlow(participants=[agent_a2, agent_b2, agent_c1, agent_c2, agent_e], graph=graph2)

print("=== Example 2: A→B→(C1,C2)→B with 'Any' Activation ===")
print("B will execute as soon as EITHER C1 OR C2 completes (whichever finishes first)")
# await Console(flow2.run_stream(task="Start a parallel processing task."))
```

### Example 3: Mixed Activation Groups

This example shows how different activation groups can coexist in the same graph. We have a scenario where:

- Node D receives inputs from multiple sources with different activation requirements
- Some dependencies use "all" activation (must wait for all inputs)
- Other dependencies use "any" activation (proceed on first input)

This pattern is useful for complex workflows where different types of dependencies have different urgency levels.

```python
# Create agents for mixed activation scenario
agent_a3 = AssistantAgent("A", model_client=client, system_message="Provide critical input that must be processed.")
agent_b3 = AssistantAgent("B", model_client=client, system_message="Provide secondary critical input.")
agent_c3 = AssistantAgent("C", model_client=client, system_message="Provide optional quick input.")
agent_d3 = AssistantAgent("D", model_client=client, system_message="Process inputs based on different priority levels.")

# Build graph with mixed activation groups
builder3 = DiGraphBuilder()
builder3.add_node(agent_a3).add_node(agent_b3).add_node(agent_c3).add_node(agent_d3)

# Critical inputs that must ALL be present (activation_group="critical", activation_condition="all")
builder3.add_edge(agent_a3, agent_d3, activation_group="critical", activation_condition="all")
builder3.add_edge(agent_b3, agent_d3, activation_group="critical", activation_condition="all")

# Optional input that can trigger execution on its own (activation_group="optional", activation_condition="any")
builder3.add_edge(agent_c3, agent_d3, activation_group="optional", activation_condition="any")

# Build and create flow
graph3 = builder3.build()
flow3 = GraphFlow(participants=[agent_a3, agent_b3, agent_c3, agent_d3], graph=graph3)

print("=== Example 3: Mixed Activation Groups ===")
print("D will execute when:")
print("- BOTH A AND B complete (critical group with 'all' activation), OR")
print("- C completes (optional group with 'any' activation)")
print("This allows for both required dependencies and fast-path triggers.")
# await Console(flow3.run_stream(task="Process inputs with mixed priority levels."))
```

## Key Takeaways for Activation Groups

- **activation_group**: Groups edges that point to the same target node, allowing you to define different dependency patterns.

- **activation_condition**:
  - `"all"` (default): Target node waits for ALL edges in the group to be satisfied
  - `"any"`: Target node executes as soon as ANY edge in the group is satisfied

- **Use Cases**:
  - Cycles with multiple entry points: Different activation groups prevent conflicts
  - Priority-based execution: Mix "all" and "any" conditions for different urgency levels
  - Parallel processing with early termination: Use "any" to proceed with the fastest result

- **Best Practices**:
  - Use descriptive group names ("critical", "optional", "feedback", etc.)
  - Keep activation conditions consistent within the same group
  - Test your graph logic with different execution paths

These patterns enable sophisticated workflow control while maintaining clear, understandable execution semantics.

