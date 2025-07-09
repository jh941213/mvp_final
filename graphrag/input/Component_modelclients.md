# Model Clients

AutoGen provides a suite of built-in model clients for using ChatCompletion API. All model clients implement the ChatCompletionClient protocol class.

Currently we support the following built-in model clients:

- **OpenAIChatCompletionClient**: for OpenAI models and models with OpenAI API compatibility (e.g., Gemini).
- **AzureOpenAIChatCompletionClient**: for Azure OpenAI models.
- **AzureAIChatCompletionClient**: for GitHub models and models hosted on Azure.
- **OllamaChatCompletionClient** (Experimental): for local models hosted on Ollama.
- **AnthropicChatCompletionClient** (Experimental): for models hosted on Anthropic.
- **SKChatCompletionAdapter**: adapter for Semantic Kernel AI connectors.

For more information on how to use these model clients, please refer to the documentation of each client.

## Log Model Calls

AutoGen uses standard Python logging module to log events like model calls and responses. The logger name is `autogen_core.EVENT_LOGGER_NAME`, and the event type is `LLMCall`.

```python
import logging

from autogen_core import EVENT_LOGGER_NAME

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(EVENT_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
```

## Call Model Client

To call a model client, you can use the `create()` method. This example uses the OpenAIChatCompletionClient to call an OpenAI model.

```python
from autogen_core.models import UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(
    model="gpt-4", temperature=0.3
)  # assuming OPENAI_API_KEY is set in the environment.

result = await model_client.create([UserMessage(content="What is the capital of France?", source="user")])
print(result)
```

```
finish_reason='stop' content='The capital of France is Paris.' usage=RequestUsage(prompt_tokens=15, completion_tokens=8) cached=False logprobs=None thought=None
```

## Streaming Tokens

You can use the `create_stream()` method to create a chat completion request with streaming token chunks.

```python
from autogen_core.models import CreateResult, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(model="gpt-4o")  # assuming OPENAI_API_KEY is set in the environment.

messages = [
    UserMessage(content="Write a very short story about a dragon.", source="user"),
]

# Create a stream.
stream = model_client.create_stream(messages=messages)

# Iterate over the stream and print the responses.
print("Streamed responses:")
async for chunk in stream:  # type: ignore
    if isinstance(chunk, str):
        # The chunk is a string.
        print(chunk, flush=True, end="")
    else:
        # The final chunk is a CreateResult object.
        assert isinstance(chunk, CreateResult) and isinstance(chunk.content, str)
        # The last response is a CreateResult object with the complete message.
        print("\n\n------------\n")
        print("The complete response:", flush=True)
        print(chunk.content, flush=True)
```

**Streamed responses:**
```
In the heart of an ancient forest, beneath the shadow of snow-capped peaks, a dragon named Elara lived secretly for centuries. Elara was unlike any dragon from the old tales; her scales shimmered with a deep emerald hue, each scale engraved with symbols of lost wisdom. The villagers in the nearby valley spoke of mysterious lights dancing across the night sky, but none dared venture close enough to solve the enigma.

One cold winter's eve, a young girl named Lira, brimming with curiosity and armed with the innocence of youth, wandered into Elara's domain. Instead of fire and fury, she found warmth and a gentle gaze. The dragon shared stories of a world long forgotten and in return, Lira gifted her simple stories of human life, rich in laughter and scent of earth.

From that night on, the villagers noticed subtle changes—the crops grew taller, and the air seemed sweeter. Elara had infused the valley with ancient magic, a guardian of balance, watching quietly as her new friend thrived under the stars. And so, Lira and Elara's bond marked the beginning of a timeless friendship that spun tales of hope whispered through the leaves of the ever-verdant forest.

------------

The complete response:
In the heart of an ancient forest, beneath the shadow of snow-capped peaks, a dragon named Elara lived secretly for centuries. Elara was unlike any dragon from the old tales; her scales shimmered with a deep emerald hue, each scale engraved with symbols of lost wisdom. The villagers in the nearby valley spoke of mysterious lights dancing across the night sky, but none dared venture close enough to solve the enigma.

One cold winter's eve, a young girl named Lira, brimming with curiosity and armed with the innocence of youth, wandered into Elara's domain. Instead of fire and fury, she found warmth and a gentle gaze. The dragon shared stories of a world long forgotten and in return, Lira gifted her simple stories of human life, rich in laughter and scent of earth.

From that night on, the villagers noticed subtle changes—the crops grew taller, and the air seemed sweeter. Elara had infused the valley with ancient magic, a guardian of balance, watching quietly as her new friend thrived under the stars. And so, Lira and Elara's bond marked the beginning of a timeless friendship that spun tales of hope whispered through the leaves of the ever-verdant forest.

------------

The token usage was:
RequestUsage(prompt_tokens=0, completion_tokens=0)
```

