# autogen_agentchat.conditions 모듈

이 모듈은 멀티 에이전트 팀의 동작을 제어하기 위한 다양한 종료 조건들을 제공합니다.

## 종료 조건 개요

모든 종료 조건은 `TerminationCondition` 기본 클래스를 상속받으며, 다음과 같은 공통 특징을 가집니다:

- **상태 유지**: 종료 조건 도달 여부를 추적
- **리셋 가능**: `reset()` 메서드로 재사용 가능
- **조합 가능**: AND(`&`) 및 OR(`|`) 연산자로 조건 조합
- **비동기 지원**: 모든 메서드가 비동기 처리 지원

## 기본 종료 조건들

### MaxMessageTermination

지정된 최대 메시지 수에 도달하면 대화를 종료합니다.

**매개변수:**
- `max_messages`: 허용되는 최대 메시지 수
- `include_agent_event`: `BaseAgentEvent`를 메시지 수에 포함할지 여부 (기본값: False)

**예제:**
```python
from autogen_agentchat.conditions import MaxMessageTermination

# 최대 10개 메시지 후 종료
termination = MaxMessageTermination(10)

# 에이전트 이벤트도 포함하여 카운트
termination_with_events = MaxMessageTermination(10, include_agent_event=True)
```

### TextMentionTermination

특정 텍스트가 언급되면 대화를 종료합니다.

**매개변수:**
- `text`: 찾을 텍스트
- `sources`: 특정 에이전트의 메시지만 확인 (선택사항)

**예제:**
```python
from autogen_agentchat.conditions import TextMentionTermination

# "TERMINATE" 언급 시 종료
termination = TextMentionTermination("TERMINATE")

# 특정 에이전트의 "완료" 언급 시에만 종료
termination_specific = TextMentionTermination("완료", sources=["reviewer", "manager"])
```

### SourceMatchTermination

특정 에이전트가 응답하면 대화를 종료합니다.

**매개변수:**
- `sources`: 종료를 트리거할 에이전트 이름 목록

**예제:**
```python
from autogen_agentchat.conditions import SourceMatchTermination

# "final_agent"가 응답하면 종료
termination = SourceMatchTermination(["final_agent"])

# 여러 에이전트 중 하나가 응답하면 종료
termination_multiple = SourceMatchTermination(["agent1", "agent2", "supervisor"])
```

### HandoffTermination

특정 대상으로의 핸드오프 메시지를 받으면 대화를 종료합니다.

**매개변수:**
- `target`: 핸드오프 대상 이름

**예제:**
```python
from autogen_agentchat.conditions import HandoffTermination

# "user"로의 핸드오프 시 종료 (인간-루프 상호작용용)
termination = HandoffTermination("user")
```

### FunctionCallTermination

특정 함수 실행 결과를 받으면 대화를 종료합니다.

**매개변수:**
- `function_name`: 확인할 함수 이름

**예제:**
```python
from autogen_agentchat.conditions import FunctionCallTermination

# "finalize_task" 함수 호출 결과 시 종료
termination = FunctionCallTermination("finalize_task")
```

## 메시지 타입 기반 종료 조건

### TextMessageTermination

`TextMessage`를 받으면 대화를 종료합니다.

**매개변수:**
- `source`: 특정 소스의 메시지만 확인 (선택사항)

**예제:**
```python
from autogen_agentchat.conditions import TextMessageTermination

# 모든 텍스트 메시지에서 종료
termination = TextMessageTermination()

# 특정 에이전트의 텍스트 메시지에서만 종료
termination_specific = TextMessageTermination(source="final_agent")
```

### StopMessageTermination

`StopMessage`를 받으면 대화를 종료합니다.

**예제:**
```python
from autogen_agentchat.conditions import StopMessageTermination

# StopMessage 수신 시 종료
termination = StopMessageTermination()
```

## 시간 및 리소스 기반 종료 조건

### TimeoutTermination

지정된 시간이 경과하면 대화를 종료합니다.

**매개변수:**
- `timeout_seconds`: 제한 시간 (초)

**예제:**
```python
from autogen_agentchat.conditions import TimeoutTermination

# 30초 후 종료
termination = TimeoutTermination(30.0)

# 5분 후 종료
termination_long = TimeoutTermination(300.0)
```

### TokenUsageTermination

토큰 사용량 한계에 도달하면 대화를 종료합니다.

**매개변수:**
- `max_total_token`: 최대 총 토큰 수
- `max_prompt_token`: 최대 프롬프트 토큰 수
- `max_completion_token`: 최대 완성 토큰 수

**예제:**
```python
from autogen_agentchat.conditions import TokenUsageTermination

# 총 1000 토큰 제한
termination = TokenUsageTermination(max_total_token=1000)

# 프롬프트와 완성 토큰 각각 제한
termination_detailed = TokenUsageTermination(
    max_prompt_token=800,
    max_completion_token=200
)

# 모든 토큰 타입 제한
termination_comprehensive = TokenUsageTermination(
    max_total_token=1000,
    max_prompt_token=600,
    max_completion_token=400
)
```

## 제어 기반 종료 조건

### ExternalTermination

외부에서 수동으로 제어하는 종료 조건입니다.

**주요 메서드:**
- `set()`: 종료 조건을 활성화

