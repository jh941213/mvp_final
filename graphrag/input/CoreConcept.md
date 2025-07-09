# Agent Runtime Environments

At the foundation level, the framework provides a runtime environment, which facilitates communication between agents, manages their identities and lifecycles, and enforce security and privacy boundaries.

It supports two types of runtime environment: **standalone** and **distributed**. Both types provide a common set of APIs for building multi-agent applications, so you can switch between them without changing your agent implementation. Each type can also have multiple implementations.

## Standalone Agent Runtime

Standalone runtime is suitable for single-process applications where all agents are implemented in the same programming language and running in the same process. In the Python API, an example of standalone runtime is the `SingleThreadedAgentRuntime`.

The following diagram shows the standalone runtime in the framework.

**Standalone Runtime**

Here, agents communicate via messages through the runtime, and the runtime manages the lifecycle of agents.

Developers can build agents quickly by using the provided components including routed agent, AI model clients, tools for AI models, code execution sandboxes, model context stores, and more. They can also implement their own agents from scratch, or use other libraries.

## Distributed Agent Runtime

Distributed runtime is suitable for multi-process applications where agents may be implemented in different programming languages and running on different machines.

**Distributed Runtime**

A distributed runtime, as shown in the diagram above, consists of a **host servicer** and multiple **workers**. The host servicer facilitates communication between agents across workers and maintains the states of connections. The workers run agents and communicate with the host servicer via gateways. They advertise to the host servicer the agents they run and manage the agents' lifecycles.

Agents work the same way as in the standalone runtime so that developers can switch between the two runtime types with no change to their agent implementation.

## Application Stack

AutoGen core is designed to be an unopinionated framework that can be used to build a wide variety of multi-agent applications. It is not tied to any specific agent abstraction or multi-agent pattern.

The following diagram shows the application stack.

**Application Stack**

At the bottom of the stack is the base messaging and routing facilities that enable agents to communicate with each other. These are managed by the agent runtime, and for most applications, developers only need to interact with the high-level APIs provided by the runtime (see Agent and Agent Runtime).

At the top of the stack, developers need to define the types of the messages that agents exchange. This set of message types forms a **behavior contract** that agents must adhere to, and the implementation of the contracts determines how agents handle messages. The behavior contract is also sometimes referred to as the **message protocol**. It is the developer's responsibility to implement the behavior contract. Multi-agent patterns emerge from these behavior contracts (see Multi-Agent Design Patterns).

## An Example Application

Consider a concrete example of a multi-agent application for code generation. The application consists of three agents: **Coder Agent**, **Executor Agent**, and **Reviewer Agent**. The following diagram shows the data flow between the agents, and the message types exchanged between them.

**Code Generation Example**

In this example, the behavior contract consists of the following:

- `CodingTaskMsg` message from application to the Coder Agent
- `CodeGenMsg` from Coder Agent to Executor Agent
- `ExecutionResultMsg` from Executor Agent to Reviewer Agent
- `ReviewMsg` from Reviewer Agent to Coder Agent
- `CodingResultMsg` from the Reviewer Agent to the application

The behavior contract is implemented by the agents' handling of these messages. For example, the Reviewer Agent listens for `ExecutionResultMsg` and evaluates the code execution result to decide whether to approve or reject, if approved, it sends a `CodingResultMsg` to the application, otherwise, it sends a `ReviewMsg` to the Coder Agent for another round of code generation.

This behavior contract is a case of a multi-agent pattern called **reflection**, where a generation result is reviewed by another round of generation, to improve the overall quality.

# Agent Identity and Lifecycle

The agent runtime manages agents' identities and lifecycles. Application does not create agents directly, rather, it registers an agent type with a factory function for agent instances. In this section, we explain how agents are identified and created by the runtime.

## Agent ID

Agent ID uniquely identifies an agent instance within an agent runtime – including distributed runtime. It is the "address" of the agent instance for receiving messages. It has two components: agent type and agent key.

> **Note:** Agent ID = (Agent Type, Agent Key)

