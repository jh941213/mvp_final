# autogen_core.model_context 모듈

`autogen_core.model_context` 모듈은 채팅 완성 컨텍스트 관리를 위한 다양한 전략과 구현체를 제공합니다. 에이전트가 LLM 메시지를 저장하고 검색할 수 있도록 하며, 다양한 회상 전략을 지원합니다.

## 기본 클래스

### ChatCompletionContext

```python
class ChatCompletionContext(initial_messages: List[LLMMessage] | None = None)
```

채팅 완성 컨텍스트의 인터페이스를 정의하는 추상 기본 클래스입니다. 에이전트가 LLM 메시지를 저장하고 검색할 수 있도록 하며, 다양한 회상 전략으로 구현할 수 있습니다.

#### 주요 매개변수
- `initial_messages: List[LLMMessage] | None` - 초기 메시지 목록

#### 주요 메서드

**add_message(message: LLMMessage)**
- 컨텍스트에 메시지를 추가합니다.

**get_messages() -> List[LLMMessage]**
- 컨텍스트에서 메시지를 검색합니다. (추상 메서드)

**clear()**
- 컨텍스트를 지웁니다.

**save_state() / load_state(state: Mapping[str, Any])**
- 컨텍스트 상태를 저장하고 복원합니다.

#### 커스텀 컨텍스트 예제

```python
from typing import List
from autogen_core.model_context import UnboundedChatCompletionContext
from autogen_core.models import AssistantMessage, LLMMessage

class ReasoningModelContext(UnboundedChatCompletionContext):
    """추론 모델용 컨텍스트 - thought 필드를 필터링합니다."""

    async def get_messages(self) -> List[LLMMessage]:
        messages = await super().get_messages()
        # AssistantMessage에서 thought 필드 제거
        messages_out: List[LLMMessage] = []
        for message in messages:
            if isinstance(message, AssistantMessage):
                message.thought = None
            messages_out.append(message)
        return messages_out
```

## 구현체들

### UnboundedChatCompletionContext

```python
class UnboundedChatCompletionContext(initial_messages: List[LLMMessage] | None = None)
```

모든 메시지를 보관하는 무제한 채팅 완성 컨텍스트입니다.

#### 특징
- 모든 메시지를 메모리에 유지
- 메시지 수에 제한이 없음
- 단순하고 직관적인 구현

```python
# 기본 사용법
from autogen_core.model_context import UnboundedChatCompletionContext
from autogen_core.models import SystemMessage, UserMessage

context = UnboundedChatCompletionContext()

# 메시지 추가
await context.add_message(SystemMessage(content="당신은 도움이 되는 어시스턴트입니다."))
await context.add_message(UserMessage(content="안녕하세요!", source="user"))

# 모든 메시지 검색
messages = await context.get_messages()
print(f"총 {len(messages)}개의 메시지")
```

### BufferedChatCompletionContext

```python
class BufferedChatCompletionContext(buffer_size: int, initial_messages: List[LLMMessage] | None = None)
```

최근 n개의 메시지만 유지하는 버퍼링된 채팅 완성 컨텍스트입니다.

#### 주요 매개변수
- `buffer_size: int` - 버퍼 크기 (유지할 메시지 수)
- `initial_messages: List[LLMMessage] | None` - 초기 메시지 목록

#### 특징
- 고정된 크기의 슬라이딩 윈도우
- 메모리 사용량 제한
- 최근 대화에 집중

```python
# 예제: 최근 10개 메시지만 유지
from autogen_core.model_context import BufferedChatCompletionContext

context = BufferedChatCompletionContext(buffer_size=10)

# 메시지들 추가
for i in range(15):
    await context.add_message(UserMessage(content=f"메시지 {i}", source="user"))

# 최근 10개 메시지만 반환
messages = await context.get_messages()
print(f"버퍼 크기: {len(messages)}")  # 10개
```

### HeadAndTailChatCompletionContext

```python
class HeadAndTailChatCompletionContext(head_size: int, tail_size: int, initial_messages: List[LLMMessage] | None = None)
```

처음 n개와 마지막 m개의 메시지를 유지하는 채팅 완성 컨텍스트입니다.

