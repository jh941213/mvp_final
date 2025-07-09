# Memory and RAG

There are several use cases where it is valuable to maintain a store of useful facts that can be intelligently added to the context of the agent just before a specific step. The typically use case here is a RAG pattern where a query is used to retrieve relevant information from a database that is then added to the agent's context.

AgentChat provides a **Memory protocol** that can be extended to provide this functionality. The key methods are `query`, `update_context`, `add`, `clear`, and `close`.

- **add**: add new entries to the memory store
- **query**: retrieve relevant information from the memory store
- **update_context**: mutate an agent's internal `model_context` by adding the retrieved information (used in the AssistantAgent class)
- **clear**: clear all entries from the memory store
- **close**: clean up any resources used by the memory store

## ListMemory Example

`ListMemory` is provided as an example implementation of the Memory protocol. It is a simple list-based memory implementation that maintains memories in chronological order, appending the most recent memories to the model's context. The implementation is designed to be straightforward and predictable, making it easy to understand and debug. In the following example, we will use `ListMemory` to maintain a memory bank of user preferences and demonstrate how it can be used to provide consistent context for agent responses over time.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Initialize user memory
user_memory = ListMemory()

# Add user preferences to memory
await user_memory.add(MemoryContent(content="The weather should be in metric units", mime_type=MemoryMimeType.TEXT))

await user_memory.add(MemoryContent(content="Meal recipe must be vegan", mime_type=MemoryMimeType.TEXT))


async def get_weather(city: str, units: str = "imperial") -> str:
    if units == "imperial":
        return f"The weather in {city} is 73 °F and Sunny."
    elif units == "metric":
        return f"The weather in {city} is 23 °C and Sunny."
    else:
        return f"Sorry, I don't know the weather in {city}."


assistant_agent = AssistantAgent(
    name="assistant_agent",
    model_client=OpenAIChatCompletionClient(
        model="gpt-4o-2024-08-06",
    ),
    tools=[get_weather],
    memory=[user_memory],
)

