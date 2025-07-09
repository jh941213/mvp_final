# autogen_agentchat.teams 모듈

이 모듈은 다양한 사전 정의된 멀티 에이전트 팀의 구현을 제공합니다. 각 팀은 `BaseGroupChat` 클래스를 상속받습니다.

## 기본 클래스

### BaseGroupChat

모든 그룹 채팅 팀의 기본 추상 클래스입니다.

**주요 특징:**
- 팀 상태 관리 (초기화, 실행, 일시정지, 재시작, 리셋)
- 상태 저장 및 로드 기능
- 종료 조건 및 최대 턴 수 제어
- 스트리밍 및 일반 실행 모드

**주요 메서드:**
- `run()`: 팀을 실행하고 결과 반환
- `run_stream()`: 스트리밍 방식으로 팀 실행
- `reset()`: 팀과 참가자를 초기 상태로 리셋
- `pause()`/`resume()`: 팀 일시정지/재시작 (실험적 기능)
- `save_state()`/`load_state()`: 상태 저장/로드

## 팀 구현체

### RoundRobinGroupChat

참가자들이 라운드로빈 방식으로 순서대로 메시지를 발행하는 팀입니다.

**주요 특징:**
- 참가자가 한 명인 경우 해당 참가자만 발언
- 순차적 턴 진행
- 간단하고 예측 가능한 실행 흐름

**예제:**
```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    
    agent1 = AssistantAgent("Assistant1", model_client=model_client)
    agent2 = AssistantAgent("Assistant2", model_client=model_client)
    
    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([agent1, agent2], termination_condition=termination)
    
    async for message in team.run_stream(task="농담을 몇 개 들려주세요."):
        print(message)

asyncio.run(main())
```

### SelectorGroupChat

ChatCompletion 모델을 사용하여 각 메시지 후 다음 발언자를 선택하는 팀입니다.

**주요 매개변수:**
- `model_client`: 다음 발언자 선택용 모델 클라이언트
- `selector_prompt`: 발언자 선택 프롬프트 템플릿
- `allow_repeated_speaker`: 이전 발언자의 연속 발언 허용 여부
- `selector_func`: 커스텀 발언자 선택 함수
- `candidate_func`: 후보자 필터링 함수

**프롬프트 템플릿 변수:**
- `{roles}`: 후보 에이전트의 이름과 설명
- `{participants}`: 후보자 이름 목록
- `{history}`: 대화 기록

**예제:**
```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    
    travel_advisor = AssistantAgent(
        "Travel_Advisor",
        model_client,
        description="여행 계획 도움",
    )
    hotel_agent = AssistantAgent(
        "Hotel_Agent", 
        model_client,
        description="호텔 예약 도움",
    )
    
    team = SelectorGroupChat(
        [travel_advisor, hotel_agent],
        model_client=model_client,
    )
    
    async for message in team.run_stream(task="3일간 뉴욕 여행을 예약해주세요."):
        print(message)

asyncio.run(main())
```

### Swarm

핸드오프 메시지만을 기반으로 다음 발언자를 선택하는 팀입니다.

**주요 특징:**
- 첫 번째 참가자가 초기 발언자
- `HandoffMessage`를 통한 발언자 전환
- 핸드오프가 없으면 현재 발언자 계속 진행
- 인간-루프 상호작용에 적합

**예제:**
```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import Swarm
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    
    agent1 = AssistantAgent(
        "Alice",
        model_client=model_client,
        handoffs=["Bob"],
        system_message="당신은 Alice이고 자신에 대한 질문만 답합니다.",
    )
    agent2 = AssistantAgent(
        "Bob", 
        model_client=model_client, 
        system_message="당신은 Bob이고 생일은 1월 1일입니다."
    )
    
    team = Swarm([agent1, agent2])
    
    async for message in team.run_stream(task="Bob의 생일은 언제인가요?"):
        print(message)

asyncio.run(main())
```

### MagenticOneGroupChat

MagenticOneOrchestrator가 참가자들을 관리하는 팀입니다.

**주요 특징:**
- Magentic-One 아키텍처 기반
- 오케스트레이터가 대화 흐름 관리
- 복잡한 작업 해결에 특화
- 효율적인 참가자 상호작용 보장

**주요 매개변수:**
- `model_client`: 응답 생성용 모델 클라이언트
- `max_stalls`: 재계획 전 최대 정체 횟수
- `final_answer_prompt`: 최종 답변 생성 프롬프트

**예제:**
```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    
    assistant = AssistantAgent("Assistant", model_client=model_client)
    team = MagenticOneGroupChat([assistant], model_client=model_client)
    
    async for message in team.run_stream(task="페르마의 마지막 정리에 대한 다른 증명을 제공해주세요"):
        print(message)

asyncio.run(main())
```

### GraphFlow

방향 그래프(DiGraph) 실행 패턴을 따르는 팀입니다. (실험적 기능)

**주요 특징:**
- 복잡한 워크플로우 지원 (순차, 병렬, 조건부 분기, 루프)
- 그래프 구조로 실행 순서 정의
- 노드별 활성화 조건 설정 가능
- 조건부 엣지를 통한 동적 흐름 제어

