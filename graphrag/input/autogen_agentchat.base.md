# autogen_agentchat.base 모듈

이 모듈은 AgentChat의 핵심 기본 클래스들과 프로토콜을 정의합니다. 모든 에이전트, 팀, 종료 조건의 기반이 되는 추상 클래스들을 포함합니다.

## 핵심 프로토콜

### ChatAgent

모든 채팅 에이전트가 구현해야 하는 프로토콜입니다.

**필수 구현 속성:**
- `name`: 에이전트 이름 (팀 내에서 고유해야 함)
- `description`: 에이전트 설명 (팀이 에이전트 선택 시 사용)
- `produced_message_types`: 생성하는 메시지 타입들

**필수 구현 메서드:**
- `on_messages()`: 메시지 처리 및 응답 생성
- `on_messages_stream()`: 스트리밍 방식 메시지 처리
- `on_reset()`: 초기 상태로 리셋
- `on_pause()`/`on_resume()`: 일시정지/재시작
- `save_state()`/`load_state()`: 상태 저장/로드
- `close()`: 리소스 해제

**예제 구현:**
```python
from autogen_agentchat.base import ChatAgent
from autogen_agentchat.messages import BaseChatMessage
from autogen_core import CancellationToken

class MyCustomAgent(ChatAgent):
    def __init__(self, name: str, description: str):
        self._name = name
        self._description = description
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def produced_message_types(self):
        return [TextMessage]
    
    async def on_messages(self, messages, cancellation_token):
        # 메시지 처리 로직
        response_message = TextMessage(content="응답", source=self.name)
        return Response(chat_message=response_message)
    
    async def on_reset(self, cancellation_token):
        # 리셋 로직
        pass
    
    # ... 기타 필수 메서드 구현
```

### TaskRunner

작업을 실행할 수 있는 객체의 프로토콜입니다.

**주요 메서드:**
- `run()`: 작업 실행 후 결과 반환
- `run_stream()`: 스트리밍 방식으로 작업 실행

**특징:**
- 상태를 유지하며 연속적인 호출 지원
- 작업이 지정되지 않으면 이전 작업에서 계속 진행
- 취소 토큰을 통한 작업 중단 지원

### Team

팀을 나타내는 추상 클래스입니다.

**필수 구현 메서드:**
- `reset()`: 팀과 모든 참가자를 초기 상태로 리셋
- `pause()`/`resume()`: 팀 일시정지/재시작
- `save_state()`/`load_state()`: 상태 저장/로드

## 응답 및 결과 클래스

### Response

에이전트의 `on_messages()` 호출 결과를 나타냅니다.

**주요 필드:**
- `chat_message`: 에이전트가 생성한 채팅 메시지
- `inner_messages`: 내부 처리 과정에서 생성된 메시지들

**예제:**
```python
from autogen_agentchat.base import Response
from autogen_agentchat.messages import TextMessage

# 간단한 응답
response = Response(
    chat_message=TextMessage(content="안녕하세요!", source="assistant")
)

# 내부 메시지가 있는 응답
response = Response(
    chat_message=TextMessage(content="최종 답변", source="assistant"),
    inner_messages=[
        TextMessage(content="중간 처리 1", source="assistant"),
        TextMessage(content="중간 처리 2", source="assistant"),
    ]
)
```

### TaskResult

작업 실행 결과를 나타내는 Pydantic 모델입니다.

**주요 필드:**
- `messages`: 작업 중 생성된 모든 메시지
- `stop_reason`: 작업 종료 이유

**예제:**
```python
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage

result = TaskResult(
    messages=[
        TextMessage(content="사용자 입력", source="user"),
        TextMessage(content="에이전트 응답", source="assistant"),
    ],
    stop_reason="종료 조건 만족"
)
```

## 종료 조건

### TerminationCondition

대화 종료 시점을 결정하는 추상 기본 클래스입니다.

**주요 특징:**
- 상태를 유지하는 조건부 객체
- 메시지 시퀀스를 받아 종료 여부 판단
- 한 번 종료 조건에 도달하면 리셋 후 재사용 가능
- AND/OR 연산자로 조건 조합 가능

**필수 구현:**
- `terminated` 속성: 종료 조건 도달 여부
- `reset()` 메서드: 조건 리셋

### AndTerminationCondition

여러 조건이 모두 만족될 때 종료하는 조건입니다.

**사용법:**
```python
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination

# 10개 메시지 AND "TERMINATE" 언급 시 종료
condition = MaxMessageTermination(10) & TextMentionTermination("TERMINATE")
```

### OrTerminationCondition

여러 조건 중 하나라도 만족되면 종료하는 조건입니다.

