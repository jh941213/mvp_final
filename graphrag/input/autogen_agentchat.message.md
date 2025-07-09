autogen_agentchat.messages
This module defines various message types used for agent-to-agent communication. Each message type inherits either from the BaseChatMessage class or BaseAgentEvent class and includes specific fields relevant to the type of message being sent.

AgentEvent
The union type of all built-in concrete subclasses of BaseAgentEvent.

alias of Annotated[ToolCallRequestEvent | ToolCallExecutionEvent | MemoryQueryEvent | UserInputRequestedEvent | ModelClientStreamingChunkEvent | ThoughtEvent | SelectSpeakerEvent | CodeGenerationEvent | CodeExecutionEvent, FieldInfo(annotation=NoneType, required=True, discriminator=’type’)]

pydantic model BaseAgentEvent[source]
Bases: BaseMessage, ABC

Base class for agent events.

Note

If you want to create a new message type for signaling observable events to user and application, inherit from this class.

Agent events are used to signal actions and thoughts produced by agents and teams to user and applications. They are not used for agent-to-agent communication and are not expected to be processed by other agents.

You should override the to_text() method if you want to provide a custom rendering of the content.

Show JSON schema
Fields
:
created_at (datetime.datetime)

id (str)

metadata (Dict[str, str])

models_usage (autogen_core.models._types.RequestUsage | None)

source (str)

field created_at: datetime [Optional]
The time when the message was created.

field id: str [Optional]
Unique identifier for this event.

field metadata: Dict[str, str] = {}
Additional metadata about the message.

field models_usage: RequestUsage | None = None
The model client usage incurred when producing this message.

field source: str [Required]
The name of the agent that sent this message.

pydantic model BaseChatMessage[source]
Bases: BaseMessage, ABC

Abstract base class for chat messages.

Note

If you want to create a new message type that is used for agent-to-agent communication, inherit from this class, or simply use StructuredMessage if your content type is a subclass of Pydantic BaseModel.

This class is used for messages that are sent between agents in a chat conversation. Agents are expected to process the content of the message using models and return a response as another BaseChatMessage.

Show JSON schema
Fields
:
created_at (datetime.datetime)

id (str)

metadata (Dict[str, str])

models_usage (autogen_core.models._types.RequestUsage | None)

source (str)

field created_at: datetime [Optional]
The time when the message was created.

field id: str [Optional]
Unique identifier for this message.

field metadata: Dict[str, str] = {}
Additional metadata about the message.

field models_usage: RequestUsage | None = None
The model client usage incurred when producing this message.

field source: str [Required]
The name of the agent that sent this message.

abstract to_model_message() → UserMessage[source]
Convert the message content to a UserMessage for use with model client, e.g., ChatCompletionClient.

abstract to_model_text() → str[source]
Convert the content of the message to text-only representation. This is used for creating text-only content for models.

This is not used for rendering the message in console. For that, use to_text().

The difference between this and to_model_message() is that this is used to construct parts of the a message for the model client, while to_model_message() is used to create a complete message for the model client.

pydantic model BaseMessage[source]
Bases: BaseModel, ABC

Abstract base class for all message types in AgentChat.

Warning

If you want to create a new message type, do not inherit from this class. Instead, inherit from BaseChatMessage or BaseAgentEvent to clarify the purpose of the message type.

Show JSON schema
dump() → Mapping[str, Any][source]
Convert the message to a JSON-serializable dictionary.

The default implementation uses the Pydantic model’s model_dump() method to convert the message to a dictionary. Override this method if you want to customize the serialization process or add additional fields to the output.

classmethod load(data: Mapping[str, Any]) → Self[source]
Create a message from a dictionary of JSON-serializable data.

The default implementation uses the Pydantic model’s model_validate() method to create the message from the data. Override this method if you want to customize the deserialization process or add additional fields to the input data.

abstract to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model BaseTextChatMessage[source]
Bases: BaseChatMessage, ABC

Base class for all text-only BaseChatMessage types. It has implementations for to_text(), to_model_text(), and to_model_message() methods.

Inherit from this class if your message content type is a string.

Show JSON schema
Fields
:
content (str)

field content: str [Required]
The content of the message.

to_model_message() → UserMessage[source]
Convert the message content to a UserMessage for use with model client, e.g., ChatCompletionClient.

to_model_text() → str[source]
Convert the content of the message to text-only representation. This is used for creating text-only content for models.

This is not used for rendering the message in console. For that, use to_text().

The difference between this and to_model_message() is that this is used to construct parts of the a message for the model client, while to_model_message() is used to create a complete message for the model client.

to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

ChatMessage
The union type of all built-in concrete subclasses of BaseChatMessage. It does not include StructuredMessage types.

