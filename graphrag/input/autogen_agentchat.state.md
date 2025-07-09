# autogen_agentchat.state 모듈

이 모듈은 에이전트, 팀, 종료 조건의 상태 관리를 위한 Pydantic 모델들을 제공합니다.

## 상태 관리 개요

AutoGen의 상태 관리 시스템은 다음과 같은 특징을 가집니다:

- **직렬화 가능**: 모든 상태는 JSON으로 직렬화/역직렬화 가능
- **버전 관리**: 상태 스키마 버전을 추적하여 호환성 보장
- **타입 안전성**: Pydantic 모델을 통한 타입 검증
- **계층적 구조**: 기본 클래스에서 파생된 전문화된 상태 클래스들

## 기본 상태 클래스

### BaseState

모든 저장 가능한 상태의 기본 클래스입니다.

**주요 필드:**
- `type`: 상태 타입 식별자 (기본값: "BaseState")
- `version`: 상태 스키마 버전 (기본값: "1.0.0")

**특징:**
- 모든 상태 클래스의 부모 클래스
- 타입과 버전 정보를 통한 상태 식별
- JSON 직렬화/역직렬화 지원

**예제:**
```python
from autogen_agentchat.state import BaseState

# 기본 상태 생성
base_state = BaseState()
print(base_state.type)     # "BaseState"
print(base_state.version)  # "1.0.0"

# JSON 직렬화
state_json = base_state.model_dump_json()
print(state_json)

# JSON에서 복원
restored_state = BaseState.model_validate_json(state_json)
```

## 에이전트 상태 클래스

### AssistantAgentState

AssistantAgent의 상태를 나타냅니다.

**주요 필드:**
- `type`: "AssistantAgentState"
- `llm_context`: LLM 컨텍스트 정보 (선택사항)

**사용 시나리오:**
- 에이전트의 대화 컨텍스트 저장
- 모델 상태 및 설정 보존
- 세션 간 연속성 유지

**예제:**
```python
from autogen_agentchat.state import AssistantAgentState

# 에이전트 상태 생성
agent_state = AssistantAgentState(
    llm_context={
        "messages": [{"role": "system", "content": "You are a helpful assistant"}],
        "model_settings": {"temperature": 0.7}
    }
)

# 상태 저장
saved_state = agent_state.model_dump()
```

### SocietyOfMindAgentState

SocietyOfMindAgent의 상태를 나타냅니다.

**주요 필드:**
- `type`: "SocietyOfMindAgentState"
- `inner_team_state`: 내부 팀의 상태 정보 (선택사항)

**사용 시나리오:**
- 내부 팀의 전체 상태 보존
- 복잡한 멀티 에이전트 시스템의 상태 관리
- 계층적 에이전트 구조의 상태 저장

**예제:**
```python
from autogen_agentchat.state import SocietyOfMindAgentState

# Society of Mind 에이전트 상태
som_state = SocietyOfMindAgentState(
    inner_team_state={
        "team_members": ["writer", "reviewer", "editor"],
        "current_phase": "writing",
        "collaboration_history": []
    }
)
```

### ChatAgentContainerState

채팅 에이전트 컨테이너의 상태를 나타냅니다.

**주요 필드:**
- `type`: "ChatAgentContainerState"
- `agent_state`: 에이전트 상태 정보 (선택사항)
- `message_buffer`: 메시지 버퍼 (선택사항)

**사용 시나리오:**
- 에이전트와 메시지 버퍼의 통합 상태 관리
- 컨테이너화된 에이전트 환경의 상태 보존
- 메시지 큐 및 처리 상태 저장

**예제:**
```python
from autogen_agentchat.state import ChatAgentContainerState

# 컨테이너 상태 생성
container_state = ChatAgentContainerState(
    agent_state={
        "name": "assistant",
        "active": True,
        "last_response_time": "2024-01-01T10:00:00Z"
    },
    message_buffer=[
        {"id": 1, "content": "Hello", "timestamp": "2024-01-01T10:00:00Z"},
        {"id": 2, "content": "How can I help?", "timestamp": "2024-01-01T10:00:01Z"}
    ]
)
```

## 팀 상태 클래스

### TeamState

에이전트 팀의 상태를 나타냅니다.

**주요 필드:**
- `type`: "TeamState"
- `agent_states`: 팀 내 모든 에이전트의 상태 (선택사항)

**사용 시나리오:**
- 팀 전체의 통합 상태 관리
- 팀 멤버별 개별 상태 추적
- 팀 레벨 복원 및 재시작

