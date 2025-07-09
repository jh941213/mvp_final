# autogen_agentchat.tools 모듈

이 모듈은 AgentChat에서 사용할 수 있는 도구들을 제공합니다. 에이전트나 팀을 도구로 래핑하여 다른 에이전트에서 활용할 수 있게 해줍니다.

## 주요 클래스

### AgentTool

단일 에이전트를 도구로 래핑하여 다른 에이전트에서 작업을 실행할 수 있게 해주는 도구입니다.

**주요 매개변수:**
- `agent`: 작업 실행에 사용할 `BaseChatAgent` 인스턴스
- `return_value_as_last_message`: 반환값 형식 제어
  - `True`: 마지막 메시지 내용만 문자열로 반환
  - `False`: 모든 메시지를 소스 접두사와 함께 연결하여 반환 (예: "writer: ...", "assistant: ...")

**주요 특징:**
- `TaskResult` 객체로 작업 실행 결과 반환
- 다른 에이전트의 도구로 등록 가능
- 에이전트 간 협업 워크플로우 구성에 유용

**예제:**
```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4")
    
    # 글쓰기 전문 에이전트 생성
    writer = AssistantAgent(
        name="writer",
        description="텍스트 생성 전문 에이전트",
        model_client=model_client,
        system_message="잘 쓰세요.",
    )
    
    # 글쓰기 에이전트를 도구로 래핑
    writer_tool = AgentTool(agent=writer)
    
    # 메인 어시스턴트에 글쓰기 도구 등록
    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=[writer_tool],
        system_message="당신은 도움이 되는 어시스턴트입니다.",
    )
    
    await Console(assistant.run_stream(task="바다에 관한 시를 써주세요."))

asyncio.run(main())
```

**사용 시나리오:**
- 특화된 에이전트를 범용 에이전트의 도구로 활용
- 복잡한 작업을 전문 에이전트에게 위임
- 모듈화된 에이전트 시스템 구축

### TeamTool

에이전트 팀을 도구로 래핑하여 다른 에이전트에서 팀 작업을 실행할 수 있게 해주는 도구입니다.

**주요 매개변수:**
- `team`: 작업 실행에 사용할 `BaseGroupChat` 팀 인스턴스
- `name`: 도구의 이름
- `description`: 도구에 대한 설명
- `return_value_as_last_message`: 반환값 형식 제어 (AgentTool과 동일)

**주요 특징:**
- 여러 에이전트로 구성된 팀을 하나의 도구로 추상화
- 복잡한 협업 워크플로우를 단순한 도구 호출로 변환
- 계층적 에이전트 시스템 구축 가능

**예제:**
```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import SourceMatchTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.tools import TeamTool
from autogen_agentchat.ui import Console
from autogen_ext.models.ollama import OllamaChatCompletionClient

async def main():
    model_client = OllamaChatCompletionClient(model="llama3.2")

    # 글쓰기 팀 구성
    writer = AssistantAgent(
        name="writer", 
        model_client=model_client, 
        system_message="당신은 도움이 되는 어시스턴트입니다."
    )
    reviewer = AssistantAgent(
        name="reviewer", 
        model_client=model_client, 
        system_message="당신은 비판적인 검토자입니다."
    )
    summarizer = AssistantAgent(
        name="summarizer",
        model_client=model_client,
        system_message="검토를 결합하여 수정된 응답을 생성합니다.",
    )
    
    # 라운드로빈 팀 생성
    team = RoundRobinGroupChat(
        [writer, reviewer, summarizer], 
        termination_condition=SourceMatchTermination(sources=["summarizer"])
    )

    # 팀을 도구로 래핑
    tool = TeamTool(
        team=team, 
        name="writing_team", 
        description="글쓰기 작업을 위한 도구", 
        return_value_as_last_message=True
    )

    # 메인 에이전트에 팀 도구 등록
    main_agent = AssistantAgent(
        name="main_agent",
        model_client=model_client,
        system_message="글쓰기 도구를 사용할 수 있는 도움이 되는 어시스턴트입니다.",
        tools=[tool],
    )
    
    await Console(
        main_agent.run_stream(
            task="사랑을 배우는 로봇에 관한 짧은 이야기를 써주세요.",
        )
    )

asyncio.run(main())
```

**사용 시나리오:**
- 복잡한 다단계 작업을 팀으로 처리
- 전문화된 팀을 재사용 가능한 도구로 변환
- 계층적 멀티 에이전트 시스템 구축

## 공통 기능

### 반환값 형식 제어

두 도구 모두 `return_value_as_last_message` 매개변수로 반환값 형식을 제어할 수 있습니다:

**`return_value_as_last_message=True`:**
```
"최종 결과 메시지 내용"
```

**`return_value_as_last_message=False`:**
```
"writer: 첫 번째 메시지 내용
reviewer: 검토 메시지 내용
summarizer: 최종 요약 내용"
```

### 구성 관리

두 클래스 모두 `Component` 기반으로 구성 관리 기능을 제공합니다:

- `_from_config()`: 구성 객체로부터 인스턴스 생성
- `_to_config()`: 현재 인스턴스의 구성 덤프
- 직렬화/역직렬화 지원

## 활용 패턴

### 1. 전문화된 에이전트 도구화
```python
# 코딩 전문 에이전트
coding_agent = AssistantAgent("coder", model_client, system_message="코딩 전문가")
coding_tool = AgentTool(coding_agent)

# 번역 전문 에이전트
translation_agent = AssistantAgent("translator", model_client, system_message="번역 전문가")
translation_tool = AgentTool(translation_agent)

# 범용 에이전트에 전문 도구들 등록
general_agent = AssistantAgent("assistant", model_client, tools=[coding_tool, translation_tool])
```

### 2. 계층적 팀 구조
```python
# 하위 팀들
research_team = RoundRobinGroupChat([researcher, analyst])
writing_team = RoundRobinGroupChat([writer, editor])

# 하위 팀들을 도구로 변환
research_tool = TeamTool(research_team, "research", "연구 작업")
writing_tool = TeamTool(writing_team, "writing", "글쓰기 작업")

# 상위 에이전트가 하위 팀들을 활용
coordinator = AssistantAgent("coordinator", model_client, tools=[research_tool, writing_tool])
```

### 3. 워크플로우 모듈화
```python
# 각 단계별 팀을 도구로 모듈화
planning_tool = TeamTool(planning_team, "planning", "계획 수립")
execution_tool = TeamTool(execution_team, "execution", "실행")
review_tool = TeamTool(review_team, "review", "검토")

# 워크플로우 관리자가 단계별 도구 활용
workflow_manager = AssistantAgent(
    "manager", 
    model_client, 
    tools=[planning_tool, execution_tool, review_tool]
)
```

## 주요 고려사항

1. **성능**: 도구로 래핑된 에이전트/팀은 별도의 실행 컨텍스트에서 동작
2. **상태 관리**: 각 도구 호출은 독립적이며 상태를 유지하지 않음
3. **오류 처리**: 래핑된 에이전트/팀의 오류는 도구 실행 결과에 반영
4. **리소스 관리**: 복잡한 팀 도구는 상당한 컴퓨팅 리소스 소모 가능

이러한 도구들을 활용하면 복잡하고 확장 가능한 멀티 에이전트 시스템을 효율적으로 구축할 수 있습니다. 