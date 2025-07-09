# autogen_agentchat.agents 모듈

이 모듈은 AgentChat 패키지에서 제공하는 다양한 사전 정의된 에이전트들을 초기화합니다. `BaseChatAgent`는 AgentChat의 모든 에이전트의 기본 클래스입니다.

## 주요 클래스

### BaseChatAgent

모든 채팅 에이전트의 기본 추상 클래스입니다.

**주요 특징:**
- 상태를 유지하며 메서드 호출 간 상태를 보존
- 새로운 메시지만 전달받아야 함 (전체 대화 기록 X)
- `on_messages()`, `on_reset()`, `produced_message_types` 구현 필요
- 스트리밍이 필요한 경우 `on_messages_stream()` 구현

**주요 메서드:**
- `run()`: 주어진 작업으로 에이전트 실행
- `run_stream()`: 스트리밍 방식으로 에이전트 실행
- `on_messages()`: 메시지 처리 및 응답 생성
- `on_reset()`: 초기 상태로 리셋

### AssistantAgent

도구 사용 기능을 제공하는 어시스턴트 에이전트입니다.

**주요 매개변수:**
- `name`: 에이전트 이름
- `model_client`: 추론용 모델 클라이언트
- `tools`: 등록할 도구 목록
- `workbench`: 작업 환경 (도구와 상호 배타적)
- `handoffs`: 다른 에이전트로의 전환 설정
- `system_message`: 시스템 메시지
- `max_tool_iterations`: 도구 호출 최대 반복 횟수
- `reflect_on_tool_use`: 도구 사용 후 반성 여부
- `output_content_type`: 구조화된 출력 타입

**도구 호출 동작:**
- 도구 호출이 없으면 즉시 응답 반환
- 도구 호출이 있으면 즉시 실행
- `reflect_on_tool_use=False`: 도구 결과를 `ToolCallSummaryMessage`로 반환
- `reflect_on_tool_use=True`: 도구 결과를 바탕으로 추가 추론 후 응답

**핸드오프 동작:**
- 핸드오프가 트리거되면 `HandoffMessage` 반환
- 도구 호출과 핸드오프가 모두 있으면 도구 호출 먼저 실행

**예제:**
```python
import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    agent = AssistantAgent(name="assistant", model_client=model_client)
    result = await agent.run(task="북미의 두 도시 이름을 말해주세요.")
    print(result)

asyncio.run(main())
```

### CodeExecutorAgent

코드 생성 및 실행을 담당하는 에이전트입니다. (실험적 기능)

**주요 매개변수:**
- `name`: 에이전트 이름
- `code_executor`: 코드 실행기 (DockerCommandLineCodeExecutor 권장)
- `model_client`: 모델 클라이언트 (선택사항)
- `max_retries_on_error`: 오류 시 최대 재시도 횟수
- `supported_languages`: 지원 언어 목록

**동작 방식:**
- `model_client`가 있으면: 코드 생성 → 실행 → 결과 반영
- `model_client`가 없으면: 입력 메시지의 코드 블록만 실행

**예제:**
```python
import asyncio
from autogen_agentchat.agents import CodeExecutorAgent
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

async def main():
    code_executor = DockerCommandLineCodeExecutor(work_dir="coding")
    await code_executor.start()
    
    agent = CodeExecutorAgent("code_executor", code_executor=code_executor)
    # 코드 실행 후 정리
    await code_executor.stop()

asyncio.run(main())
```

### MessageFilterAgent

메시지 필터링 기능을 제공하는 래퍼 에이전트입니다. (실험적 기능)

**주요 기능:**
- 소스별 메시지 필터링
- 첫 번째/마지막 N개 메시지 선택
- 다중 에이전트 워크플로우에서 유용

**예제:**
```python
from autogen_agentchat.agents import MessageFilterAgent

agent = MessageFilterAgent(
    name="filtered_agent",
    wrapped_agent=base_agent,
    filter=MessageFilterConfig(
        per_source=[
            PerSourceFilter(source="user", position="first", count=1),
            PerSourceFilter(source="other_agent", position="last", count=2),
        ]
    )
)
```

### SocietyOfMindAgent

내부 에이전트 팀을 사용하여 응답을 생성하는 에이전트입니다.

**주요 매개변수:**
- `name`: 에이전트 이름
- `team`: 내부 에이전트 팀
- `model_client`: 응답 생성용 모델 클라이언트
- `instruction`: 응답 생성 시 사용할 지시사항
- `response_prompt`: 응답 프롬프트

**동작 방식:**
1. 내부 팀 실행
2. 팀 메시지를 바탕으로 모델 클라이언트로 응답 생성
3. 내부 팀 리셋

**예제:**
```python
import asyncio
from autogen_agentchat.agents import AssistantAgent, SocietyOfMindAgent
from autogen_agentchat.teams import RoundRobinGroupChat

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    
    agent1 = AssistantAgent("writer", model_client=model_client)
    agent2 = AssistantAgent("editor", model_client=model_client)
    
    inner_team = RoundRobinGroupChat([agent1, agent2])
    society_agent = SocietyOfMindAgent("society", team=inner_team, model_client=model_client)

asyncio.run(main())
```

### UserProxyAgent

입력 함수를 통해 사용자를 대표하는 에이전트입니다.

**주요 매개변수:**
- `name`: 에이전트 이름
- `description`: 에이전트 설명
- `input_func`: 사용자 입력을 받는 함수

**주의사항:**
- 사용자 응답을 기다리는 동안 팀이 차단 상태가 됨
- 타임아웃 및 취소 토큰 처리 필요
- 느린 사용자 응답에는 종료 조건 사용 권장

**예제:**
```python
import asyncio
from autogen_agentchat.agents import UserProxyAgent

async def main():
    agent = UserProxyAgent("user_proxy")
    # 사용자 입력 처리
    # 타임아웃 및 취소 처리 구현 필요

asyncio.run(main())
```

## 공통 기능

### 스트리밍 모드
- `model_client_stream=True` 설정으로 활성화
- `run_stream()` 및 `on_messages_stream()` 메서드 사용
- 실시간 응답 청크 생성

### 메모리 관리
- 다양한 메모리 타입 지원 (`ListMemory` 등)
- 모델 컨텍스트 업데이트를 통한 메모리 활용

### 구조화된 출력
- Pydantic 모델을 통한 구조화된 응답
- `output_content_type` 매개변수로 설정

### 컨텍스트 제한
- `BufferedChatCompletionContext`: 메시지 수 제한
- `TokenLimitedChatCompletionContext`: 토큰 수 제한

## 주요 고려사항

1. **스레드 안전성**: 에이전트는 스레드 안전하지 않으며 동시 실행하면 안 됨
2. **상태 관리**: 에이전트는 상태를 유지하므로 새 메시지만 전달
3. **도구 사용**: 도구와 워크벤치는 상호 배타적
4. **메모리 효율성**: 큰 파일의 경우 컨텍스트 제한 사용 권장
5. **에러 처리**: 적절한 예외 처리 및 재시도 로직 구현

이 모듈의 에이전트들은 다양한 AI 워크플로우와 멀티 에이전트 시스템 구축에 활용할 수 있습니다. 