alias of Annotated[TextMessage | MultiModalMessage | StopMessage | ToolCallSummaryMessage | HandoffMessage, FieldInfo(annotation=NoneType, required=True, discriminator=’type’)]

pydantic model CodeExecutionEvent[source]
Bases: BaseAgentEvent

An event signaling code execution event.

Show JSON schema
Fields
:
result (autogen_core.code_executor._base.CodeResult)

retry_attempt (int)

type (Literal['CodeExecutionEvent'])

field result: CodeResult [Required]
Code Execution Result

field retry_attempt: int [Required]
Retry number, 0 means first execution

field type: Literal['CodeExecutionEvent'] = 'CodeExecutionEvent'
to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model CodeGenerationEvent[source]
Bases: BaseAgentEvent

An event signaling code generation event.

Show JSON schema
Fields
:
code_blocks (List[autogen_core.code_executor._base.CodeBlock])

content (str)

retry_attempt (int)

type (Literal['CodeGenerationEvent'])

field code_blocks: List[CodeBlock] [Required]
List of code blocks present in content

field content: str [Required]
The complete content as string.

field retry_attempt: int [Required]
Retry number, 0 means first generation

field type: Literal['CodeGenerationEvent'] = 'CodeGenerationEvent'
to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model HandoffMessage[source]
Bases: BaseTextChatMessage

A message requesting handoff of a conversation to another agent.

Show JSON schema
Fields
:
context (List[Annotated[autogen_core.models._types.SystemMessage | autogen_core.models._types.UserMessage | autogen_core.models._types.AssistantMessage | autogen_core.models._types.FunctionExecutionResultMessage, FieldInfo(annotation=NoneType, required=True, discriminator='type')]])

target (str)

type (Literal['HandoffMessage'])

field context: List[Annotated[SystemMessage | UserMessage | AssistantMessage | FunctionExecutionResultMessage, FieldInfo(annotation=NoneType, required=True, discriminator='type')]] = []
The model context to be passed to the target agent.

field target: str [Required]
The name of the target agent to handoff to.

field type: Literal['HandoffMessage'] = 'HandoffMessage'
pydantic model MemoryQueryEvent[source]
Bases: BaseAgentEvent

An event signaling the results of memory queries.

Show JSON schema
Fields
:
content (List[autogen_core.memory._base_memory.MemoryContent])

type (Literal['MemoryQueryEvent'])

field content: List[MemoryContent] [Required]
The memory query results.

field type: Literal['MemoryQueryEvent'] = 'MemoryQueryEvent'
to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model ModelClientStreamingChunkEvent[source]
Bases: BaseAgentEvent

An event signaling a text output chunk from a model client in streaming mode.

Show JSON schema
Fields
:
content (str)

full_message_id (str | None)

type (Literal['ModelClientStreamingChunkEvent'])

field content: str [Required]
A string chunk from the model client.

field full_message_id: str | None = None
Optional reference to the complete message that may come after the chunks. This allows consumers of the stream to correlate chunks with the eventual completed message.

field type: Literal['ModelClientStreamingChunkEvent'] = 'ModelClientStreamingChunkEvent'
to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model MultiModalMessage[source]
Bases: BaseChatMessage

A multimodal message.

Show JSON schema
Fields
:
content (List[str | autogen_core._image.Image])

type (Literal['MultiModalMessage'])

field content: List[str | Image] [Required]
The content of the message.

field type: Literal['MultiModalMessage'] = 'MultiModalMessage'
to_model_message() → UserMessage[source]
Convert the message content to a UserMessage for use with model client, e.g., ChatCompletionClient.

to_model_text(image_placeholder: str | None = '[image]') → str[source]
Convert the content of the message to a string-only representation. If an image is present, it will be replaced with the image placeholder by default, otherwise it will be a base64 string when set to None.

to_text(iterm: bool = False) → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model SelectSpeakerEvent[source]
Bases: BaseAgentEvent

An event signaling the selection of speakers for a conversation.

Show JSON schema
Fields
:
content (List[str])

type (Literal['SelectSpeakerEvent'])

field content: List[str] [Required]
The names of the selected speakers.

field type: Literal['SelectSpeakerEvent'] = 'SelectSpeakerEvent'
to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model StopMessage[source]
Bases: BaseTextChatMessage

A message requesting stop of a conversation.

Show JSON schema
Fields
:
type (Literal['StopMessage'])

field type: Literal['StopMessage'] = 'StopMessage'
class StructuredContentType
Type variable for structured content types.

alias of TypeVar(‘StructuredContentType’, bound=BaseModel, covariant=True)