**예제:**
```python
import asyncio
from autogen_agentchat.conditions import ExternalTermination

async def main():
    termination = ExternalTermination()
    
    # 팀을 백그라운드 태스크로 실행
    team_task = asyncio.create_task(team.run_stream(task="작업 시작"))
    
    # 5초 후 외부에서 종료
    await asyncio.sleep(5)
    termination.set()
    
    # 팀 종료 대기
    await team_task

asyncio.run(main())
```

### FunctionalTermination

커스텀 함수를 사용한 종료 조건입니다.

**매개변수:**
- `func`: 메시지 시퀀스를 받아 boolean을 반환하는 함수 (동기/비동기 모두 지원)

**예제:**
```python
from autogen_agentchat.conditions import FunctionalTermination
from autogen_agentchat.messages import StopMessage

def custom_condition(messages):
    # 마지막 메시지가 StopMessage인지 확인
    return isinstance(messages[-1], StopMessage)

# 커스텀 조건으로 종료
termination = FunctionalTermination(custom_condition)

# 비동기 함수 사용
async def async_condition(messages):
    # 복잡한 비동기 검증 로직
    await asyncio.sleep(0.1)  # 예시 비동기 작업
    return len(messages) > 5 and "완료" in messages[-1].content

termination_async = FunctionalTermination(async_condition)
```

## 조건 조합

종료 조건들은 논리 연산자로 조합할 수 있습니다.

### AND 조합 (`&`)

모든 조건이 만족되어야 종료됩니다.

```python
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination

# 10개 메시지 AND "TERMINATE" 언급 시 종료
termination = MaxMessageTermination(10) & TextMentionTermination("TERMINATE")
```

### OR 조합 (`|`)

조건 중 하나라도 만족되면 종료됩니다.

```python
# 10개 메시지 OR "TERMINATE" 언급 시 종료
termination = MaxMessageTermination(10) | TextMentionTermination("TERMINATE")
```

### 복합 조합

복잡한 조건 조합도 가능합니다.

```python
from autogen_agentchat.conditions import (
    MaxMessageTermination,
    TextMentionTermination,
    TimeoutTermination,
    SourceMatchTermination
)

# 복합 조건: (5분 타임아웃 OR 20개 메시지) AND ("완료" 언급 OR supervisor 응답)
complex_termination = (
    (TimeoutTermination(300) | MaxMessageTermination(20)) &
    (TextMentionTermination("완료") | SourceMatchTermination(["supervisor"]))
)
```

## 실용적인 활용 패턴

### 1. 기본 대화 제한
```python
# 기본적인 대화 제한 설정
basic_termination = (
    MaxMessageTermination(50) |  # 최대 50개 메시지
    TextMentionTermination("TERMINATE") |  # 종료 키워드
    TimeoutTermination(1800)  # 30분 타임아웃
)
```

### 2. 리소스 관리
```python
# 토큰 사용량과 시간 제한
resource_termination = (
    TokenUsageTermination(max_total_token=5000) |
    TimeoutTermination(600)  # 10분
)
```

### 3. 워크플로우 제어
```python
# 특정 단계 완료 후 종료
workflow_termination = (
    SourceMatchTermination(["final_reviewer"]) |
    HandoffTermination("user") |  # 사용자 개입 필요
    MaxMessageTermination(100)  # 안전장치
)
```

### 4. 인간-루프 상호작용
```python
# 사용자 개입이 필요한 상황
human_loop_termination = (
    HandoffTermination("user") |
    TextMentionTermination("도움 필요") |
    FunctionCallTermination("request_human_help")
)
```

### 5. 커스텀 비즈니스 로직
```python
def business_logic_check(messages):
    # 비즈니스 규칙 확인
    if len(messages) < 3:
        return False
    
    last_message = messages[-1]
    if hasattr(last_message, 'content'):
        # 특정 키워드나 패턴 확인
        return any(keyword in last_message.content.lower() 
                  for keyword in ["승인됨", "거부됨", "보류"])
    return False

business_termination = FunctionalTermination(business_logic_check)
```

## 종료 조건 관리

### 리셋과 재사용
```python
async def run_multiple_sessions():
    termination = MaxMessageTermination(10) | TextMentionTermination("DONE")
    
    # 첫 번째 세션
    await team.run(task="첫 번째 작업", termination_condition=termination)
    
    # 종료 조건 리셋 후 재사용
    await termination.reset()
    
    # 두 번째 세션
    await team.run(task="두 번째 작업", termination_condition=termination)
```

### 동적 조건 변경
```python
class DynamicTermination:
    def __init__(self):
        self.external = ExternalTermination()
        self.current_condition = MaxMessageTermination(10)
    
    def update_condition(self, new_condition):
        self.current_condition = new_condition
    
    def trigger_external(self):
        self.external.set()
    
    @property
    def combined_condition(self):
        return self.current_condition | self.external
```

## 주요 고려사항

1. **성능**: 복잡한 조건 조합은 성능에 영향을 줄 수 있음
2. **메모리**: 긴 메시지 히스토리는 메모리 사용량 증가
3. **타이밍**: 시간 기반 조건은 시스템 시계에 의존
4. **토큰 계산**: 토큰 사용량 조건은 모델별로 다를 수 있음
5. **상태 관리**: 종료 조건 상태를 적절히 리셋해야 함

이러한 다양한 종료 조건들을 적절히 조합하여 사용하면 멀티 에이전트 시스템의 동작을 정밀하게 제어할 수 있습니다. 