# Run the agent with a task.
stream = assistant_agent.run_stream(task="What is the weather in New York?")
await Console(stream)
```

We can inspect that the `assistant_agent` `model_context` is actually updated with the retrieved memory entries. The transform method is used to format the retrieved memory entries into a string that can be used by the agent. In this case, we simply concatenate the content of each memory entry into a single string.

```python
await assistant_agent._model_context.get_messages()
```

We see above that the weather is returned in Centigrade as stated in the user preferences.

Similarly, assuming we ask a separate question about generating a meal plan, the agent is able to retrieve relevant information from the memory store and provide a personalized (vegan) response.

```python
stream = assistant_agent.run_stream(task="Write brief meal recipe with broth")
await Console(stream)
```

## Custom Memory Stores (Vector DBs, etc.)

You can build on the Memory protocol to implement more complex memory stores. For example, you could implement a custom memory store that uses a vector database to store and retrieve information, or a memory store that uses a machine learning model to generate personalized responses based on the user's preferences etc.

Specifically, you will need to overload the `add`, `query` and `update_context` methods to implement the desired functionality and pass the memory store to your agent.

Currently the following example memory stores are available as part of the `autogen_ext` extensions package.

- `autogen_ext.memory.chromadb.ChromaDBVectorMemory`: A memory store that uses a vector database to store and retrieve information.
- `autogen_ext.memory.chromadb.SentenceTransformerEmbeddingFunctionConfig`: A configuration class for the SentenceTransformer embedding function used by the ChromaDBVectorMemory store. Note that other embedding functions such as `autogen_ext.memory.openai.OpenAIEmbeddingFunctionConfig` can also be used with the ChromaDBVectorMemory store.

```python
import tempfile

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_ext.memory.chromadb import (
    ChromaDBVectorMemory,
    PersistentChromaDBVectorMemoryConfig,
    SentenceTransformerEmbeddingFunctionConfig,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Use a temporary directory for ChromaDB persistence
with tempfile.TemporaryDirectory() as tmpdir:
    chroma_user_memory = ChromaDBVectorMemory(
        config=PersistentChromaDBVectorMemoryConfig(
            collection_name="preferences",
            persistence_path=tmpdir,  # Use the temp directory here
            k=2,  # Return top k results
            score_threshold=0.4,  # Minimum similarity score
            embedding_function_config=SentenceTransformerEmbeddingFunctionConfig(
                model_name="all-MiniLM-L6-v2"  # Use default model for testing
            ),
        )
    )
    # Add user preferences to memory
    await chroma_user_memory.add(
        MemoryContent(
            content="The weather should be in metric units",
            mime_type=MemoryMimeType.TEXT,
            metadata={"category": "preferences", "type": "units"},
        )
    )

    await chroma_user_memory.add(
        MemoryContent(
            content="Meal recipe must be vegan",
            mime_type=MemoryMimeType.TEXT,
            metadata={"category": "preferences", "type": "dietary"},
        )
    )

    model_client = OpenAIChatCompletionClient(
        model="gpt-4o",
    )

    # Create assistant agent with ChromaDB memory
    assistant_agent = AssistantAgent(
        name="assistant_agent",
        model_client=model_client,
        tools=[get_weather],
        memory=[chroma_user_memory],
    )

    stream = assistant_agent.run_stream(task="What is the weather in New York?")
    await Console(stream)

    await model_client.close()
    await chroma_user_memory.close()
```

Note that you can also serialize the ChromaDBVectorMemory and save it to disk.

```python
chroma_user_memory.dump_component().model_dump_json()
```

## RAG Agent: Putting It All Together

The RAG (Retrieval Augmented Generation) pattern which is common in building AI systems encompasses two distinct phases:

1. **Indexing**: Loading documents, chunking them, and storing them in a vector database
2. **Retrieval**: Finding and using relevant chunks during conversation runtime

In our previous examples, we manually added items to memory and passed them to our agents. In practice, the indexing process is usually automated and based on much larger document sources like product documentation, internal files, or knowledge bases.

> **Note**: The quality of a RAG system is dependent on the quality of the chunking and retrieval process (models, embeddings, etc.). You may need to experiment with more advanced chunking and retrieval models to get the best results.

### Building a Simple RAG Agent

To begin, let's create a simple document indexer that we will used to load documents, chunk them, and store them in a ChromaDBVectorMemory memory store.

```python
import re
from typing import List

import aiofiles
import aiohttp
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType


class SimpleDocumentIndexer:
    """Basic document indexer for AutoGen Memory."""

    def __init__(self, memory: Memory, chunk_size: int = 1500) -> None:
        self.memory = memory
        self.chunk_size = chunk_size

    async def _fetch_content(self, source: str) -> str:
        """Fetch content from URL or file."""
        if source.startswith(("http://", "https://")):
            async with aiohttp.ClientSession() as session:
                async with session.get(source) as response:
                    return await response.text()
        else:
            async with aiofiles.open(source, "r", encoding="utf-8") as f:
                return await f.read()

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags and normalize whitespace."""
        text = re.sub(r"<[^>]*>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _split_text(self, text: str) -> List[str]:
        """Split text into fixed-size chunks."""
        chunks: list[str] = []
        # Just split text into fixed-size chunks
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i : i + self.chunk_size]
            chunks.append(chunk.strip())
        return chunks

    async def index_documents(self, sources: List[str]) -> int:
        """Index documents into memory."""
        total_chunks = 0

        for source in sources:
            try:
                content = await self._fetch_content(source)

                # Strip HTML if content appears to be HTML
                if "<" in content and ">" in content:
                    content = self._strip_html(content)

                chunks = self._split_text(content)

                for i, chunk in enumerate(chunks):
                    await self.memory.add(
                        MemoryContent(
                            content=chunk, mime_type=MemoryMimeType.TEXT, metadata={"source": source, "chunk_index": i}
                        )
                    )

                total_chunks += len(chunks)

            except Exception as e:
                print(f"Error indexing {source}: {str(e)}")

        return total_chunks
```

Now let's use our indexer with ChromaDBVectorMemory to build a complete RAG agent:

```python
import os
from pathlib import Path

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.memory.chromadb import ChromaDBVectorMemory, PersistentChromaDBVectorMemoryConfig
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Initialize vector memory
rag_memory = ChromaDBVectorMemory(
    config=PersistentChromaDBVectorMemoryConfig(
        collection_name="autogen_docs",
        persistence_path=os.path.join(str(Path.home()), ".chromadb_autogen"),
        k=3,  # Return top 3 results
        score_threshold=0.4,  # Minimum similarity score
    )
)

await rag_memory.clear()  # Clear existing memory


# Index AutoGen documentation
async def index_autogen_docs() -> None:
    indexer = SimpleDocumentIndexer(memory=rag_memory)
    sources = [
        "https://raw.githubusercontent.com/microsoft/autogen/main/README.md",
        "https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/tutorial/agents.html",
        "https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/tutorial/teams.html",
        "https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/tutorial/termination.html",
    ]
    chunks: int = await indexer.index_documents(sources)
    print(f"Indexed {chunks} chunks from {len(sources)} AutoGen documents")


await index_autogen_docs()


# Create our RAG assistant agent
rag_assistant = AssistantAgent(
    name="rag_assistant", model_client=OpenAIChatCompletionClient(model="gpt-4o"), memory=[rag_memory]
)

# Ask questions about AutoGen
stream = rag_assistant.run_stream(task="What is AgentChat?")
await Console(stream)

# Remember to close the memory when done
await rag_memory.close()
```

This implementation provides a RAG agent that can answer questions based on AutoGen documentation. When a question is asked, the Memory system retrieves relevant chunks and adds them to the context, enabling the assistant to generate informed responses.

For production systems, you might want to:

- Implement more sophisticated chunking strategies
- Add metadata filtering capabilities
- Customize the retrieval scoring
- Optimize embedding models for your specific domain

## Mem0Memory Example

`autogen_ext.memory.mem0.Mem0Memory` provides integration with Mem0.ai's memory system. It supports both cloud-based and local backends, offering advanced memory capabilities for agents. The implementation handles proper retrieval and context updating, making it suitable for production environments.

In the following example, we'll demonstrate how to use Mem0Memory to maintain persistent memories across conversations:

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_ext.memory.mem0 import Mem0Memory
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Initialize Mem0 cloud memory (requires API key)
# For local deployment, use is_cloud=False with appropriate config
mem0_memory = Mem0Memory(
    is_cloud=True,
    limit=5,  # Maximum number of memories to retrieve
)

# Add user preferences to memory
await mem0_memory.add(
    MemoryContent(
        content="The weather should be in metric units",
        mime_type=MemoryMimeType.TEXT,
        metadata={"category": "preferences", "type": "units"},
    )
)

await mem0_memory.add(
    MemoryContent(
        content="Meal recipe must be vegan",
        mime_type=MemoryMimeType.TEXT,
        metadata={"category": "preferences", "type": "dietary"},
    )
)

# Create assistant with mem0 memory
assistant_agent = AssistantAgent(
    name="assistant_agent",
    model_client=OpenAIChatCompletionClient(
        model="gpt-4o-2024-08-06",
    ),
    tools=[get_weather],
    memory=[mem0_memory],
)

# Ask about the weather
stream = assistant_agent.run_stream(task="What are my dietary preferences?")
await Console(stream)
```

The example above demonstrates how Mem0Memory can be used with an assistant agent. The memory integration ensures that:

- All agent interactions are stored in Mem0 for future reference
- Relevant memories (like user preferences) are automatically retrieved and added to the context
- The agent can maintain consistent behavior based on stored memories

Mem0Memory is particularly useful for:

- Long-running agent deployments that need persistent memory
- Applications requiring enhanced privacy controls
- Teams wanting unified memory management across agents
- Use cases needing advanced memory filtering and analytics

Just like ChromaDBVectorMemory, you can serialize Mem0Memory configurations:

```python
# Serialize the memory configuration
config_json = mem0_memory.dump_component().model_dump_json()
print(f"Memory config JSON: {config_json[:100]}...")
```

---

**On this page:**
- Memory and RAG
- ListMemory Example
- Custom Memory Stores (Vector DBs, etc.)
- RAG Agent: Putting It All Together
- Building a Simple RAG Agent
- Mem0Memory Example