> **Note**: The last response in the streaming response is always the final response of the type `CreateResult`.

> **Note**: The default usage response is to return zero values. To enable usage, see `create_stream()` for more details.

## Structured Output

Structured output can be enabled by setting the `response_format` field in `OpenAIChatCompletionClient` and `AzureOpenAIChatCompletionClient` to as a Pydantic BaseModel class.

> **Note**: Structured output is only available for models that support it. It also requires the model client to support structured output as well. Currently, the `OpenAIChatCompletionClient` and `AzureOpenAIChatCompletionClient` support structured output.

```python
from typing import Literal

from pydantic import BaseModel


# The response format for the agent as a Pydantic base model.
class AgentResponse(BaseModel):
    thoughts: str
    response: Literal["happy", "sad", "neutral"]


# Create an agent that uses the OpenAI GPT-4o model with the custom response format.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    response_format=AgentResponse,  # type: ignore
)

# Send a message list to the model and await the response.
messages = [
    UserMessage(content="I am happy.", source="user"),
]
response = await model_client.create(messages=messages)
assert isinstance(response.content, str)
parsed_response = AgentResponse.model_validate_json(response.content)
print(parsed_response.thoughts)
print(parsed_response.response)

# Close the connection to the model client.
await model_client.close()
```

```
I'm glad to hear that you're feeling happy! It's such a great emotion that can brighten your whole day. Is there anything in particular that's bringing you joy today? 😊
happy
```

You also use the `extra_create_args` parameter in the `create()` method to set the `response_format` field so that the structured output can be configured for each request.

## Caching Model Responses

`autogen_ext` implements `ChatCompletionCache` that can wrap any `ChatCompletionClient`. Using this wrapper avoids incurring token usage when querying the underlying client with the same prompt multiple times.

`ChatCompletionCache` uses a `CacheStore` protocol. We have implemented some useful variants of `CacheStore` including `DiskCacheStore` and `RedisStore`.

Here's an example of using diskcache for local caching:

```python
# pip install -U "autogen-ext[openai, diskcache]"
import asyncio
import tempfile

from autogen_core.models import UserMessage
from autogen_ext.cache_store.diskcache import DiskCacheStore
from autogen_ext.models.cache import CHAT_CACHE_VALUE_TYPE, ChatCompletionCache
from autogen_ext.models.openai import OpenAIChatCompletionClient
from diskcache import Cache


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Initialize the original client
        openai_model_client = OpenAIChatCompletionClient(model="gpt-4o")

        # Then initialize the CacheStore, in this case with diskcache.Cache.
        # You can also use redis like:
        # from autogen_ext.cache_store.redis import RedisStore
        # import redis
        # redis_instance = redis.Redis()
        # cache_store = RedisCacheStore[CHAT_CACHE_VALUE_TYPE](redis_instance)
        cache_store = DiskCacheStore[CHAT_CACHE_VALUE_TYPE](Cache(tmpdirname))
        cache_client = ChatCompletionCache(openai_model_client, cache_store)

        response = await cache_client.create([UserMessage(content="Hello, how are you?", source="user")])
        print(response)  # Should print response from OpenAI
        response = await cache_client.create([UserMessage(content="Hello, how are you?", source="user")])
        print(response)  # Should print cached response

        await openai_model_client.close()
        await cache_client.close()


asyncio.run(main())
```

```
True
```

Inspecting `cached_client.total_usage()` (or `model_client.total_usage()`) before and after a cached response should yield idential counts.

Note that the caching is sensitive to the exact arguments provided to `cached_client.create` or `cached_client.create_stream`, so changing tools or json_output arguments might lead to a cache miss.

## Build an Agent with a Model Client

Let's create a simple AI agent that can respond to messages using the ChatCompletion API.

