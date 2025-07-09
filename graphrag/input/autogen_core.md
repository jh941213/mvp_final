# autogen_core 모듈

`autogen_core` 모듈은 AutoGen 프레임워크의 핵심 구성 요소들을 제공합니다. 에이전트 런타임, 메시지 처리, 구독 시스템, 컴포넌트 관리 등의 기본 기능을 포함합니다.

## 핵심 클래스

### Agent

```python
class Agent(*args, **kwargs)
```

모든 에이전트가 구현해야 하는 기본 프로토콜입니다.

#### 주요 속성
- `metadata: AgentMetadata` - 에이전트의 메타데이터
- `id: AgentId` - 에이전트의 고유 식별자

#### 주요 메서드

**bind_id_and_runtime(id: AgentId, runtime: AgentRuntime)**
- 에이전트 인스턴스를 AgentRuntime에 바인딩합니다.

**on_message(message: Any, ctx: MessageContext)**
- 메시지 핸들러입니다. 런타임에서만 호출되어야 합니다.
- 반환값: 메시지에 대한 응답 (None 가능)
- 예외: `CancelledError`, `CantHandleException`

**save_state() / load_state(state: Mapping[str, Any])**
- 에이전트의 상태를 저장하고 복원합니다.
- 상태는 JSON 직렬화 가능해야 합니다.

### AgentId

```python
class AgentId(type: str | AgentType, key: str)
```

에이전트 런타임 내에서 에이전트 인스턴스를 고유하게 식별하는 ID입니다.

#### 주요 속성
- `type: str` - 에이전트를 특정 팩토리 함수와 연결하는 식별자
- `key: str` - 에이전트 인스턴스 식별자

#### 주요 메서드

**from_str(agent_id: str)**
- "type/key" 형식의 문자열을 AgentId로 변환합니다.

```python
# 예제
agent_id = AgentId.from_str("assistant/user1")
print(agent_id.type)  # "assistant"
print(agent_id.key)   # "user1"
```

### AgentRuntime

```python
class AgentRuntime(*args, **kwargs)
```

에이전트 실행 환경을 관리하는 프로토콜입니다.

#### 주요 메서드

**send_message(message: Any, recipient: AgentId, ...)**
- 에이전트에게 메시지를 보내고 응답을 받습니다.

**publish_message(message: Any, topic_id: TopicId, ...)**
- 특정 토픽의 모든 에이전트에게 메시지를 발행합니다.

**register_factory(type: str, agent_factory: Callable, ...)**
- 에이전트 팩토리를 등록합니다.

```python
# 예제
async def my_agent_factory():
    return MyAgent()

await runtime.register_factory("my_agent", my_agent_factory)
```

**save_state() / load_state(state: Mapping[str, Any])**
- 전체 런타임의 상태를 저장하고 복원합니다.

### BaseAgent

```python
class BaseAgent(description: str)
```

Agent 프로토콜의 추상 기본 구현체입니다.

#### 주요 특징
- `on_message_impl()` 추상 메서드를 구현해야 합니다.
- 메시지 전송, 발행, 상태 관리 기능을 제공합니다.

#### 주요 메서드

**register(runtime: AgentRuntime, type: str, factory: Callable, ...)**
- 에이전트를 런타임에 등록합니다.

**register_instance(runtime: AgentRuntime, agent_id: AgentId, ...)**
- 에이전트 인스턴스를 등록합니다.

```python
# 예제
class MyAgent(BaseAgent):
    async def on_message_impl(self, message: Any, ctx: MessageContext) -> Any:
        # 메시지 처리 로직
        return f"처리됨: {message}"

# 등록
await MyAgent.register(runtime, "my_agent", lambda: MyAgent("설명"))
```

### RoutedAgent

```python
class RoutedAgent(description: str)
```

메시지 타입에 따라 핸들러로 라우팅하는 에이전트 기본 클래스입니다.

#### 주요 특징
- 메서드에 `@message_handler`, `@event`, `@rpc` 데코레이터를 사용합니다.
- 메시지 타입별로 자동 라우팅됩니다.

```python
@dataclass
class MyMessage:
    content: str

class MyAgent(RoutedAgent):
    def __init__(self):
        super().__init__("MyAgent")

    @message_handler
    async def handle_message(self, message: MyMessage, ctx: MessageContext) -> None:
        print(f"받은 메시지: {message.content}")

    @rpc
    async def handle_rpc(self, message: MyMessage, ctx: MessageContext) -> str:
        return f"처리됨: {message.content}"
```