**예제:**
```python
from autogen_agentchat.state import TeamState

# 팀 상태 생성
team_state = TeamState(
    agent_states={
        "agent1": {
            "type": "AssistantAgentState",
            "llm_context": {"messages": []}
        },
        "agent2": {
            "type": "AssistantAgentState", 
            "llm_context": {"messages": []}
        },
        "manager": {
            "type": "RoundRobinManagerState",
            "next_speaker_index": 0
        }
    }
)
```

## 그룹 채팅 매니저 상태 클래스

### BaseGroupChatManagerState

모든 그룹 채팅 매니저의 기본 상태입니다.

**주요 필드:**
- `type`: "BaseGroupChatManagerState"
- `current_turn`: 현재 턴 번호 (기본값: 0)
- `message_thread`: 메시지 스레드 (선택사항)

**공통 기능:**
- 턴 기반 대화 상태 추적
- 메시지 히스토리 관리
- 모든 매니저의 공통 상태 요소

### RoundRobinManagerState

라운드로빈 그룹 채팅 매니저의 상태입니다.

**주요 필드:**
- `type`: "RoundRobinManagerState"
- `next_speaker_index`: 다음 발언자 인덱스 (기본값: 0)

**사용 시나리오:**
- 순차적 발언 순서 관리
- 중단된 대화의 재시작 지점 저장
- 라운드로빈 로직의 상태 보존

**예제:**
```python
from autogen_agentchat.state import RoundRobinManagerState

# 라운드로빈 매니저 상태
rr_state = RoundRobinManagerState(
    current_turn=5,
    next_speaker_index=2,
    message_thread=[
        {"speaker": "agent1", "content": "Hello"},
        {"speaker": "agent2", "content": "Hi there"}
    ]
)
```

### SelectorManagerState

셀렉터 그룹 채팅 매니저의 상태입니다.

**주요 필드:**
- `type`: "SelectorManagerState"
- `previous_speaker`: 이전 발언자 (선택사항)

**사용 시나리오:**
- AI 기반 발언자 선택 로직의 상태 추적
- 이전 발언자 정보 기반 선택 제한
- 동적 발언자 선택 히스토리 관리

**예제:**
```python
from autogen_agentchat.state import SelectorManagerState

# 셀렉터 매니저 상태
selector_state = SelectorManagerState(
    current_turn=3,
    previous_speaker="expert_agent",
    message_thread=[
        {"speaker": "user", "content": "What's the weather?"},
        {"speaker": "weather_agent", "content": "It's sunny"},
        {"speaker": "expert_agent", "content": "Perfect for outdoor activities"}
    ]
)
```

### SwarmManagerState

Swarm 매니저의 상태입니다.

**주요 필드:**
- `type`: "SwarmManagerState"
- `current_speaker`: 현재 발언자

**사용 시나리오:**
- 핸드오프 기반 발언자 제어
- 현재 활성 에이전트 추적
- Swarm 패턴의 상태 관리

**예제:**
```python
from autogen_agentchat.state import SwarmManagerState

# Swarm 매니저 상태
swarm_state = SwarmManagerState(
    current_turn=2,
    current_speaker="specialist_agent",
    message_thread=[
        {"speaker": "coordinator", "content": "Starting task"},
        {"speaker": "specialist_agent", "content": "I'll handle this"}
    ]
)
```

### MagenticOneOrchestratorState

MagenticOne 오케스트레이터의 상태입니다.

**주요 필드:**
- `type`: "MagenticOneOrchestratorState"
- `facts`: 수집된 사실 정보
- `n_rounds`: 라운드 수 (기본값: 0)
- `n_stalls`: 정체 횟수 (기본값: 0)
- `plan`: 현재 계획
- `task`: 현재 작업

**사용 시나리오:**
- 복잡한 작업의 진행 상태 추적
- 오케스트레이션 로직의 상태 보존
- 계획 수립 및 실행 상태 관리

**예제:**
```python
from autogen_agentchat.state import MagenticOneOrchestratorState

# MagenticOne 오케스트레이터 상태
magentic_state = MagenticOneOrchestratorState(
    current_turn=8,
    facts="User wants to analyze sales data. Data is in CSV format.",
    n_rounds=2,
    n_stalls=0,
    plan="1. Load data 2. Analyze trends 3. Generate report",
    task="Analyze Q4 sales performance and identify key trends",
    message_thread=[]
)
```

## 상태 사용 패턴

### 1. 상태 저장 및 복원