The agent type is not an agent class. It associates an agent with a specific factory function, which produces instances of agents of the same agent type. For example, different factory functions can produce the same agent class but with different constructor parameters. The agent key is an instance identifier for the given agent type. Agent IDs can be converted to and from strings. the format of this string is:

> **Note:** Agent_Type/Agent_Key

Types and Keys are considered valid if they only contain alphanumeric letters (a-z) and (0-9), or underscores (_). A valid identifier cannot start with a number, or contain any spaces.

In a multi-agent application, agent types are typically defined directly by the application, i.e., they are defined in the application code. On the other hand, agent keys are typically generated given messages delivered to the agents, i.e., they are defined by the application data.

For example, a runtime has registered the agent type "code_reviewer" with a factory function producing agent instances that perform code reviews. Each code review request has a unique ID `review_request_id` to mark a dedicated session. In this case, each request can be handled by a new instance with an agent ID, ("code_reviewer", review_request_id).

## Agent Lifecycle

When a runtime delivers a message to an agent instance given its ID, it either fetches the instance, or creates it if it does not exist.

**Agent Lifecycle**

The runtime is also responsible for "paging in" or "out" agent instances to conserve resources and balance load across multiple machines. This is not implemented yet

# Topic and Subscription

There are two ways for runtime to deliver messages, **direct messaging** or **broadcast**. Direct messaging is one to one: the sender must provide the recipient's agent ID. On the other hand, broadcast is one to many and the sender does not provide recipients' agent IDs.

Many scenarios are suitable for broadcast. For example, in event-driven workflows, agents do not always know who will handle their messages, and a workflow can be composed of agents with no inter-dependencies. This section focuses on the core concepts in broadcast: topic and subscription.

## Topic

A topic defines the scope of a broadcast message. In essence, agent runtime implements a publish-subscribe model through its broadcast API: when publishing a message, the topic must be specified. It is an indirection over agent IDs.

A topic consists of two components: topic type and topic source.

> **Note:** Topic = (Topic Type, Topic Source)

Similar to agent ID, which also has two components, topic type is usually defined by application code to mark the type of messages the topic is for. For example, a GitHub agent may use "GitHub_Issues" as the topic type when publishing messages about new issues.

Topic source is the unique identifier for a topic within a topic type. It is typically defined by application data. For example, the GitHub agent may use "github.com/{repo_name}/issues/{issue_number}" as the topic source to uniquely identifies the topic. Topic source allows the publisher to limit the scope of messages and create silos.

Topic IDs can be converted to and from strings. the format of this string is:

> **Note:** Topic_Type/Topic_Source

Types are considered valid if they are in UTF8 and only contain alphanumeric letters (a-z) and (0-9), or underscores (_). A valid identifier cannot start with a number, or contain any spaces. Sources are considered valid if they are in UTF8 and only contain characters between (inclusive) ascii 32 (space) and 126 (~).

## Subscription

A subscription maps topic to agent IDs.

**Subscription**

The diagram above shows the relationship between topic and subscription. An agent runtime keeps track of the subscriptions and uses them to deliver messages to agents.

If a topic has no subscription, messages published to this topic will not be delivered to any agent. If a topic has many subscriptions, messages will be delivered following all the subscriptions to every recipient agent only once. Applications can add or remove subscriptions using agent runtime's API.

## Type-based Subscription

A type-based subscription maps a topic type to an agent type (see agent ID). It declares an unbounded mapping from topics to agent IDs without knowing the exact topic sources and agent keys. The mechanism is simple: any topic matching the type-based subscription's topic type will be mapped to an agent ID with the subscription's agent type and the agent key assigned to the value of the topic source. For Python API, use `TypeSubscription`.

> **Note:** Type-Based Subscription = Topic Type –> Agent Type

Generally speaking, type-based subscription is the preferred way to declare subscriptions. It is portable and data-independent: developers do not need to write application code that depends on specific agent IDs.

### Scenarios of Type-Based Subscription

Type-based subscriptions can be applied to many scenarios when the exact topic or agent IDs are data-dependent. The scenarios can be broken down by two considerations: (1) whether it is single-tenant or multi-tenant, and (2) whether it is a single topic or multiple topics per tenant. A tenant typically refers to a set of agents that handle a specific user session or a specific request.