**지원 패턴:**
- **순차 실행**: A → B → C
- **병렬 팬아웃**: A → (B, C)
- **조건부 분기**: A → B (조건1) 또는 C (조건2)
- **루프**: A → B → A (조건부 종료)

**예제 - 순차 흐름:**
```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    
    agent_a = AssistantAgent("A", model_client=model_client)
    agent_b = AssistantAgent("B", model_client=model_client)
    agent_c = AssistantAgent("C", model_client=model_client)
    
    # 순차 그래프 구성: A → B → C
    builder = DiGraphBuilder()
    builder.add_node(agent_a).add_node(agent_b).add_node(agent_c)
    builder.add_edge(agent_a, agent_b).add_edge(agent_b, agent_c)
    graph = builder.build()
    
    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c],
        graph=graph,
    )
    
    async for event in team.run_stream(task="고양이에 관한 짧은 이야기를 써주세요."):
        print(event)

asyncio.run(main())
```

**예제 - 조건부 분기:**
```python
# 조건부 분기: A → B ("yes"인 경우) 또는 C (그 외)
builder = DiGraphBuilder()
builder.add_node(agent_a).add_node(agent_b).add_node(agent_c)
builder.add_edge(agent_a, agent_b, condition=lambda msg: "yes" in msg.to_model_text())
builder.add_edge(agent_a, agent_c, condition=lambda msg: "yes" not in msg.to_model_text())
```

## 그래프 구성 요소

### DiGraph

그래프 구조를 정의하는 Pydantic 모델입니다.

**주요 필드:**
- `nodes`: 노드와 엣지 정의
- `default_start_node`: 기본 시작 노드

**검증 기능:**
- 순환 구조 검증
- 종료 조건 확인
- 그래프 무결성 검사

### DiGraphBuilder

그래프를 편리하게 구성할 수 있는 빌더 클래스입니다.

**주요 메서드:**
- `add_node()`: 노드 추가
- `add_edge()`: 엣지 추가
- `add_conditional_edges()`: 다중 조건부 엣지 추가
- `set_entry_point()`: 시작 노드 설정
- `build()`: 검증된 DiGraph 생성

### DiGraphNode & DiGraphEdge

**DiGraphNode:**
- `name`: 노드 이름
- `edges`: 나가는 엣지 목록
- `activation`: 활성화 조건 ("all" 또는 "any")

**DiGraphEdge:**
- `target`: 대상 노드
- `condition`: 실행 조건 (문자열 또는 callable)
- `activation_group`: 활성화 그룹
- `activation_condition`: 그룹 내 활성화 조건

## 공통 기능

### 상태 관리

모든 팀은 상태 저장/로드 기능을 제공합니다:

```python
# 상태 저장
state = await team.save_state()

# 상태 로드
await team.load_state(state)
```

### 종료 조건

다양한 종료 조건을 설정할 수 있습니다:

```python
from autogen_agentchat.conditions import (
    MaxMessageTermination,
    TextMentionTermination,
    HandoffTermination
)

# 최대 메시지 수
termination = MaxMessageTermination(10)

# 특정 텍스트 언급
termination = TextMentionTermination("TERMINATE")

# 핸드오프 대상
termination = HandoffTermination(target="user")

# 조건 조합
termination = MaxMessageTermination(10) | TextMentionTermination("DONE")
```

### 실행 모드

**일반 실행:**
```python
result = await team.run(task="작업 내용")
print(result.messages)
```

**스트리밍 실행:**
```python
async for message in team.run_stream(task="작업 내용"):
    print(message)
```

**취소 토큰 사용:**
```python
from autogen_core import CancellationToken

cancellation_token = CancellationToken()
result = await team.run(task="작업 내용", cancellation_token=cancellation_token)
```

## 활용 패턴

### 1. 단순 협업
```python
# 라운드로빈으로 순차 협업
team = RoundRobinGroupChat([writer, reviewer, editor])
```

### 2. 지능형 라우팅
```python
# 모델이 적절한 전문가 선택
team = SelectorGroupChat([expert1, expert2, expert3], model_client)
```

### 3. 핸드오프 기반 워크플로우
```python
# 명시적 핸드오프로 제어
team = Swarm([coordinator, specialist1, specialist2])
```

### 4. 복잡한 그래프 워크플로우
```python
# 조건부 분기와 병렬 처리
builder = DiGraphBuilder()
# ... 그래프 구성
team = GraphFlow(participants, graph=builder.build())
```

### 5. 오케스트레이션 기반
```python
# 중앙 집중식 관리
team = MagenticOneGroupChat([agent1, agent2, agent3], model_client)
```

## 주요 고려사항

1. **성능**: 복잡한 그래프나 많은 참가자는 성능에 영향
2. **상태 일관성**: 실행 중 상태 저장 시 일관성 문제 가능
3. **종료 조건**: 무한 루프 방지를 위한 적절한 종료 조건 필요
4. **에러 처리**: 참가자 에러가 팀 전체에 영향 가능
5. **메모리 관리**: 긴 대화 기록은 메모리 사용량 증가

이러한 팀 구현체들을 활용하면 다양한 멀티 에이전트 협업 시나리오를 효과적으로 구현할 수 있습니다. 