```python
from dataclasses import dataclass

from autogen_core import MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient


@dataclass
class Message:
    content: str


class SimpleAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A simple agent")
        self._system_messages = [SystemMessage(content="You are a helpful AI assistant.")]
        self._model_client = model_client

    @message_handler
    async def handle_user_message(self, message: Message, ctx: MessageContext) -> Message:
        # Prepare input to the chat completion model.
        user_message = UserMessage(content=message.content, source="user")
        response = await self._model_client.create(
            self._system_messages + [user_message], cancellation_token=ctx.cancellation_token
        )
        # Return with the model's response.
        assert isinstance(response.content, str)
        return Message(content=response.content)
```

The `SimpleAgent` class is a subclass of the `autogen_core.RoutedAgent` class for the convenience of automatically routing messages to the appropriate handlers. It has a single handler, `handle_user_message`, which handles message from the user. It uses the `ChatCompletionClient` to generate a response to the message. It then returns the response to the user, following the direct communication model.

> **Note**: The `cancellation_token` of the type `autogen_core.CancellationToken` is used to cancel asynchronous operations. It is linked to async calls inside the message handlers and can be used by the caller to cancel the handlers.

```python
# Create the runtime and register the agent.
from autogen_core import AgentId

model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    # api_key="sk-...", # Optional if you have an OPENAI_API_KEY set in the environment.
)

runtime = SingleThreadedAgentRuntime()
await SimpleAgent.register(
    runtime,
    "simple_agent",
    lambda: SimpleAgent(model_client=model_client),
)
# Start the runtime processing messages.
runtime.start()
# Send a message to the agent and get the response.
message = Message("Hello, what are some fun things to do in Seattle?")
response = await runtime.send_message(message, AgentId("simple_agent", "default"))
print(response.content)
# Stop the runtime processing messages.
await runtime.stop()
await model_client.close()
```

```
Seattle is a vibrant city with a wide range of activities and attractions. Here are some fun things to do in Seattle:

1. **Space Needle**: Visit this iconic observation tower for stunning views of the city and surrounding mountains.

2. **Pike Place Market**: Explore this historic market where you can see the famous fish toss, buy local produce, and find unique crafts and eateries.

3. **Museum of Pop Culture (MoPOP)**: Dive into the world of contemporary culture, music, and science fiction at this interactive museum.

4. **Chihuly Garden and Glass**: Marvel at the beautiful glass art installations by artist Dale Chihuly, located right next to the Space Needle.

5. **Seattle Aquarium**: Discover the diverse marine life of the Pacific Northwest at this engaging aquarium.

6. **Seattle Art Museum**: Explore a vast collection of art from around the world, including contemporary and indigenous art.

7. **Kerry Park**: For one of the best views of the Seattle skyline, head to this small park on Queen Anne Hill.

8. **Ballard Locks**: Watch boats pass through the locks and observe the salmon ladder to see salmon migrating.

9. **Ferry to Bainbridge Island**: Take a scenic ferry ride across Puget Sound to enjoy charming shops, restaurants, and beautiful natural scenery.

10. **Olympic Sculpture Park**: Stroll through this outdoor park with large-scale sculptures and stunning views of the waterfront and mountains.

11. **Underground Tour**: Discover Seattle's history on this quirky tour of the city's underground passageways in Pioneer Square.

12. **Seattle Waterfront**: Enjoy the shops, restaurants, and attractions along the waterfront, including the Seattle Great Wheel and the aquarium.

13. **Discovery Park**: Explore the largest green space in Seattle, featuring trails, beaches, and views of Puget Sound.

14. **Food Tours**: Try out Seattle's diverse culinary scene, including fresh seafood, international cuisines, and coffee culture (don't miss the original Starbucks!).

15. **Attend a Sports Game**: Catch a Seahawks (NFL), Mariners (MLB), or Sounders (MLS) game for a lively local experience.

Whether you're interested in culture, nature, food, or history, Seattle has something for everyone to enjoy!
```

The above `SimpleAgent` always responds with a fresh context that contains only the system message and the latest user's message. We can use model context classes from `autogen_core.model_context` to make the agent "remember" previous conversations. See the Model Context page for more details.

## API Keys From Environment Variables

In the examples above, we show that you can provide the API key through the `api_key` argument. Importantly, the OpenAI and Azure OpenAI clients use the `openai` package, which will automatically read an api key from the environment variable if one is not provided.

- For OpenAI, you can set the `OPENAI_API_KEY` environment variable.
- For Azure OpenAI, you can set the `AZURE_OPENAI_API_KEY` environment variable.
- In addition, for Gemini (Beta), you can set the `GEMINI_API_KEY` environment variable.

This is a good practice to explore, as it avoids including sensitive api keys in your code.

---
