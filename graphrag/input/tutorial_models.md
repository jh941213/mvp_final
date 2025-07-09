# Models

In many cases, agents need access to LLM model services such as OpenAI, Azure OpenAI, or local models. Since there are many different providers with different APIs, autogen-core implements a protocol for model clients and autogen-ext implements a set of model clients for popular model services. AgentChat can use these model clients to interact with model services.

This section provides a quick overview of available model clients. For more details on how to use them directly, please refer to Model Clients in the Core API documentation.

> **Note**: See ChatCompletionCache for a caching wrapper to use with the following clients.

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

## OpenAI

To access OpenAI models, install the openai extension, which allows you to use the `OpenAIChatCompletionClient`.

```bash
pip install "autogen-ext[openai]"
```

You will also need to obtain an API key from OpenAI.

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

openai_model_client = OpenAIChatCompletionClient(
    model="gpt-4o-2024-08-06",
    # api_key="sk-...", # Optional if you have an OPENAI_API_KEY environment variable set.
)
```

To test the model client, you can use the following code:

```python
from autogen_core.models import UserMessage

result = await openai_model_client.create([UserMessage(content="What is the capital of France?", source="user")])
print(result)
await openai_model_client.close()
```

**출력:**
```
CreateResult(finish_reason='stop', content='The capital of France is Paris.', usage=RequestUsage(prompt_tokens=15, completion_tokens=7), cached=False, logprobs=None)
```

> **Note**: You can use this client with models hosted on OpenAI-compatible endpoints, however, we have not tested this functionality. See OpenAIChatCompletionClient for more information.

## Azure OpenAI

Similarly, install the azure and openai extensions to use the `AzureOpenAIChatCompletionClient`.

```bash
pip install "autogen-ext[openai,azure]"
```

To use the client, you need to provide your deployment id, Azure Cognitive Services endpoint, api version, and model capabilities. For authentication, you can either provide an API key or an Azure Active Directory (AAD) token credential.

The following code snippet shows how to use AAD authentication. The identity used must be assigned the Cognitive Services OpenAI User role.

```python
from autogen_core.models import UserMessage
from autogen_ext.auth.azure import AzureTokenProvider
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential

# Create the token provider
token_provider = AzureTokenProvider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",
)

az_model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="{your-azure-deployment}",
    model="{model-name, such as gpt-4o}",
    api_version="2024-06-01",
    azure_endpoint="https://{your-custom-endpoint}.openai.azure.com/",
    azure_ad_token_provider=token_provider,  # Optional if you choose key-based authentication.
    # api_key="sk-...", # For key-based authentication.
)

result = await az_model_client.create([UserMessage(content="What is the capital of France?", source="user")])
print(result)
await az_model_client.close()
```

See [here](./tutorial/models.ipynb#azure-openai) for how to use the Azure client directly or for more information.

## Azure AI Foundry

Azure AI Foundry (previously known as Azure AI Studio) offers models hosted on Azure. To use those models, you use the `AzureAIChatCompletionClient`.

You need to install the azure extra to use this client.

```bash
pip install "autogen-ext[azure]"
```

Below is an example of using this client with the Phi-4 model from GitHub Marketplace.

```python
import os

from autogen_core.models import UserMessage
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential

client = AzureAIChatCompletionClient(
    model="Phi-4",
    endpoint="https://models.inference.ai.azure.com",
    # To authenticate with the model you will need to generate a personal access token (PAT) in your GitHub settings.
    # Create your PAT token by following instructions here: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
    credential=AzureKeyCredential(os.environ["GITHUB_TOKEN"]),
    model_info={
        "json_output": False,
        "function_calling": False,
        "vision": False,
        "family": "unknown",
        "structured_output": False,
    },
)

result = await client.create([UserMessage(content="What is the capital of France?", source="user")])
print(result)
await client.close()
```

**출력:**
```
finish_reason='stop' content='The capital of France is Paris.' usage=RequestUsage(prompt_tokens=14, completion_tokens=8) cached=False logprobs=None
```

## Anthropic (experimental)

To use the `AnthropicChatCompletionClient`, you need to install the anthropic extra. Underneath, it uses the anthropic python sdk to access the models. You will also need to obtain an API key from Anthropic.

```bash
pip install -U "autogen-ext[anthropic]"
```

```python
from autogen_core.models import UserMessage
from autogen_ext.models.anthropic import AnthropicChatCompletionClient

anthropic_client = AnthropicChatCompletionClient(model="claude-3-7-sonnet-20250219")
result = await anthropic_client.create([UserMessage(content="What is the capital of France?", source="user")])
print(result)
await anthropic_client.close()
```

**출력:**
```
finish_reason='stop' content="The capital of France is Paris. It's not only the political and administrative capital but also a major global center for art, fashion, gastronomy, and culture. Paris is known for landmarks such as the Eiffel Tower, the Louvre Museum, Notre-Dame Cathedral, and the Champs-Élysées." usage=RequestUsage(prompt_tokens=14, completion_tokens=73) cached=False logprobs=None thought=None
```

## Ollama (experimental)

Ollama is a local model server that can run models locally on your machine.

> **Note**: Small local models are typically not as capable as larger models on the cloud. For some tasks they may not perform as well and the output may be surprising.

To use Ollama, install the ollama extension and use the `OllamaChatCompletionClient`.

```bash
pip install -U "autogen-ext[ollama]"
```

```python
from autogen_core.models import UserMessage
from autogen_ext.models.ollama import OllamaChatCompletionClient

