# autogen_core.logging 모듈

## 열거형 타입

### MessageKind

```python
class MessageKind(Enum)
```

- `DIRECT = 1`
- `PUBLISH = 2`
- `RESPOND = 3`

### DeliveryStage

```python
class DeliveryStage(Enum)
```

- `SEND = 1`
- `DELIVER = 2`

## 이벤트 클래스들

### LLMCallEvent

```python
class LLMCallEvent(*, messages: List[Dict[str, Any]], response: Dict[str, Any], prompt_tokens: int, completion_tokens: int, **kwargs: Any)
```

**속성:**
- `prompt_tokens: int`
- `completion_tokens: int`

### LLMStreamStartEvent

```python
class LLMStreamStartEvent(*, messages: List[Dict[str, Any]], **kwargs: Any)
```

모델 클라이언트가 스트림 시작을 로깅하는 데 사용됩니다.

**매개변수:**
- `messages (List[Dict[str, Any]])` - 호출에 사용된 메시지들. JSON 직렬화 가능해야 합니다.

**예제:**
```python
import logging
from autogen_core import EVENT_LOGGER_NAME
from autogen_core.logging import LLMStreamStartEvent

messages = [{"role": "user", "content": "Hello, world!"}]
logger = logging.getLogger(EVENT_LOGGER_NAME)
logger.info(LLMStreamStartEvent(messages=messages))
```

### LLMStreamEndEvent

```python
class LLMStreamEndEvent(*, response: Dict[str, Any], prompt_tokens: int, completion_tokens: int, **kwargs: Any)
```

**속성:**
- `prompt_tokens: int`
- `completion_tokens: int`

### MessageEvent

```python
class MessageEvent(*, payload: str, sender: AgentId | None, receiver: AgentId | TopicId | None, kind: MessageKind, delivery_stage: DeliveryStage, **kwargs: Any)
```

### MessageDroppedEvent

```python
class MessageDroppedEvent(*, payload: str, sender: AgentId | None, receiver: AgentId | TopicId | None, kind: MessageKind, **kwargs: Any)
```

### MessageHandlerExceptionEvent

```python
class MessageHandlerExceptionEvent(*, payload: str, handling_agent: AgentId, exception: BaseException, **kwargs: Any)
```

### AgentConstructionExceptionEvent

```python
class AgentConstructionExceptionEvent(*, agent_id: AgentId, exception: BaseException, **kwargs: Any)
```

### ToolCallEvent

```python
class ToolCallEvent(*, tool_name: str, arguments: Dict[str, Any], result: str)
``` 