### SingleThreadedAgentRuntime

```python
class SingleThreadedAgentRuntime(*, intervention_handlers=None, tracer_provider=None, ignore_unhandled_exceptions=True)
```

단일 스레드에서 동작하는 에이전트 런타임입니다.

#### 주요 특징
- 개발 및 독립 실행 애플리케이션에 적합
- 메시지를 순서대로 처리
- 높은 처리량이나 동시성이 필요한 시나리오에는 부적합

#### 주요 메서드

**start() / stop() / stop_when_idle()**
- 런타임 시작, 중지, 유휴 상태에서 중지

**process_next()**
- 큐의 다음 메시지를 처리합니다.

```python
# 예제
async def main():
    runtime = SingleThreadedAgentRuntime()
    await MyAgent.register(runtime, "my_agent", lambda: MyAgent("에이전트"))
    
    runtime.start()
    await runtime.send_message(
        MyMessage("안녕하세요"), 
        AgentId("my_agent", "default")
    )
    await runtime.stop_when_idle()
```

## 메시지 및 컨텍스트

### MessageContext

```python
class MessageContext(sender: AgentId | None, topic_id: TopicId | None, is_rpc: bool, cancellation_token: CancellationToken, message_id: str)
```

메시지 처리 시 전달되는 컨텍스트 정보입니다.

#### 주요 속성
- `sender` - 메시지 발신자
- `topic_id` - 토픽 ID (발행된 메시지의 경우)
- `is_rpc` - RPC 메시지 여부
- `cancellation_token` - 취소 토큰
- `message_id` - 메시지 고유 ID

### TopicId

```python
class TopicId(type: str, source: str)
```

브로드캐스트 메시지의 범위를 정의합니다.

#### 주요 속성
- `type` - 이벤트 타입
- `source` - 이벤트가 발생한 컨텍스트

```python
# 예제
topic = TopicId(type="user_action", source="web_interface")
await runtime.publish_message(message, topic)
```

## 구독 시스템

### Subscription

```python
class Subscription(*args, **kwargs)
```

에이전트가 관심 있는 토픽을 정의하는 프로토콜입니다.

#### 주요 메서드

**is_match(topic_id: TopicId) -> bool**
- 주어진 토픽이 구독과 일치하는지 확인

**map_to_agent(topic_id: TopicId) -> AgentId**
- 토픽을 처리할 에이전트로 매핑

### TypeSubscription

```python
class TypeSubscription(topic_type: str, agent_type: str | AgentType, id: str | None = None)
```

토픽 타입 기반 구독입니다.

```python
# 예제
subscription = TypeSubscription(topic_type="user_message", agent_type="chat_agent")
# "user_message" 타입의 토픽을 "chat_agent" 타입 에이전트가 처리
```

### DefaultSubscription

```python
class DefaultSubscription(topic_type: str = 'default', agent_type: str | AgentType | None = None)
```

기본 구독으로, 전역 범위만 필요한 애플리케이션에 적합합니다.

## 데코레이터

### @message_handler

```python
@message_handler(func=None, *, strict=True, match=None)
```

일반적인 메시지 핸들러를 위한 데코레이터입니다.

### @event

```python
@event(func=None, *, strict=True, match=None)
```

이벤트 메시지 핸들러를 위한 데코레이터입니다. 반환값이 None이어야 합니다.

### @rpc

```python
@rpc(func=None, *, strict=True, match=None)
```

RPC 메시지 핸들러를 위한 데코레이터입니다. 응답을 반환할 수 있습니다.

```python
class MyAgent(RoutedAgent):
    @event
    async def handle_event(self, message: EventMessage, ctx: MessageContext) -> None:
        # 이벤트 처리, 응답 없음
        pass

    @rpc
    async def handle_request(self, message: RequestMessage, ctx: MessageContext) -> ResponseMessage:
        # 요청 처리 후 응답 반환
        return ResponseMessage("처리 완료")
```

## 컴포넌트 시스템

### Component

```python
class Component[ConfigT]
```

설정 기반 컴포넌트를 생성하기 위한 기본 클래스입니다.

#### 구현 요구사항
- `component_config_schema` - Pydantic 모델 클래스
- `component_type` - 컴포넌트의 논리적 타입
- `_to_config()` - 설정 덤프 메서드
- `_from_config()` - 설정에서 인스턴스 생성 메서드

