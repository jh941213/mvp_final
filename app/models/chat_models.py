#!/usr/bin/env python3
"""
채팅 모델 정의
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid

class MessageRole(str, Enum):
    """메시지 역할"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class AgentType(str, Enum):
    """에이전트 유형"""
    HR = "hr"
    BULLETIN = "bulletin"
    PROJECT = "project"
    KTDS_INFO = "ktds_info"
    MIDM = "midm"
    ORCHESTRATOR = "orchestrator"
    STORM = "storm"

class ModelConfig(BaseModel):
    """AI 모델 설정"""
    name: str
    display_name: str
    description: str
    provider: str  # "azure_openai", "openai", "gemini", "friendli"
    endpoint: str
    api_key: str
    api_version: str
    context_window: int
    max_tokens: int
    temperature: float = 0.7
    is_available: bool = True
    is_default: bool = False
    capabilities: List[str] = Field(default_factory=list)  # ["chat", "storm", "code", "image"]

# 사용 가능한 모델 목록
AVAILABLE_MODELS = {
    "gpt-4.1": ModelConfig(
        name="gpt-4.1",
        display_name="GPT-4.1",
        description="가장 강력한 범용 AI 모델",
        provider="azure_openai",
        endpoint="https://kdb-rg.openai.azure.com/",
        api_key="5KtFRZPggVvXgnVRlg1KNB4tNJxqtGiu9j97NxYODV1t1CuNgwZfJQQJ99BGACHYHv6XJ3w3AAABACOGSZvs",
        api_version="2024-12-01-preview",
        context_window=128000,
        max_tokens=4096,
        is_default=True,
        capabilities=["chat", "storm", "code", "analysis"]
    ),
    "gpt-4.1-mini": ModelConfig(
        name="gpt-4.1-mini",
        display_name="GPT-4.1 Mini",
        description="빠르고 효율적인 AI 모델",
        provider="azure_openai",
        endpoint="https://kdb-rg.openai.azure.com/",
        api_key="5KtFRZPggVvXgnVRlg1KNB4tNJxqtGiu9j97NxYODV1t1CuNgwZfJQQJ99BGACHYHv6XJ3w3AAABACOGSZvs",
        api_version="2024-12-01-preview",
        context_window=128000,
        max_tokens=4096,
        capabilities=["chat", "storm", "code"]
    ),
    "gpt-4.1-nano": ModelConfig(
        name="gpt-4.1-nano",
        display_name="GPT-4.1 Nano",
        description="경량화된 빠른 AI 모델",
        provider="azure_openai",
        endpoint="https://kdb-rg.openai.azure.com/",
        api_key="5KtFRZPggVvXgnVRlg1KNB4tNJxqtGiu9j97NxYODV1t1CuNgwZfJQQJ99BGACHYHv6XJ3w3AAABACOGSZvs",
        api_version="2024-12-01-preview",
        context_window=128000,
        max_tokens=4096,
        is_default=False,
        capabilities=["chat", "storm"]
    ),
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        display_name="GPT-4o",
        description="멀티모달 지원 고성능 AI 모델",
        provider="azure_openai",
        endpoint="https://kdb-rg.openai.azure.com/",
        api_key="5KtFRZPggVvXgnVRlg1KNB4tNJxqtGiu9j97NxYODV1t1CuNgwZfJQQJ99BGACHYHv6XJ3w3AAABACOGSZvs",
        api_version="2024-12-01-preview",
        context_window=128000,
        max_tokens=4096,
        capabilities=["chat", "storm", "code", "image", "multimodal"]
    ),
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        display_name="GPT-4o Mini",
        description="경량화된 멀티모달 AI 모델",
        provider="azure_openai",
        endpoint="https://kdb-rg.openai.azure.com/",
        api_key="5KtFRZPggVvXgnVRlg1KNB4tNJxqtGiu9j97NxYODV1t1CuNgwZfJQQJ99BGACHYHv6XJ3w3AAABACOGSZvs",
        api_version="2024-12-01-preview",
        context_window=128000,
        max_tokens=4096,
        capabilities=["chat", "storm", "image", "multimodal"]
    ),
    "gemini-2.5-pro": ModelConfig(
        name="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        description="Google의 최신 고성능 멀티모달 AI 모델",
        provider="gemini",
        endpoint="https://generativelanguage.googleapis.com/",
        api_key="AIzaSyDgYXrzEKHHcmQNAnSN4PfOKd2FEYEC8Iw",
        api_version="v1",
        context_window=200000,
        max_tokens=8192,
        capabilities=["chat", "storm", "image", "multimodal", "code"]
    ),
    "gemini-2.5-flash": ModelConfig(
        name="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        description="Google의 빠른 멀티모달 AI 모델",
        provider="gemini",
        endpoint="https://generativelanguage.googleapis.com/",
        api_key="AIzaSyDgYXrzEKHHcmQNAnSN4PfOKd2FEYEC8Iw",
        api_version="v1",
        context_window=100000,
        max_tokens=8192,
        capabilities=["chat", "storm", "image", "multimodal"]
    ),
    "gemini-2.0-flash": ModelConfig(
        name="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        description="Google의 이전 버전 멀티모달 AI 모델",
        provider="gemini",
        endpoint="https://generativelanguage.googleapis.com/",
        api_key="AIzaSyDgYXrzEKHHcmQNAnSN4PfOKd2FEYEC8Iw",
        api_version="v1",
        context_window=100000,
        max_tokens=8192,
        capabilities=["chat", "image", "multimodal"]
    ),
    "midm-2.0": ModelConfig(
        name="midm-2.0",
        display_name="MIDM 2.0",
        description="한국어 특화 AI 모델",
        provider="friendli",
        endpoint="https://inference.friendli.ai/",
        api_key="flp_SdYLO1i2ReY4ew9etGwfrjdAwimTP0DA9HcXyYfm3hh061",
        api_version="v1",
        context_window=32000,
        max_tokens=4096,
        capabilities=["chat", "korean"]
    )
}