pydantic model StructuredMessage[source]
Bases: BaseChatMessage, Generic[StructuredContentType]

A BaseChatMessage type with an unspecified content type.

To create a new structured message type, specify the content type as a subclass of Pydantic BaseModel.

from pydantic import BaseModel
from autogen_agentchat.messages import StructuredMessage


class MyMessageContent(BaseModel):
    text: str
    number: int


message = StructuredMessage[MyMessageContent](
    content=MyMessageContent(text="Hello", number=42),
    source="agent1",
)

print(message.to_text())  # {"text": "Hello", "number": 42}
from pydantic import BaseModel
from autogen_agentchat.messages import StructuredMessage


class MyMessageContent(BaseModel):
    text: str
    number: int


message = StructuredMessage[MyMessageContent](
    content=MyMessageContent(text="Hello", number=42),
    source="agent",
    format_string="Hello, {text} {number}!",
)

print(message.to_text())  # Hello, agent 42!
Show JSON schema
Fields
:
content (autogen_agentchat.messages.StructuredContentType)

format_string (str | None)

field content: StructuredContentType [Required]
The content of the message. Must be a subclass of Pydantic BaseModel.

field format_string: str | None = None
(Experimental) An optional format string to render the content into a human-readable format. The format string can use the fields of the content model as placeholders. For example, if the content model has a field name, you can use {name} in the format string to include the value of that field. The format string is used in the to_text() method to create a human-readable representation of the message. This setting is experimental and will change in the future.

to_model_message() → UserMessage[source]
Convert the message content to a UserMessage for use with model client, e.g., ChatCompletionClient.

to_model_text() → str[source]
Convert the content of the message to text-only representation. This is used for creating text-only content for models.

This is not used for rendering the message in console. For that, use to_text().

The difference between this and to_model_message() is that this is used to construct parts of the a message for the model client, while to_model_message() is used to create a complete message for the model client.

to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

property type: str
pydantic model TextMessage[source]
Bases: BaseTextChatMessage

A text message with string-only content.

Show JSON schema
Fields
:
type (Literal['TextMessage'])

field type: Literal['TextMessage'] = 'TextMessage'
pydantic model ThoughtEvent[source]
Bases: BaseAgentEvent

An event signaling the thought process of a model. It is used to communicate the reasoning tokens generated by a reasoning model, or the extra text content generated by a function call.

Show JSON schema
Fields
:
content (str)

type (Literal['ThoughtEvent'])

field content: str [Required]
The thought process of the model.

field type: Literal['ThoughtEvent'] = 'ThoughtEvent'
to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model ToolCallExecutionEvent[source]
Bases: BaseAgentEvent

An event signaling the execution of tool calls.

Show JSON schema
Fields
:
content (List[autogen_core.models._types.FunctionExecutionResult])

type (Literal['ToolCallExecutionEvent'])

field content: List[FunctionExecutionResult] [Required]
The tool call results.

field type: Literal['ToolCallExecutionEvent'] = 'ToolCallExecutionEvent'
to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model ToolCallRequestEvent[source]
Bases: BaseAgentEvent

An event signaling a request to use tools.

Show JSON schema
Fields
:
content (List[autogen_core._types.FunctionCall])

type (Literal['ToolCallRequestEvent'])

field content: List[FunctionCall] [Required]
The tool calls.

field type: Literal['ToolCallRequestEvent'] = 'ToolCallRequestEvent'
to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.

pydantic model ToolCallSummaryMessage[source]
Bases: BaseTextChatMessage

A message signaling the summary of tool call results.

Show JSON schema
Fields
:
results (List[autogen_core.models._types.FunctionExecutionResult])

tool_calls (List[autogen_core._types.FunctionCall])

type (Literal['ToolCallSummaryMessage'])

field results: List[FunctionExecutionResult] [Required]
The results of the tool calls.

field tool_calls: List[FunctionCall] [Required]
The tool calls that were made.

field type: Literal['ToolCallSummaryMessage'] = 'ToolCallSummaryMessage'
pydantic model UserInputRequestedEvent[source]
Bases: BaseAgentEvent

An event signaling a that the user proxy has requested user input. Published prior to invoking the input callback.

Show JSON schema
Fields
:
content (Literal[''])

request_id (str)

type (Literal['UserInputRequestedEvent'])

field content: Literal[''] = ''
Empty content for compat with consumers expecting a content field.

field request_id: str [Required]
Identifier for the user input request.

field type: Literal['UserInputRequestedEvent'] = 'UserInputRequestedEvent'
to_text() → str[source]
Convert the message content to a string-only representation that can be rendered in the console and inspected by the user or conditions. This is not used for creating text-only content for models. For BaseChatMessage types, use to_model_text() instead.