```python
from pydantic import BaseModel

class MyConfig(BaseModel):
    value: str

class MyComponent(Component[MyConfig]):
    component_type = "custom"
    component_config_schema = MyConfig

    def __init__(self, value: str):
        self.value = value

    def _to_config(self) -> MyConfig:
        return MyConfig(value=self.value)

    @classmethod
    def _from_config(cls, config: MyConfig) -> 'MyComponent':
        return cls(value=config.value)
```

### CacheStore

```python
class CacheStore[T]
```

저장소/캐시 작업을 위한 기본 인터페이스입니다.

#### 주요 메서드

**get(key: str, default: T | None = None) -> T | None**
- 키로 아이템을 조회합니다.

**set(key: str, value: T) -> None**
- 키-값 쌍을 저장합니다.

### InMemoryStore

```python
class InMemoryStore[T]
```

메모리 내 저장소 구현체입니다.

```python
# 예제
store = InMemoryStore[str]()
store.set("key1", "value1")
value = store.get("key1")  # "value1"
```

## 유틸리티 클래스

### CancellationToken

```python
class CancellationToken()
```

비동기 호출 취소를 위한 토큰입니다.

#### 주요 메서드

**cancel() / is_cancelled()**
- 취소 실행 및 취소 상태 확인

**add_callback(callback: Callable[[], None])**
- 취소 시 호출될 콜백 추가

**link_future(future: Future[Any])**
- Future를 토큰에 연결하여 취소 가능하게 만듭니다.

### AgentInstantiationContext

```python
class AgentInstantiationContext()
```

에이전트 인스턴스화 중 컨텍스트 정보를 제공하는 정적 클래스입니다.

#### 주요 메서드

**current_runtime() -> AgentRuntime**
- 현재 런타임을 반환합니다.

**current_agent_id() -> AgentId**
- 현재 에이전트 ID를 반환합니다.

```python
class TestAgent(RoutedAgent):
    def __init__(self, description: str):
        super().__init__(description)
        # 팩토리나 생성자에서 현재 컨텍스트 접근
        runtime = AgentInstantiationContext.current_runtime()
        agent_id = AgentInstantiationContext.current_agent_id()
```

### Image

```python
class Image(image: PIL.Image.Image)
```

이미지를 나타내는 클래스입니다.

#### 주요 메서드

**from_pil(pil_image) / from_uri(uri) / from_base64(base64_str) / from_file(file_path)**
- 다양한 소스에서 이미지를 생성합니다.

**to_base64() / to_openai_format(detail='auto')**
- 이미지를 다른 형식으로 변환합니다.

```python
# 예제
image = Image.from_file(Path("image.jpg"))
base64_data = image.to_base64()
openai_format = image.to_openai_format(detail="high")
```

## 개입 핸들러

### InterventionHandler

```python
class InterventionHandler(*args, **kwargs)
```

런타임에서 처리되는 메시지를 수정, 로깅 또는 드롭할 수 있는 핸들러입니다.

#### 주요 메서드

**on_send(message, *, message_context, recipient)**
- 메시지 전송 시 호출됩니다.

**on_publish(message, *, message_context)**
- 메시지 발행 시 호출됩니다.

**on_response(message, *, sender, recipient)**
- 응답 수신 시 호출됩니다.

```python
class MyInterventionHandler(DefaultInterventionHandler):
    async def on_send(self, message: Any, *, message_context: MessageContext, recipient: AgentId):
        # 메시지를 대문자로 변환
        if hasattr(message, 'content'):
            message.content = message.content.upper()
        return message

runtime = SingleThreadedAgentRuntime(intervention_handlers=[MyInterventionHandler()])
```

## 추적 및 관찰성

### 추적 함수

**trace_create_agent_span(agent_name, ...)**
- 에이전트 생성 추적 스팬을 생성합니다.

**trace_invoke_agent_span(agent_name, ...)**
- 에이전트 호출 추적 스팬을 생성합니다.

**trace_tool_span(tool_name, ...)**
- 도구 실행 추적 스팬을 생성합니다.

```python
# 예제
with trace_create_agent_span("my_agent", agent_id="agent_001") as span:
    # 에이전트 생성 코드
    agent = MyAgent()
```

## 실용적인 예제

### 기본 에이전트 시스템