**사용법:**
```python
# 10개 메시지 OR "TERMINATE" 언급 시 종료
condition = MaxMessageTermination(10) | TextMentionTermination("TERMINATE")
```

**종료 조건 조합 예제:**
```python
import asyncio
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination

async def main():
    # OR 조건: 10턴 또는 "TERMINATE" 언급 시 종료
    cond1 = MaxMessageTermination(10) | TextMentionTermination("TERMINATE")
    
    # AND 조건: 10턴 AND "TERMINATE" 언급 시 종료
    cond2 = MaxMessageTermination(10) & TextMentionTermination("TERMINATE")
    
    # 복합 조건: (5턴 OR "DONE" 언급) AND "FINAL" 언급
    cond3 = (MaxMessageTermination(5) | TextMentionTermination("DONE")) & TextMentionTermination("FINAL")
    
    # 조건 리셋
    await cond1.reset()
    await cond2.reset()
    await cond3.reset()

asyncio.run(main())
```

## 핸드오프 구성

### Handoff

에이전트 간 작업 이양을 위한 구성 클래스입니다.

**주요 필드:**
- `target`: 이양 대상 에이전트 이름 (필수)
- `name`: 핸드오프 구성 이름 (자동 생성 가능)
- `description`: 핸드오프 설명 (자동 생성 가능)
- `message`: 대상 에이전트에게 전달할 메시지 (자동 생성 가능)

**특징:**
- `handoff_tool` 속성으로 핸드오프 도구 생성
- 필드가 비어있으면 대상 에이전트명 기반으로 자동 생성

**예제:**
```python
from autogen_agentchat.base import Handoff

# 기본 핸드오프 (자동 생성)
handoff1 = Handoff(target="specialist_agent")

# 상세 핸드오프
handoff2 = Handoff(
    target="code_reviewer",
    name="code_review_handoff",
    description="코드 검토가 필요할 때 사용",
    message="다음 코드를 검토해주세요."
)

# 핸드오프 도구 생성
tool = handoff2.handoff_tool
```

## 예외 클래스

### TerminatedException

종료 조건이 만족되었을 때 발생하는 예외입니다.

**특징:**
- `BaseException`을 상속 (시스템 레벨 예외)
- 정상적인 종료 신호로 사용
- 일반적인 예외 처리와 구분됨

## 활용 패턴

### 1. 커스텀 에이전트 구현
```python
class SpecializedAgent(ChatAgent):
    def __init__(self, name: str, specialty: str):
        self._name = name
        self._specialty = specialty
        self._state = {}
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return f"{self._specialty} 전문 에이전트"
    
    async def on_messages(self, messages, cancellation_token):
        # 전문 분야별 처리 로직
        pass
```

### 2. 커스텀 종료 조건
```python
class CustomTermination(TerminationCondition):
    def __init__(self, condition_func):
        self._condition_func = condition_func
        self._terminated = False
    
    @property
    def terminated(self) -> bool:
        return self._terminated
    
    async def reset(self):
        self._terminated = False
    
    def __call__(self, messages):
        if self._condition_func(messages):
            self._terminated = True
            return StopMessage(content="커스텀 조건 만족", source="system")
        return None
```

### 3. 응답 처리 패턴
```python
async def process_agent_response(agent, messages):
    response = await agent.on_messages(messages, CancellationToken())
    
    # 주 응답 처리
    main_message = response.chat_message
    print(f"주 응답: {main_message.content}")
    
    # 내부 메시지 처리
    if response.inner_messages:
        for inner_msg in response.inner_messages:
            print(f"내부 처리: {inner_msg}")
```

### 4. 작업 실행 패턴
```python
async def run_with_monitoring(task_runner, task):
    try:
        # 스트리밍으로 실행하며 모니터링
        async for item in task_runner.run_stream(task=task):
            if isinstance(item, TaskResult):
                print(f"작업 완료: {item.stop_reason}")
                return item
            else:
                print(f"진행 중: {item}")
    except TerminatedException:
        print("정상 종료됨")
```

## 주요 고려사항

1. **상태 관리**: 모든 컴포넌트는 상태를 적절히 관리해야 함
2. **리소스 해제**: `close()` 메서드로 리소스 정리 필수
3. **예외 처리**: `TerminatedException`은 정상 종료 신호임
4. **취소 토큰**: 모든 비동기 메서드는 취소 토큰을 지원해야 함
5. **메시지 타입**: `produced_message_types`는 정확히 명시해야 함

이러한 기본 클래스들을 이해하고 올바르게 구현하면 AutoGen 시스템과 완전히 호환되는 커스텀 컴포넌트를 만들 수 있습니다. 