#### Single-Tenant, Single Topic

In this scenario, there is only one tenant and one topic for the entire application. It is the simplest scenario and can be used in many cases like a command line tool or a single-user application.

To apply type-based subscription for this scenario, create one type-based subscription for each agent type, and use the same topic type for all the type-based subscriptions. When you publish, always use the same topic, i.e., the same topic type and topic source.

For example, assuming there are three agent types: "triage_agent", "coder_agent" and "reviewer_agent", and the topic type is "default", create the following type-based subscriptions:

```python
# Type-based Subscriptions for single-tenant, single topic scenario
TypeSubscription(topic_type="default", agent_type="triage_agent")
TypeSubscription(topic_type="default", agent_type="coder_agent")
TypeSubscription(topic_type="default", agent_type="reviewer_agent")
```

With the above type-based subscriptions, use the same topic source "default" for all messages. So the topic is always ("default", "default"). A message published to this topic will be delivered to all the agents of all above types. Specifically, the message will be sent to the following agent IDs:

```python
# The agent IDs created based on the topic source
AgentID("triage_agent", "default")
AgentID("coder_agent", "default")
AgentID("reviewer_agent", "default")
```

The following figure shows how type-based subscription works in this example.

**Type-Based Subscription Single-Tenant, Single Topic Scenario Example**

If the agent with the ID does not exist, the runtime will create it.

#### Single-Tenant, Multiple Topics

In this scenario, there is only one tenant but you want to control which agent handles which topic. This is useful when you want to create silos and have different agents specialized in handling different topics.

To apply type-based subscription for this scenario, create one type-based subscription for each agent type but with different topic types. You can map the same topic type to multiple agent types if you want these agent types to share a same topic. For topic source, still use the same value for all messages when you publish.

Continuing the example above with same agent types, create the following type-based subscriptions:

```python
# Type-based Subscriptions for single-tenant, multiple topics scenario
TypeSubscription(topic_type="triage", agent_type="triage_agent")
TypeSubscription(topic_type="coding", agent_type="coder_agent")
TypeSubscription(topic_type="coding", agent_type="reviewer_agent")
```

With the above type-based subscriptions, any message published to the topic ("triage", "default") will be delivered to the agent with type "triage_agent", and any message published to the topic ("coding", "default") will be delivered to the agents with types "coder_agent" and "reviewer_agent".

The following figure shows how type-based subscription works in this example.

**Type-Based Subscription Single-Tenant, Multiple Topics Scenario Example**

#### Multi-Tenant Scenarios

In single-tenant scenarios, the topic source is always the same (e.g., "default") – it is hard-coded in the application code. When moving to multi-tenant scenarios, the topic source becomes data-dependent.

> **Note:** A good indication that you are in a multi-tenant scenario is that you need multiple instances of the same agent type. For example, you may want to have different agent instances to handle different user sessions to keep private data isolated, or, you may want to distribute a heavy workload across multiple instances of the same agent type and have them work on it concurrently.

Continuing the example above, if you want to have dedicated instances of agents to handle a specific GitHub issue, you need to set the topic source to be a unique identifier for the issue.

For example, let's say there is one type-based subscription for the agent type "triage_agent":

```python
TypeSubscription(topic_type="github_issues", agent_type="triage_agent")
```

When a message is published to the topic ("github_issues", "github.com/microsoft/autogen/issues/1"), the runtime will deliver the message to the agent with ID ("triage_agent", "github.com/microsoft/autogen/issues/1"). When a message is published to the topic ("github_issues", "github.com/microsoft/autogen/issues/9"), the runtime will deliver the message to the agent with ID ("triage_agent", "github.com/microsoft/autogen/issues/9").

The following figure shows how type-based subscription works in this example.

**Type-Based Subscription Multi-Tenant Scenario Example**

Note the agent ID is data-dependent, and the runtime will create a new instance of the agent if it does not exist.

To support multiple topics per tenant, you can use different topic types, just like the single-tenant, multiple topics scenario.