```python
import asyncio
from dataclasses import dataclass
from autogen_core import (
    RoutedAgent, SingleThreadedAgentRuntime, AgentId,
    MessageContext, message_handler, DefaultTopicId,
    default_subscription
)

@dataclass
class ChatMessage:
    content: str
    user_id: str

@default_subscription
class ChatAgent(RoutedAgent):
    def __init__(self):
        super().__init__("채팅 에이전트")
        self.message_count = 0

    @message_handler
    async def handle_chat(self, message: ChatMessage, ctx: MessageContext) -> None:
        self.message_count += 1
        print(f"[{message.user_id}] {message.content} (총 {self.message_count}개 메시지)")

async def main():
    runtime = SingleThreadedAgentRuntime()
    await ChatAgent.register(runtime, "chat_agent", lambda: ChatAgent())
    
    runtime.start()
    
    # 메시지 발행
    await runtime.publish_message(
        ChatMessage("안녕하세요!", "user1"), 
        DefaultTopicId()
    )
    
    await runtime.stop_when_idle()

asyncio.run(main())
```

### RPC 스타일 에이전트

```python
@dataclass
class CalculateRequest:
    operation: str
    a: float
    b: float

@dataclass
class CalculateResponse:
    result: float

class CalculatorAgent(RoutedAgent):
    def __init__(self):
        super().__init__("계산기 에이전트")

    @rpc
    async def calculate(self, request: CalculateRequest, ctx: MessageContext) -> CalculateResponse:
        if request.operation == "add":
            result = request.a + request.b
        elif request.operation == "multiply":
            result = request.a * request.b
        else:
            raise ValueError(f"지원하지 않는 연산: {request.operation}")
        
        return CalculateResponse(result=result)

async def main():
    runtime = SingleThreadedAgentRuntime()
    await CalculatorAgent.register(runtime, "calculator", lambda: CalculatorAgent())
    
    runtime.start()
    
    # RPC 호출
    response = await runtime.send_message(
        CalculateRequest("add", 10, 20),
        AgentId("calculator", "default")
    )
    print(f"계산 결과: {response.result}")  # 30
    
    await runtime.stop()
```

### 상태 관리

```python
class StatefulAgent(RoutedAgent):
    def __init__(self):
        super().__init__("상태 관리 에이전트")
        self.counter = 0
        self.messages = []

    async def save_state(self) -> dict:
        return {
            "counter": self.counter,
            "messages": self.messages
        }

    async def load_state(self, state: dict) -> None:
        self.counter = state.get("counter", 0)
        self.messages = state.get("messages", [])

    @message_handler
    async def handle_message(self, message: str, ctx: MessageContext) -> None:
        self.counter += 1
        self.messages.append(message)
        print(f"메시지 #{self.counter}: {message}")

# 상태 저장 및 복원
async def main():
    runtime = SingleThreadedAgentRuntime()
    agent_id = AgentId("stateful", "default")
    
    # 에이전트 등록 및 메시지 처리
    await StatefulAgent.register(runtime, "stateful", lambda: StatefulAgent())
    runtime.start()
    
    await runtime.send_message("첫 번째 메시지", agent_id)
    await runtime.send_message("두 번째 메시지", agent_id)
    
    # 상태 저장
    state = await runtime.agent_save_state(agent_id)
    print(f"저장된 상태: {state}")
    
    # 상태 복원 (새로운 런타임에서)
    new_runtime = SingleThreadedAgentRuntime()
    await StatefulAgent.register(new_runtime, "stateful", lambda: StatefulAgent())
    new_runtime.start()
    
    await new_runtime.agent_load_state(agent_id, state)
    await new_runtime.send_message("복원 후 메시지", agent_id)
    
    await runtime.stop()
    await new_runtime.stop()
```

## 주요 고려사항

### 성능 최적화
- `SingleThreadedAgentRuntime`은 개발용으로 적합
- 프로덕션 환경에서는 분산 런타임 고려
- 메시지 직렬화 오버헤드 최소화

### 오류 처리
- `CantHandleException`으로 처리 불가능한 메시지 표시
- `CancelledError`로 취소된 작업 처리
- 개입 핸들러에서 `DropMessage` 반환으로 메시지 드롭

### 상태 관리
- 모든 상태는 JSON 직렬화 가능해야 함
- 상태 저장/복원 시 버전 호환성 고려
- 대용량 상태의 경우 외부 저장소 사용 검토

### 메시지 라우팅
- 타입 기반 자동 라우팅 활용
- `match` 함수로 세밀한 라우팅 제어
- 구독 시스템으로 이벤트 기반 아키텍처 구현

이 문서는 `autogen_core` 모듈의 핵심 기능들을 다루며, 실제 에이전트 시스템 개발에 필요한 모든 구성 요소를 제공합니다. 