#### 주요 매개변수
- `head_size: int` - 처음에서 유지할 메시지 수
- `tail_size: int` - 마지막에서 유지할 메시지 수
- `initial_messages: List[LLMMessage] | None` - 초기 메시지 목록

#### 특징
- 초기 컨텍스트(시스템 메시지 등)와 최근 대화 모두 보존
- 중간 대화는 제거하여 메모리 절약
- 장기 대화에서 중요한 정보 유지

```python
# 예제: 처음 5개와 마지막 5개 메시지 유지
from autogen_core.model_context import HeadAndTailChatCompletionContext

context = HeadAndTailChatCompletionContext(head_size=5, tail_size=5)

# 시스템 메시지 추가 (head에 포함됨)
await context.add_message(SystemMessage(content="당신은 전문가입니다."))

# 많은 메시지 추가
for i in range(20):
    await context.add_message(UserMessage(content=f"질문 {i}", source="user"))

# 처음 5개 + 마지막 5개 = 최대 10개 메시지 반환
messages = await context.get_messages()
print(f"Head + Tail 메시지 수: {len(messages)}")
```

### TokenLimitedChatCompletionContext

```python
class TokenLimitedChatCompletionContext(
    model_client: ChatCompletionClient, 
    *, 
    token_limit: int | None = None, 
    tool_schema: List[ToolSchema] | None = None, 
    initial_messages: List[LLMMessage] | None = None
)
```

토큰 제한에 기반하여 컨텍스트를 관리하는 채팅 완성 컨텍스트입니다. (실험적 기능)

#### 주요 매개변수
- `model_client: ChatCompletionClient` - 토큰 계산을 위한 모델 클라이언트
- `token_limit: int | None` - 최대 토큰 수 (None이면 모델 클라이언트의 remaining_tokens() 사용)
- `tool_schema: List[ToolSchema] | None` - 컨텍스트에서 사용할 도구 스키마 목록
- `initial_messages: List[LLMMessage] | None` - 초기 메시지 목록

#### 특징
- 토큰 수 기반 동적 관리
- 모델의 컨텍스트 윈도우 한계 고려
- 실시간 토큰 계산

```python
# 예제: 토큰 제한 기반 컨텍스트
from autogen_core.model_context import TokenLimitedChatCompletionContext

# 모델 클라이언트가 필요 (토큰 계산용)
context = TokenLimitedChatCompletionContext(
    model_client=your_model_client,
    token_limit=4000  # 4000 토큰 제한
)

# 메시지 추가 - 토큰 제한을 초과하면 오래된 메시지 제거
await context.add_message(SystemMessage(content="긴 시스템 프롬프트..."))
await context.add_message(UserMessage(content="사용자 질문", source="user"))

# 토큰 제한 내의 메시지만 반환
messages = await context.get_messages()
```

## 상태 관리

### ChatCompletionContextState

```python
class ChatCompletionContextState(BaseModel)
```

채팅 완성 컨텍스트의 상태를 나타내는 Pydantic 모델입니다.

#### 필드
- `messages: List[LLMMessage]` - 저장된 메시지 목록

```python
# 상태 저장 및 복원 예제
async def save_and_restore_context():
    # 원본 컨텍스트 생성
    original_context = UnboundedChatCompletionContext()
    await original_context.add_message(SystemMessage(content="시스템 메시지"))
    await original_context.add_message(UserMessage(content="사용자 메시지", source="user"))
    
    # 상태 저장
    state = await original_context.save_state()
    print(f"저장된 상태: {state}")
    
    # 새로운 컨텍스트에 상태 복원
    new_context = UnboundedChatCompletionContext()
    await new_context.load_state(state)
    
    # 복원된 메시지 확인
    restored_messages = await new_context.get_messages()
    print(f"복원된 메시지 수: {len(restored_messages)}")
```

## 실용적인 예제

### 대화형 챗봇 시스템