def get_available_models() -> Dict[str, ModelConfig]:
    """사용 가능한 모델 목록 반환"""
    return {k: v for k, v in AVAILABLE_MODELS.items() if v.is_available}

def get_default_model() -> ModelConfig:
    """기본 모델 반환"""
    for model in AVAILABLE_MODELS.values():
        if model.is_default:
            return model
    return list(AVAILABLE_MODELS.values())[0]  # 첫 번째 모델을 기본값으로

def get_model_by_name(name: str) -> Optional[ModelConfig]:
    """이름으로 모델 찾기"""
    return AVAILABLE_MODELS.get(name)

class ChatMessage(BaseModel):
    """채팅 메시지"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentInfo(BaseModel):
    """에이전트 정보"""
    name: str
    type: AgentType
    capabilities: List[str] = Field(default_factory=list)
    description: str
    confidence: float = 0.8
    tools_used: List[str] = Field(default_factory=list)
    execution_time: float = 0.0

class StormConfig(BaseModel):
    """STORM 에이전트 설정"""
    enabled: bool = False
    human_in_the_loop: bool = False
    editor_count: int = 3
    max_turns: int = 20
    enable_realtime_progress: bool = True
    enable_interviews: bool = True
    enable_search: bool = True

class StormStats(BaseModel):
    """STORM 진행 통계"""
    total_steps: int = 6
    current_step: int = 0
    completed_interviews: int = 0
    total_interviews: int = 0
    processing_time: float = 0.0
    sections_completed: int = 0

class StormInteraction(BaseModel):
    """STORM Human-in-the-loop 상호작용"""
    type: str  # "editor_review", "outline_review", "section_review"
    content: str
    options: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    session_id: Optional[str] = None
    user_id: str
    context: Dict[str, Any] = Field(default_factory=dict)
    stream: bool = False
    agent_mode: str = "normal"  # "normal", "storm", "storm_interactive"
    storm_config: Optional[StormConfig] = None
    model_name: Optional[str] = None  # 사용할 모델 이름 (예: "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano")

class ChatResponse(BaseModel):
    """채팅 응답"""
    response: str
    session_id: str
    agent_info: AgentInfo
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    processing_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    storm_stats: Optional[StormStats] = None
    storm_interaction: Optional[StormInteraction] = None

class StreamChatResponse(BaseModel):
    """스트리밍 채팅 응답"""
    type: str  # "token", "metadata", "complete", "error", "storm_progress", "storm_interaction"
    content: str
    session_id: str
    agent_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    storm_stats: Optional[StormStats] = None
    storm_interaction: Optional[StormInteraction] = None

class ChatStats(BaseModel):
    """채팅 통계"""
    total_messages: int
    avg_response_time: float
    active_sessions: int
    agent_usage: Dict[str, int]

class MultihopQuery(BaseModel):
    """다중 홉 쿼리"""
    query: str
    hops: List[str]
    context: Dict[str, Any] = Field(default_factory=dict)

class ChatError(BaseModel):
    """채팅 오류"""
    error_type: str
    message: str
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class StormRequest(BaseModel):
    """STORM 요청"""
    topic: str
    session_id: Optional[str] = None
    user_id: str
    config: StormConfig = Field(default_factory=StormConfig)
    enable_human_loop: bool = False
    stream: bool = False

class StormResponse(BaseModel):
    """STORM 응답"""
    result: str
    session_id: str
    processing_time: float
    stats: StormStats
    outline: Optional[Dict[str, Any]] = None
    editors: Optional[List[Dict[str, Any]]] = None
    sections: Optional[Dict[str, str]] = None

class StormStreamResponse(BaseModel):
    """STORM 스트리밍 응답"""
    type: str  # "progress", "interaction", "result", "error"
    content: str
    session_id: str
    step: int
    total_steps: int
    stats: StormStats
    interaction: Optional[StormInteraction] = None

class StormInteractiveRequest(BaseModel):
    """STORM 인터랙티브 요청"""
    topic: str
    session_id: Optional[str] = None
    user_id: str
    config: StormConfig = Field(default_factory=StormConfig)

class StormInteractiveResponse(BaseModel):
    """STORM 인터랙티브 응답"""
    type: str  # "interaction_required", "progress", "complete"
    content: str
    session_id: str
    step: int = 0
    total_steps: int = 6
    interaction: Optional[StormInteraction] = None
    stats: StormStats = Field(default_factory=StormStats)
    result: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class StormHumanInteraction(BaseModel):
    """STORM Human-in-the-loop 상호작용"""
    session_id: str
    interaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    content: str
    options: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    step: int = 0
    title: Optional[str] = None

class StormHumanResponse(BaseModel):
    """STORM Human-in-the-loop 응답"""
    session_id: str
    interaction_id: str
    action: str = "approve"  # "approve", "reject", "modify"
    feedback: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict) 