# Assuming your Ollama server is running locally on port 11434.
ollama_model_client = OllamaChatCompletionClient(model="llama3.2")

response = await ollama_model_client.create([UserMessage(content="What is the capital of France?", source="user")])
print(response)
await ollama_model_client.close()
```

**출력:**
```
finish_reason='unknown' content='The capital of France is Paris.' usage=RequestUsage(prompt_tokens=32, completion_tokens=8) cached=False logprobs=None thought=None
```

## Gemini (experimental)

Gemini currently offers an OpenAI-compatible API (beta). So you can use the `OpenAIChatCompletionClient` with the Gemini API.

> **Note**: While some model providers may offer OpenAI-compatible APIs, they may still have minor differences. For example, the finish_reason field may be different in the response.

```python
from autogen_core.models import UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    # api_key="GEMINI_API_KEY",
)

response = await model_client.create([UserMessage(content="What is the capital of France?", source="user")])
print(response)
await model_client.close()
```

**출력:**
```
finish_reason='stop' content='Paris\n' usage=RequestUsage(prompt_tokens=7, completion_tokens=2) cached=False logprobs=None thought=None
```

Also, as Gemini adds new models, you may need to define the models capabilities via the `model_info` field. For example, to use `gemini-2.0-flash-lite` or a similar new model:

```python
from autogen_core.models import UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo

model_client = OpenAIChatCompletionClient(
    model="gemini-2.0-flash-lite",
    model_info=ModelInfo(vision=True, function_calling=True, json_output=True, family="unknown", structured_output=True)
    # api_key="GEMINI_API_KEY",
)

response = await model_client.create([UserMessage(content="What is the capital of France?", source="user")])
print(response)
await model_client.close()
```

## Llama API (experimental)

Llama API is the Meta's first party API offering. It currently offers an OpenAI compatible endpoint. So you can use the `OpenAIChatCompletionClient` with the Llama API.

This endpoint fully supports the following OpenAI client library features:
- Chat completions
- Model selection
- Temperature/sampling
- Streaming
- Image understanding
- Structured output (JSON mode)
- Function calling (tools)

```python
from pathlib import Path

from autogen_core import Image
from autogen_core.models import UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Text
model_client = OpenAIChatCompletionClient(
    model="Llama-4-Scout-17B-16E-Instruct-FP8",
    # api_key="LLAMA_API_KEY"
)

response = await model_client.create([UserMessage(content="Write me a poem", source="user")])
print(response)
await model_client.close()

# Image
model_client = OpenAIChatCompletionClient(
    model="Llama-4-Maverick-17B-128E-Instruct-FP8",
    # api_key="LLAMA_API_KEY"
)
image = Image.from_file(Path("test.png"))

response = await model_client.create([UserMessage(content=["What is in this image", image], source="user")])
print(response)
await model_client.close()
```

## Semantic Kernel Adapter

The `SKChatCompletionAdapter` allows you to use Semantic kernel model clients as a `ChatCompletionClient` by adapting them to the required interface.

You need to install the relevant provider extras to use this adapter.

The list of extras that can be installed:
- `semantic-kernel-anthropic`: Install this extra to use Anthropic models.
- `semantic-kernel-google`: Install this extra to use Google Gemini models.
- `semantic-kernel-ollama`: Install this extra to use Ollama models.
- `semantic-kernel-mistralai`: Install this extra to use MistralAI models.
- `semantic-kernel-aws`: Install this extra to use AWS models.
- `semantic-kernel-hugging-face`: Install this extra to use Hugging Face models.

For example, to use Anthropic models, you need to install `semantic-kernel-anthropic`.

```bash
pip install "autogen-ext[semantic-kernel-anthropic]"
```

To use this adapter, you need create a Semantic Kernel model client and pass it to the adapter.

For example, to use the Anthropic model:

```python
import os

from autogen_core.models import UserMessage
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.anthropic import AnthropicChatCompletion, AnthropicChatPromptExecutionSettings
from semantic_kernel.memory.null_memory import NullMemory

sk_client = AnthropicChatCompletion(
    ai_model_id="claude-3-5-sonnet-20241022",
    api_key=os.environ["ANTHROPIC_API_KEY"],
    service_id="my-service-id",  # Optional; for targeting specific services within Semantic Kernel
)
settings = AnthropicChatPromptExecutionSettings(
    temperature=0.2,
)

anthropic_model_client = SKChatCompletionAdapter(
    sk_client, kernel=Kernel(memory=NullMemory()), prompt_settings=settings
)

# Call the model directly.
model_result = await anthropic_model_client.create(
    messages=[UserMessage(content="What is the capital of France?", source="User")]
)
print(model_result)
await anthropic_model_client.close()
```

**출력:**
```
finish_reason='stop' content='The capital of France is Paris. It is also the largest city in France and one of the most populous metropolitan areas in Europe.' usage=RequestUsage(prompt_tokens=0, completion_tokens=0) cached=False logprobs=None
```

Read more about the [Semantic Kernel Adapter](./semantic-kernel-adapter).