```python
import asyncio
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_core.models import SystemMessage, UserMessage, AssistantMessage

class ChatBot:
    def __init__(self, buffer_size: int = 20):
        self.context = BufferedChatCompletionContext(
            buffer_size=buffer_size,
            initial_messages=[
                SystemMessage(content="당신은 친근한 AI 어시스턴트입니다.")
            ]
        )
    
    async def chat(self, user_input: str) -> str:
        # 사용자 메시지 추가
        await self.context.add_message(
            UserMessage(content=user_input, source="user")
        )
        
        # 컨텍스트에서 메시지 가져오기
        messages = await self.context.get_messages()
        
        # 여기서 실제 모델 호출 (예시)
        # response = await model_client.create(messages)
        response_content = f"'{user_input}'에 대한 응답입니다."
        
        # 어시스턴트 응답 추가
        await self.context.add_message(
            AssistantMessage(content=response_content, source="assistant")
        )
        
        return response_content

# 사용 예제
async def main():
    chatbot = ChatBot(buffer_size=10)
    
    responses = []
    for i in range(15):
        response = await chatbot.chat(f"질문 {i}")
        responses.append(response)
    
    # 최근 대화만 유지됨
    messages = await chatbot.context.get_messages()
    print(f"유지된 메시지 수: {len(messages)}")

asyncio.run(main())
```

### 장기 대화 관리 시스템

```python
from autogen_core.model_context import HeadAndTailChatCompletionContext

class LongConversationManager:
    def __init__(self):
        self.context = HeadAndTailChatCompletionContext(
            head_size=5,  # 초기 컨텍스트 유지
            tail_size=10  # 최근 대화 유지
        )
        
        # 중요한 시스템 설정들
        initial_messages = [
            SystemMessage(content="당신은 전문 상담사입니다."),
            SystemMessage(content="사용자의 개인정보를 보호하세요."),
            SystemMessage(content="항상 공감적으로 대화하세요."),
        ]
        
        for msg in initial_messages:
            asyncio.create_task(self.context.add_message(msg))
    
    async def process_conversation(self, conversations: List[str]):
        for i, conv in enumerate(conversations):
            await self.context.add_message(
                UserMessage(content=conv, source="user")
            )
            
            # 모의 응답
            response = f"상담 응답 {i}"
            await self.context.add_message(
                AssistantMessage(content=response, source="counselor")
            )
        
        # 중요한 초기 설정 + 최근 대화만 유지
        final_messages = await self.context.get_messages()
        return final_messages

# 사용 예제
async def counseling_example():
    manager = LongConversationManager()
    
    # 긴 대화 시뮬레이션
    conversations = [f"상담 요청 {i}" for i in range(50)]
    
    final_context = await manager.process_conversation(conversations)
    print(f"최종 컨텍스트 크기: {len(final_context)}")
    print("시스템 메시지들이 보존되었는지 확인:")
    for msg in final_context[:5]:  # 처음 5개 확인
        if hasattr(msg, 'content'):
            print(f"- {msg.content[:50]}...")
```

### 토큰 효율적인 컨텍스트 관리

```python
from autogen_core.model_context import TokenLimitedChatCompletionContext

class TokenEfficientChat:
    def __init__(self, model_client, max_tokens: int = 3000):
        self.model_client = model_client
        self.context = TokenLimitedChatCompletionContext(
            model_client=model_client,
            token_limit=max_tokens
        )
    
    async def add_conversation_turn(self, user_msg: str, assistant_msg: str):
        # 사용자 메시지 추가
        await self.context.add_message(
            UserMessage(content=user_msg, source="user")
        )
        
        # 어시스턴트 메시지 추가
        await self.context.add_message(
            AssistantMessage(content=assistant_msg, source="assistant")
        )
        
        # 현재 컨텍스트 토큰 수 확인
        messages = await self.context.get_messages()
        token_count = await self.model_client.count_tokens(messages)
        
        return token_count
    
    async def get_context_summary(self):
        messages = await self.context.get_messages()
        token_count = await self.model_client.count_tokens(messages)
        
        return {
            "message_count": len(messages),
            "token_count": token_count,
            "messages": messages
        }

# 사용 예제 (의사 코드)
async def token_management_example():
    # model_client는 실제 ChatCompletionClient 인스턴스
    chat = TokenEfficientChat(model_client, max_tokens=2000)
    
    conversations = [
        ("긴 질문 1...", "긴 답변 1..."),
        ("긴 질문 2...", "긴 답변 2..."),
        # ... 더 많은 대화
    ]
    
    for user_msg, assistant_msg in conversations:
        token_count = await chat.add_conversation_turn(user_msg, assistant_msg)
        print(f"현재 토큰 수: {token_count}")
    
    summary = await chat.get_context_summary()
    print(f"최종 요약: {summary}")
```