```python
import json
from autogen_agentchat.state import AssistantAgentState

async def save_agent_state(agent, filepath):
    """에이전트 상태를 파일에 저장"""
    state = await agent.save_state()
    agent_state = AssistantAgentState(**state)
    
    with open(filepath, 'w') as f:
        json.dump(agent_state.model_dump(), f, indent=2)

async def load_agent_state(agent, filepath):
    """파일에서 에이전트 상태를 복원"""
    with open(filepath, 'r') as f:
        state_data = json.load(f)
    
    agent_state = AssistantAgentState.model_validate(state_data)
    await agent.load_state(agent_state.model_dump())
```

### 2. 팀 상태 관리

```python
async def save_team_state(team, filepath):
    """팀 전체 상태를 저장"""
    state = await team.save_state()
    team_state = TeamState(**state)
    
    with open(filepath, 'w') as f:
        json.dump(team_state.model_dump(), f, indent=2)

async def restore_team_session(team, filepath):
    """저장된 팀 상태에서 세션 복원"""
    with open(filepath, 'r') as f:
        state_data = json.load(f)
    
    team_state = TeamState.model_validate(state_data)
    await team.load_state(team_state.model_dump())
    
    print(f"팀 세션이 복원되었습니다. 에이전트 수: {len(team_state.agent_states)}")
```

### 3. 상태 기반 체크포인트

```python
class StateCheckpoint:
    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoints = {}
    
    async def save_checkpoint(self, name: str, component, state_class):
        """컴포넌트 상태를 체크포인트로 저장"""
        state = await component.save_state()
        typed_state = state_class(**state)
        
        filepath = f"{self.checkpoint_dir}/{name}.json"
        with open(filepath, 'w') as f:
            json.dump(typed_state.model_dump(), f, indent=2)
        
        self.checkpoints[name] = {
            'filepath': filepath,
            'state_class': state_class,
            'timestamp': datetime.now().isoformat()
        }
    
    async def restore_checkpoint(self, name: str, component):
        """체크포인트에서 컴포넌트 상태 복원"""
        if name not in self.checkpoints:
            raise ValueError(f"체크포인트 '{name}'을 찾을 수 없습니다")
        
        checkpoint_info = self.checkpoints[name]
        with open(checkpoint_info['filepath'], 'r') as f:
            state_data = json.load(f)
        
        state_class = checkpoint_info['state_class']
        typed_state = state_class.model_validate(state_data)
        await component.load_state(typed_state.model_dump())
```

### 4. 상태 마이그레이션

```python
def migrate_state_version(state_data: dict, target_version: str):
    """상태 버전 간 마이그레이션"""
    current_version = state_data.get('version', '1.0.0')
    
    if current_version == '1.0.0' and target_version == '1.1.0':
        # 버전 1.0.0에서 1.1.0으로 마이그레이션
        if 'new_field' not in state_data:
            state_data['new_field'] = 'default_value'
        state_data['version'] = '1.1.0'
    
    return state_data

def load_compatible_state(state_data: dict, state_class):
    """호환 가능한 상태로 로드"""
    # 필요시 마이그레이션 수행
    if state_data.get('version') != '1.0.0':
        state_data = migrate_state_version(state_data, '1.0.0')
    
    return state_class.model_validate(state_data)
```

### 5. 상태 비교 및 분석

```python
def compare_states(state1, state2):
    """두 상태 간의 차이점 분석"""
    diff = {}
    
    for field in state1.model_fields:
        value1 = getattr(state1, field)
        value2 = getattr(state2, field)
        
        if value1 != value2:
            diff[field] = {
                'before': value1,
                'after': value2
            }
    
    return diff

def analyze_state_evolution(state_history):
    """상태 변화 히스토리 분석"""
    evolution = []
    
    for i in range(1, len(state_history)):
        prev_state = state_history[i-1]
        curr_state = state_history[i]
        
        changes = compare_states(prev_state, curr_state)
        if changes:
            evolution.append({
                'step': i,
                'changes': changes,
                'timestamp': curr_state.get('timestamp')
            })
    
    return evolution
```

## 주요 고려사항

1. **직렬화 호환성**: 커스텀 객체는 JSON 직렬화 가능해야 함
2. **버전 관리**: 상태 스키마 변경 시 마이그레이션 전략 필요
3. **메모리 효율성**: 큰 상태 객체는 메모리 사용량에 주의
4. **보안**: 민감한 정보는 상태에 포함하지 않거나 암호화 필요
5. **성능**: 빈번한 상태 저장/로드는 성능에 영향 가능

이러한 상태 관리 시스템을 통해 AutoGen의 에이전트와 팀은 중단 없는 연속성과 복원력을 제공할 수 있습니다. 