### 추론 모델 전용 컨텍스트

```python
from autogen_core.model_context import UnboundedChatCompletionContext
from autogen_core.models import AssistantMessage

class ReasoningModelContext(UnboundedChatCompletionContext):
    """DeepSeek R1 같은 추론 모델용 컨텍스트"""
    
    async def get_messages(self) -> List[LLMMessage]:
        messages = await super().get_messages()
        
        # AssistantMessage에서 긴 thought 필드 제거
        cleaned_messages = []
        for message in messages:
            if isinstance(message, AssistantMessage):
                # thought 필드를 None으로 설정하여 후속 완성에서 제외
                cleaned_message = AssistantMessage(
                    content=message.content,
                    source=message.source,
                    thought=None  # 긴 추론 과정 제거
                )
                cleaned_messages.append(cleaned_message)
            else:
                cleaned_messages.append(message)
        
        return cleaned_messages
    
    async def add_reasoning_response(self, content: str, thought: str, source: str):
        """추론 과정이 포함된 응답 추가"""
        message = AssistantMessage(
            content=content,
            source=source,
            thought=thought
        )
        await self.add_message(message)

# 사용 예제
async def reasoning_example():
    context = ReasoningModelContext()
    
    # 시스템 메시지
    await context.add_message(
        SystemMessage(content="당신은 수학 문제를 해결하는 AI입니다.")
    )
    
    # 사용자 질문
    await context.add_message(
        UserMessage(content="2x + 5 = 11을 풀어주세요.", source="user")
    )
    
    # 추론 과정이 긴 응답 (실제로는 모델에서 생성됨)
    long_thought = """
    이 방정식을 풀기 위해 다음 단계를 따르겠습니다:
    1. 양변에서 5를 빼기
    2. 양변을 2로 나누기
    ... (매우 긴 추론 과정)
    """
    
    await context.add_reasoning_response(
        content="x = 3입니다.",
        thought=long_thought,
        source="reasoning_ai"
    )
    
    # 컨텍스트 검색 시 thought 필드가 제거됨
    messages = await context.get_messages()
    
    for msg in messages:
        if isinstance(msg, AssistantMessage):
            print(f"응답: {msg.content}")
            print(f"추론 과정 포함: {msg.thought is not None}")  # False
```

## 컨텍스트 선택 가이드

### 사용 사례별 권장사항

1. **단순한 챗봇**
   - `UnboundedChatCompletionContext` - 구현이 간단하고 모든 대화 유지

2. **메모리 제한이 있는 환경**
   - `BufferedChatCompletionContext` - 고정된 메모리 사용량

3. **장기 대화에서 초기 컨텍스트 보존 필요**
   - `HeadAndTailChatCompletionContext` - 시스템 메시지와 최근 대화 모두 유지

4. **토큰 비용 최적화 필요**
   - `TokenLimitedChatCompletionContext` - 정확한 토큰 제한 관리

5. **추론 모델 사용**
   - 커스텀 컨텍스트 - `thought` 필드 필터링

### 성능 고려사항

- **메모리 사용량**: Unbounded > HeadAndTail > Buffered > TokenLimited
- **계산 복잡도**: TokenLimited > HeadAndTail > Buffered > Unbounded
- **정확성**: TokenLimited > HeadAndTail > Buffered > Unbounded

## 주요 고려사항

### 상태 관리
- 모든 컨텍스트는 `save_state()`와 `load_state()` 지원
- 상태는 JSON 직렬화 가능해야 함
- 컨텍스트 타입에 따라 복원 시 동일한 매개변수 필요

### 성능 최적화
- 큰 컨텍스트에서는 토큰 기반 관리 고려
- 메모리 사용량과 응답 품질 간의 균형 필요
- 자주 사용되는 메시지는 초기 메시지로 설정

### 오류 처리
- 토큰 제한 초과 시 자동 메시지 제거
- 빈 컨텍스트 상황 처리
- 메시지 타입 호환성 확인

이 문서는 `autogen_core.model_context` 모듈의 모든 구성 요소를 다루며, 다양한 시나리오에서 효과적인 컨텍스트 관리를 위한 실용적인 가이드를 제공합니다.