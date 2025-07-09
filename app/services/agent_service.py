#!/usr/bin/env python3
"""
에이전트 서비스
멀티에이전트 시스템과 세션 관리자를 래핑합니다.
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import time
import uuid

# backend/agent 디렉토리를 sys.path에 추가
backend_agent_path = str(Path(__file__).parent.parent.parent / "backend" / "agent")
if backend_agent_path not in sys.path:
    sys.path.insert(0, backend_agent_path)

from app.core.logging_config import get_logger
from app.core.config import get_settings
from app.models.chat_models import get_model_by_name, get_default_model
from app.services.storm_service import StormService

logger = get_logger("agent_service")

# 백엔드 멀티에이전트 시스템 임포트
BACKEND_AVAILABLE = False
try:
    import multi_agent_system
    from multi_agent_system import get_magentic_system, KTDSMagenticOneSystem
    from session_manager import SessionManager as BackendSessionManager
    from conversation_context import ConversationManager
    BACKEND_AVAILABLE = True
    logger.info("✅ Backend multi-agent system imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Backend system not available: {e}")
    BACKEND_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ Unexpected error importing backend system: {e}")
    BACKEND_AVAILABLE = False

class AgentService:
    """
    멀티에이전트 서비스 클래스
    ConversationManager 중심의 통합 세션 관리 및 STORM 에이전트 지원
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.initialized = False
        self.multi_agent_system = None
        self.conversation_manager = None
        self.session_manager = None  # 백워드 호환성을 위해 유지, 하지만 최소 사용
        self.storm_service = None    # STORM 서비스 추가
        self.agent_count = 0

    async def initialize(self):
        """서비스 초기화"""
        if self.initialized:
            logger.info("Agent Service already initialized")
            return
        
        try:
            logger.info("Initializing Agent Service...")
            
            # 멀티에이전트 시스템 초기화
            await self._initialize_multi_agent_system()
            
            # 백워드 호환성을 위한 최소 SessionManager 초기화
            await self._initialize_minimal_session_manager()
            
            # ConversationManager 초기화 (메인 관리자)
            await self._initialize_conversation_manager()
            
            # STORM 서비스 초기화
            await self._initialize_storm_service()
            
            self.initialized = True
            logger.info("Agent Service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Agent Service", error=str(e))
            raise

    async def _initialize_multi_agent_system(self, model_name: str = "gpt-4.1"):
        """멀티에이전트 시스템 초기화"""
        try:
            if BACKEND_AVAILABLE:
                logger.info(f"🚀 Initializing KTDS MagenticOne System with model: {model_name}...")
                
                self.multi_agent_system = get_magentic_system(verbose=True, model_name=model_name)
                logger.info("✅ MagenticOne system initialized successfully")
                
                if self.multi_agent_system:
                    # 에이전트 개수 설정
                    self.agent_count = getattr(self.multi_agent_system, 'agent_count', 0)
                    logger.info("✅ KTDS MagenticOne system ready",
                              agent_count=self.agent_count,
                              architecture=getattr(self.multi_agent_system, 'architecture', []),
                              model=getattr(self.multi_agent_system, 'model_name', 'gpt-4'),
                              system_name=getattr(self.multi_agent_system, 'system_name', 'KTDS MagenticOne'),
                              total_tools=getattr(self.multi_agent_system, 'total_tools', 0))
                
        except Exception as e:
            logger.error("Failed to initialize multi-agent system", error=str(e))
            self.multi_agent_system = None

    async def _initialize_minimal_session_manager(self):
        """백워드 호환성을 위한 최소 SessionManager (ConversationManager가 메인)"""
        try:
            if BACKEND_AVAILABLE:
                logger.info("Initializing minimal Session Manager for compatibility...")
                
                # SessionManager는 이제 최소 기능만 제공
                self.session_manager = BackendSessionManager()
                logger.info("✅ Minimal Session Manager initialized successfully")
                
                if self.session_manager:
                    stats = self.session_manager.get_session_stats()
                    logger.info("Session Manager ready",
                              active_sessions=stats.get("total_active_sessions", 0),
                              manager_type=stats.get("manager_type", "unknown"))
                              
        except Exception as e:
            logger.error("Failed to initialize session manager", error=str(e))
            self.session_manager = None
    
    async def _initialize_conversation_manager(self):
        """ConversationManager 초기화 (메인 세션 관리자)"""
        try:
            if BACKEND_AVAILABLE:
                logger.info("Initializing Conversation Manager (Main Session Manager)...")
                
                # KTDS 시스템 메시지 설정
                system_message = """당신은 KTDS(한국기업데이터)의 AI 어시스턴트입니다. 
사용자의 질문에 대해 정확하고 도움이 되는 답변을 제공하며, 이전 대화 내용을 기억하고 연관된 답변을 제공합니다.
회사 정보, 기술 지원, 일반적인 업무 문의에 전문적으로 대응합니다."""
                
                self.conversation_manager = ConversationManager(
                    default_buffer_size=20,  # 최근 20개 메시지 유지
                    default_system_message=system_message,
                    session_manager=self.session_manager  # Azure SQL 저장 지원
                )
                logger.info("✅ Conversation Manager initialized successfully")
                
                if self.conversation_manager:
                    stats = self.conversation_manager.get_session_stats()
                    logger.info("Conversation Manager ready",
                              active_sessions=stats.get("total_active_sessions", 0),
                              buffer_size=stats.get("default_buffer_size", 0))
                              
        except Exception as e:
            logger.error("Failed to initialize conversation manager", error=str(e))
            self.conversation_manager = None

    async def _initialize_storm_service(self):
        """STORM 서비스 초기화"""
        try:
            logger.info("Initializing STORM Service...")
            
            self.storm_service = StormService()
            await self.storm_service.initialize()
            
            logger.info("✅ STORM Service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize STORM service", error=str(e))
            self.storm_service = None

    def _create_model_client(self, model_name: Optional[str] = None):
        """동적 모델 클라이언트 생성"""
        try:
            # 모델 설정 가져오기
            if model_name:
                model_config = get_model_by_name(model_name)
                if not model_config:
                    logger.warning(f"Model {model_name} not found, using default")
                    model_config = get_default_model()
            else:
                model_config = get_default_model()
            
            logger.info(f"Creating model client for {model_config.name}")
            
            # 프로바이더별 클라이언트 생성
            if model_config.provider == "azure_openai":
                from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
                
                return AzureOpenAIChatCompletionClient(
                    model=model_config.name,
                    api_key=model_config.api_key,
                    azure_endpoint=model_config.endpoint,
                    api_version=model_config.api_version,
                    temperature=model_config.temperature
                )
            
            elif model_config.provider == "gemini":
                # Gemini 클라이언트 생성 (향후 구현)
                logger.warning("Gemini provider not yet implemented, using default Azure OpenAI")
                default_config = get_default_model()
                from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
                
                return AzureOpenAIChatCompletionClient(
                    model=default_config.name,
                    api_key=default_config.api_key,
                    azure_endpoint=default_config.endpoint,
                    api_version=default_config.api_version,
                    temperature=default_config.temperature
                )
            
            elif model_config.provider == "friendli":
                # Friendli 클라이언트 생성 (향후 구현)
                logger.warning("Friendli provider not yet implemented, using default Azure OpenAI")
                default_config = get_default_model()
                from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
                
                return AzureOpenAIChatCompletionClient(
                    model=default_config.name,
                    api_key=default_config.api_key,
                    azure_endpoint=default_config.endpoint,
                    api_version=default_config.api_version,
                    temperature=default_config.temperature
                )
            
            else:
                logger.error(f"Unsupported provider: {model_config.provider}")
                raise ValueError(f"Unsupported provider: {model_config.provider}")
                
        except Exception as e:
            logger.error(f"Failed to create model client: {str(e)}")
            # 폴백으로 기본 모델 사용
            default_config = get_default_model()
            from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
            
            return AzureOpenAIChatCompletionClient(
                model=default_config.name,
                api_key=default_config.api_key,
                azure_endpoint=default_config.endpoint,
                api_version=default_config.api_version,
                temperature=default_config.temperature
            )

    async def process_message(
        self,
        message: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        agent_mode: str = "normal",
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        메시지 처리 (ConversationManager 중심 + STORM 모드 지원 + 대화형 설정 + STORM 상호작용)
        """
        if not self.initialized:
            await self.initialize()
        
        # 모델이 지정된 경우 새로운 멀티에이전트 시스템 초기화
        if model_name and model_name != getattr(self.multi_agent_system, 'model_name', None):
            logger.info(f"🔄 Switching model to: {model_name}")
            await self._initialize_multi_agent_system(model_name)
        
        try:
            logger.info("Processing message",
                       message_length=len(message),
                       session_id=session_id,
                       user_id=user_id,
                       agent_mode=agent_mode)
            
            # 대화 컨텍스트 가져오기
            conv_context = None
            if self.conversation_manager:
                conv_context = self.conversation_manager.get_or_create_context(session_id)
            
            # STORM 상호작용 처리 (진행 중인 STORM 연구의 Human-in-the-Loop 응답)
            if agent_mode == "normal" and conv_context and self.storm_service:
                # 진행 중인 STORM 상호작용 확인
                if session_id in self.storm_service.human_interactions:
                    interaction = self.storm_service.human_interactions[session_id]
                    
                    # 사용자 메시지를 컨텍스트에 추가
                    conv_context.add_user_message(
                        content=message,
                        source=user_id,
                        metadata=context
                    )
                    
                    # 응답 처리
                    response_processed = await self._process_storm_interaction_response(
                        session_id, interaction, message, conv_context
                    )
                    
                    if response_processed:
                        return response_processed
            
            # STORM 대화형 설정 처리
            if agent_mode == "normal" and conv_context:
                # 이전 대화에서 STORM 연구자 수를 물어봤는지 확인
                last_messages = conv_context.get_recent_messages(2)
                if last_messages:
                    last_assistant_message = None
                    for msg in reversed(last_messages):
                        # msg가 딕셔너리인지 객체인지 확인
                        if isinstance(msg, dict):
                            role = msg.get("role", "")
                            content = msg.get("content", "")
                        else:
                            role = getattr(msg, 'role', '')
                            if hasattr(role, 'value'):
                                role = role.value
                            content = getattr(msg, 'content', '')
                        
                        if role == "assistant":
                            last_assistant_message = content
                            break
                    
                    # 연구자 수 질문에 대한 답변인지 확인
                    if (last_assistant_message and 
                        ("몇 명의 연구자" in last_assistant_message or "몇 명으로" in last_assistant_message) and
                        message.strip().isdigit()):
                        
                        editor_count = int(message.strip())
                        if 1 <= editor_count <= 8:
                            # 사용자 메시지를 컨텍스트에 추가
                            conv_context.add_user_message(
                                content=message,
                                source=user_id,
                                metadata=context
                            )
                            
                            # STORM 주제 찾기 (최근 메시지에서)
                            storm_topic = self._extract_storm_topic_from_history(last_messages)
                            
                            # 대화형 STORM 연구 시작
                            if storm_topic:
                                return await self._start_conversational_storm_research(
                                    storm_topic, editor_count, user_id, session_id, conv_context
                                )
                        else:
                            # 잘못된 숫자 범위
                            error_response = f"❌ 연구자 수는 1명에서 8명 사이여야 합니다. 현재 입력: {editor_count}명\n\n다시 입력해주세요 (1-8):"
                            conv_context.add_user_message(content=message, source=user_id, metadata=context)
                            conv_context.add_assistant_message(content=error_response, source="STORM_Setup_Agent", metadata={"storm_setup_error": True})
                            
                            return {
                                "response": error_response,
                                "session_id": session_id,
                                "agent_name": "STORM_Setup_Agent",
                                "agent_type": "storm",
                                "agent_description": "STORM 설정 에이전트",
                                "confidence": 0.9,
                                "tools_used": [],
                                "execution_time": 0.0,
                                "metadata": {"storm_setup_error": True}
                            }
                
                # STORM 연구 키워드 감지 (새로운 요청)
                storm_keywords = ["연구해줘", "연구하고", "연구 해줘", "리서치", "조사해줘", "분석해줘", "정리해줘", "써줘", "작성해줘"]
                if any(keyword in message.lower() for keyword in storm_keywords):
                    # 주제 추출
                    topic = self._extract_topic_from_message(message)
                    
                    if topic:
                        # 사용자 메시지를 컨텍스트에 추가
                        conv_context.add_user_message(
                            content=message,
                            source=user_id,
                            metadata=context
                        )
                        
                        # 연구자 수 질문
                        question_response = f"🎯 **STORM 연구 모드 감지**\n\n" + \
                                          f"**주제**: {topic}\n\n" + \
                                          f"몇 명의 연구자로 진행할까요? (1-8명)\n" + \
                                          f"예: 3, 5, 7"
                        
                        # 질문을 컨텍스트에 추가
                        conv_context.add_assistant_message(
                            content=question_response,
                            source="STORM_Setup_Agent",
                            metadata={"storm_setup_question": True, "storm_topic": topic}
                        )
                        
                        return {
                            "response": question_response,
                            "session_id": session_id,
                            "agent_name": "STORM_Setup_Agent",
                            "agent_type": "storm",
                            "agent_description": "STORM 설정 에이전트",
                            "confidence": 0.9,
                            "tools_used": [],
                            "execution_time": 0.0,
                            "metadata": {"storm_setup_question": True, "storm_topic": topic}
                        }
            
            # 기존 STORM 모드 처리 (직접 호출)
            if agent_mode == "storm":
                if not self.storm_service:
                    raise ValueError("STORM service not available")
                
                # 컨텍스트에서 STORM 설정 추출
                storm_config = None
                if context and "storm_config" in context:
                    from app.models.chat_models import StormConfig
                    storm_config = StormConfig(**context["storm_config"])
                
                return await self.storm_service.process_storm_research(
                    topic=message,
                    user_id=user_id,
                    session_id=session_id,
                    config=storm_config
                )
            
            # 일반 모드 처리
            if not self.multi_agent_system:
                raise ValueError("Multi-agent system not available")
            
            # ConversationManager로 멀티턴 대화 처리
            result = await self._process_with_conversation_manager(
                message, user_id, session_id, context
            )
            
            return result
            
        except Exception as e:
            logger.error("Failed to process message",
                        error=str(e),
                        session_id=session_id,
                        user_id=user_id,
                        agent_mode=agent_mode)
            raise

    async def _start_conversational_storm_research(
        self,
        storm_topic: str,
        editor_count: int,
        user_id: str,
        session_id: str,
        conv_context
    ) -> Dict[str, Any]:
        """
        대화형 STORM 연구 시작 (Human-in-the-Loop 지원)
        """
        from app.models.chat_models import StormConfig
        
        # STORM 설정 생성
        storm_config = StormConfig(
            enabled=True,
            editor_count=editor_count,
            human_in_the_loop=True,
            enable_search=True,
            enable_interviews=True,
            enable_realtime_progress=True
        )
        
        # 시작 메시지 생성
        start_response = f"🌩️ **STORM 연구 시작**\n\n" + \
                        f"**주제**: {storm_topic}\n" + \
                        f"**연구자 수**: {editor_count}명\n" + \
                        f"**모드**: Human-in-the-Loop 활성화\n\n" + \
                        f"연구를 시작하겠습니다...\n\n" + \
                        f"💡 **안내**: 연구 과정에서 아웃라인 검토, 편집자 승인 등의 단계마다 확인을 요청할 예정입니다."
        
        # 시작 메시지를 컨텍스트에 추가
        conv_context.add_assistant_message(
            content=start_response,
            source="STORM_Setup_Agent",
            metadata={"storm_setup": True, "storm_topic": storm_topic}
        )
        
        try:
            # 백그라운드에서 STORM 연구 시작
            asyncio.create_task(self._run_background_storm_research(
                storm_topic, editor_count, user_id, session_id, storm_config
            ))
            
            return {
                "response": start_response,
                "session_id": session_id,
                "agent_name": "STORM_Setup_Agent",
                "agent_type": "storm",
                "agent_description": "대화형 STORM 연구 시작",
                "confidence": 0.95,
                "tools_used": ["storm_initialization"],
                "execution_time": 0.0,
                "metadata": {
                    "storm_setup": True,
                    "storm_topic": storm_topic,
                    "editor_count": editor_count,
                    "human_in_the_loop": True
                }
            }
            
        except Exception as e:
            logger.error("Failed to start conversational STORM research", error=str(e))
            raise

    async def _run_background_storm_research(
        self,
        topic: str,
        editor_count: int,
        user_id: str,
        session_id: str,
        storm_config
    ):
        """
        백그라운드에서 STORM 연구 실행 (Human-in-the-Loop 지원)
        """
        try:
            # 커스텀 STORM 시스템 생성
            from backend.agent.storm_research import ParallelStormResearchSystem
            
            custom_storm = ParallelStormResearchSystem(max_workers=editor_count)
            
            # 대화형 콜백 설정
            custom_storm.human_interaction_callback = lambda interaction_type, content, options=None: asyncio.create_task(
                self._handle_conversational_storm_interaction(
                    session_id, interaction_type, content, options
                )
            )
            
            # STORM 연구 실행
            result = await custom_storm.run_parallel_storm_research(
                topic=topic,
                enable_human_loop=True
            )
            
            # 완료 메시지를 대화 컨텍스트에 추가
            if self.conversation_manager:
                conv_context = self.conversation_manager.get_or_create_context(session_id)
                completion_message = f"✅ **STORM 연구 완료**\n\n{result}"
                conv_context.add_assistant_message(
                    content=completion_message,
                    source="STORM_Research_Agent",
                    metadata={"storm_completed": True}
                )
            
        except Exception as e:
            logger.error("Background STORM research failed", error=str(e))
            # 오류 메시지를 대화 컨텍스트에 추가
            if self.conversation_manager:
                conv_context = self.conversation_manager.get_or_create_context(session_id)
                error_message = f"❌ **STORM 연구 중 오류 발생**\n\n{str(e)}"
                conv_context.add_assistant_message(
                    content=error_message,
                    source="STORM_Research_Agent",
                    metadata={"storm_error": True}
                )

    async def _handle_conversational_storm_interaction(
        self,
        session_id: str,
        interaction_type: str,
        content: str,
        options: List[str] = None
    ):
        """
        대화형 STORM 상호작용 처리
        """
        try:
            # 상호작용 정보를 STORM 서비스에 등록
            interaction_id = str(uuid.uuid4())
            
            if not hasattr(self.storm_service, 'human_interactions'):
                self.storm_service.human_interactions = {}
            
            self.storm_service.human_interactions[session_id] = {
                "interaction_id": interaction_id,
                "type": interaction_type,
                "content": content,
                "options": options or [],
                "timestamp": time.time(),
                "sent": False,
                "response": None
            }
            
            # 대화 컨텍스트에 상호작용 메시지 추가
            if self.conversation_manager:
                conv_context = self.conversation_manager.get_or_create_context(session_id)
                
                # 상호작용 유형별 메시지 생성
                if interaction_type == "editor_review":
                    interaction_message = f"👥 **편집자 검토**\n\n{content}\n\n승인하시겠습니까? (승인/거부/수정)"
                elif interaction_type == "outline_review":
                    interaction_message = f"📋 **아웃라인 검토**\n\n{content}\n\n아웃라인을 승인하시겠습니까? (승인/거부/수정)"
                elif interaction_type == "section_review":
                    interaction_message = f"📝 **섹션 검토**\n\n{content}\n\n섹션을 승인하시겠습니까? (승인/거부/수정)"
                else:
                    interaction_message = f"🔄 **{interaction_type} 검토**\n\n{content}\n\n진행하시겠습니까? (승인/거부)"
                
                conv_context.add_assistant_message(
                    content=interaction_message,
                    source="STORM_Interaction_Agent",
                    metadata={
                        "storm_interaction": True,
                        "interaction_type": interaction_type,
                        "interaction_id": interaction_id
                    }
                )
            
            # 응답 대기
            return await self._wait_for_storm_interaction_response(session_id, interaction_id)
            
        except Exception as e:
            logger.error("Failed to handle conversational STORM interaction", error=str(e))
            return {"action": "approve", "feedback": "오류로 인한 자동 승인"}

    async def _wait_for_storm_interaction_response(self, session_id: str, interaction_id: str, timeout: int = 300):
        """
        STORM 상호작용 응답 대기
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if session_id in self.storm_service.human_interactions:
                interaction = self.storm_service.human_interactions[session_id]
                if interaction.get("response"):
                    return interaction["response"]
            
            await asyncio.sleep(1)
        
        # 타임아웃 시 자동 승인
        return {"action": "approve", "feedback": "타임아웃으로 인한 자동 승인"}

    async def _process_storm_interaction_response(
        self,
        session_id: str,
        interaction: Dict[str, Any],
        message: str,
        conv_context
    ) -> Optional[Dict[str, Any]]:
        """
        STORM 상호작용 응답 처리
        """
        try:
            # 사용자 응답 분석
            message_lower = message.lower().strip()
            
            if any(word in message_lower for word in ["승인", "ok", "좋다", "진행", "예", "yes"]):
                action = "approve"
                feedback = "승인"
            elif any(word in message_lower for word in ["거부", "no", "안된다", "아니다", "취소"]):
                action = "reject"
                feedback = "거부"
            elif any(word in message_lower for word in ["수정", "변경", "고치다", "바꾸다"]):
                action = "modify"
                feedback = message
            else:
                action = "approve"
                feedback = message
            
            # 응답 저장
            interaction["response"] = {
                "action": action,
                "feedback": feedback,
                "timestamp": time.time()
            }
            
            # 응답 확인 메시지 생성
            if action == "approve":
                response_message = f"✅ **{interaction['type']} 승인됨**\n\n계속 진행하겠습니다..."
            elif action == "reject":
                response_message = f"❌ **{interaction['type']} 거부됨**\n\n다시 검토하겠습니다..."
            else:
                response_message = f"🔄 **{interaction['type']} 수정 요청**\n\n피드백: {feedback}\n\n수정 후 다시 진행하겠습니다..."
            
            # 응답 메시지를 컨텍스트에 추가
            conv_context.add_assistant_message(
                content=response_message,
                source="STORM_Interaction_Agent",
                metadata={
                    "storm_interaction_response": True,
                    "action": action,
                    "interaction_type": interaction["type"]
                }
            )
            
            return {
                "response": response_message,
                "session_id": session_id,
                "agent_name": "STORM_Interaction_Agent",
                "agent_type": "storm",
                "agent_description": "STORM 상호작용 응답 처리",
                "confidence": 0.95,
                "tools_used": ["storm_interaction"],
                "execution_time": 0.0,
                "metadata": {
                    "storm_interaction_response": True,
                    "action": action,
                    "interaction_type": interaction["type"]
                }
            }
            
        except Exception as e:
            logger.error("Failed to process STORM interaction response", error=str(e))
            return None

    async def _process_with_conversation_manager(
        self,
        message: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        ConversationManager 중심의 메시지 처리
        """
        try:
            logger.info("🎯 Processing with ConversationManager-based system")
            
            # 대화 컨텍스트 가져오기 또는 생성
            conv_context = self.conversation_manager.get_or_create_context(session_id)
            
            # 사용자 메시지를 컨텍스트에 추가
            conv_context.add_user_message(
                content=message,
                source=user_id,
                metadata=context
            )
            
            # 대화 히스토리 준비
            conversation_history = conv_context.get_context_for_llm()
            
            # 현재 세션 상태 로깅
            summary = conv_context.get_conversation_summary()
            logger.info("Processing with ConversationManager",
                       session_id=session_id,
                       context_messages=f"{summary['user_messages']} users, {summary['assistant_messages']} assistants")
            
            # 멀티에이전트 시스템 처리
            if asyncio.iscoroutinefunction(self.multi_agent_system.process_query):
                response = await self.multi_agent_system.process_query(
                    query=message,
                    user_id=user_id,
                    session_id=session_id,
                    conversation_history=conversation_history
                )
            else:
                response = self.multi_agent_system.process_query(
                    query=message,
                    user_id=user_id,
                    session_id=session_id,
                    conversation_history=conversation_history
                )
            
            # 응답 처리
            if asyncio.iscoroutine(response):
                response = await response
            
            response_text = response if isinstance(response, str) else str(response)
            
            # 결과 구성
            result = {
                "response": response_text,
                "session_id": session_id,
                "agent_name": "KTDS_ConversationManager_Agent",
                "agent_type": "conversation_orchestrator",
                "agent_description": "ConversationManager 기반 통합 에이전트",
                "confidence": 0.9,
                "tools_used": ["conversation_context", "azure_sql_storage"],
                "execution_time": 0.0,
                "metadata": {
                    "conversation_manager": True,
                    "azure_sql_storage": summary.get("azure_sql_enabled", False),
                    "session_messages": summary.get("total_messages", 0),
                    "buffer_size": summary.get("buffer_size", 20)
                }
            }
            
            # 어시스턴트 응답을 컨텍스트에 추가
            conv_context.add_assistant_message(
                content=response_text,
                source="KTDS_ConversationManager_Agent",
                metadata=result.get("metadata", {})
            )
            
            logger.info("✅ ConversationManager processing completed successfully")
            return result
            
        except Exception as e:
            logger.error("ConversationManager processing failed", error=str(e))
            raise

    async def process_message_stream(
        self,
        message: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        agent_mode: str = "normal"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        스트리밍 메시지 처리 (STORM 모드 지원 + 실시간 로그)
        """
        try:
            logger.info("Processing message stream", 
                       user_id=user_id, 
                       session_id=session_id,
                       agent_mode=agent_mode)
            
            if not self.initialized:
                raise RuntimeError("Agent service not initialized")

            # 시작 로그 전송
            yield {
                "type": "log",
                "level": "info",
                "message": f"🚀 에이전트 처리 시작 - 모드: {agent_mode}",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {"stage": "initialization", "agent_mode": agent_mode}
            }

            # STORM 모드 스트리밍 처리
            if agent_mode == "storm":
                if not self.storm_service:
                    yield {
                        "type": "log",
                        "level": "error",
                        "message": "❌ STORM 서비스를 사용할 수 없습니다",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    raise ValueError("STORM service not available")
                
                yield {
                    "type": "log",
                    "level": "info",
                    "message": "🌩️ STORM 연구 에이전트 초기화 중...",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"stage": "storm_initialization"}
                }
                
                # 컨텍스트에서 STORM 설정 추출
                storm_config = None
                enable_human_loop = False
                
                if context:
                    if "storm_config" in context:
                        from app.models.chat_models import StormConfig
                        storm_config = StormConfig(**context["storm_config"])
                    enable_human_loop = context.get("enable_human_loop", False)
                
                yield {
                    "type": "log",
                    "level": "info",
                    "message": f"⚙️ STORM 설정 완료 - 상호작용 모드: {'활성화' if enable_human_loop else '비활성화'}",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "stage": "storm_config",
                        "human_loop": enable_human_loop,
                        "config": storm_config.__dict__ if storm_config else None
                    }
                }
                
                # 인터랙티브 모드인 경우 새로운 메서드 사용
                if enable_human_loop:
                    yield {
                        "type": "log",
                        "level": "info",
                        "message": "🔄 상호작용 STORM 연구 시작",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    async for chunk in self.storm_service.process_storm_interactive(
                        topic=message,
                        user_id=user_id,
                        session_id=session_id,
                        config=storm_config
                    ):
                        # STORM 이벤트도 로그 형태로 전송
                        chunk_type = chunk.get("type", "storm_progress")
                        yield {
                            "type": "log",
                            "level": "info",
                            "message": f"🌩️ STORM: {chunk.get('content', '')}",
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat(),
                            "metadata": {
                                "stage": "storm_processing",
                                "storm_type": chunk_type,
                                "step": chunk.get("step", 0),
                                "total_steps": chunk.get("total_steps", 6)
                            }
                        }
                        yield chunk
                else:
                    # 일반 STORM 모드 처리
                    yield {
                        "type": "log",
                        "level": "info",
                        "message": "📝 일반 STORM 연구 진행 중...",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    response = await self.storm_service.process_storm_research(
                        topic=message,
                        user_id=user_id,
                        session_id=session_id,
                        config=storm_config
                    )
                    
                    yield {
                        "type": "log",
                        "level": "success",
                        "message": "✅ STORM 연구 완료",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "stage": "storm_complete",
                            "processing_time": response.get("execution_time", 0)
                        }
                    }
                    
                    # 결과를 스트리밍 형태로 변환
                    yield {
                        "type": "storm_complete",
                        "content": response.get("response", ""),
                        "session_id": session_id,
                        "metadata": response.get("metadata", {})
                    }
                return

            # 일반 모드 스트리밍 처리
            yield {
                "type": "log",
                "level": "info",
                "message": "🤖 일반 에이전트 처리 시작",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {"stage": "normal_processing"}
            }
            
            # 세션에 사용자 메시지 저장
            if self.session_manager:
                yield {
                    "type": "log",
                    "level": "debug",
                    "message": "💾 사용자 메시지 저장 중...",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                await self._save_user_message(session_id, user_id, message)

            # ConversationManager 컨텍스트 확인
            if self.conversation_manager:
                yield {
                    "type": "log",
                    "level": "info",
                    "message": "🔍 대화 컨텍스트 확인 중...",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                conv_context = self.conversation_manager.get_or_create_context(session_id)
                if conv_context:
                    summary = conv_context.get_conversation_summary()
                    yield {
                        "type": "log",
                        "level": "info",
                        "message": f"📊 대화 컨텍스트 로드됨 - 메시지 수: {summary.get('total_messages', 0)}",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "stage": "context_loaded",
                            "message_count": summary.get('total_messages', 0),
                            "user_messages": summary.get('user_messages', 0),
                            "assistant_messages": summary.get('assistant_messages', 0)
                        }
                    }

            # 멀티에이전트 시스템 처리
            if self.multi_agent_system:
                yield {
                    "type": "log",
                    "level": "info",
                    "message": "🎯 멀티에이전트 시스템 처리 중...",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"stage": "multi_agent_processing"}
                }
                
                # 스트리밍 지원 여부 확인
                if hasattr(self.multi_agent_system, 'process_stream'):
                    yield {
                        "type": "log",
                        "level": "info",
                        "message": "🌊 스트리밍 모드로 에이전트 처리",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    async for chunk in self.multi_agent_system.process_stream(
                        message, user_id, session_id, context
                    ):
                        yield chunk
                else:
                    yield {
                        "type": "log",
                        "level": "info",
                        "message": "📝 일반 모드로 에이전트 처리",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # 기본 스트리밍 구현 (시뮬레이션)
                    response = await self.process_message(message, user_id, session_id, context, agent_mode)
                    
                    yield {
                        "type": "log",
                        "level": "success",
                        "message": f"✅ 에이전트 응답 생성 완료 - 길이: {len(response.get('response', ''))}자",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "stage": "response_generated",
                            "response_length": len(response.get('response', '')),
                            "agent_type": response.get('agent_type', 'orchestrator')
                        }
                    }
                    
                    # 응답을 청크로 나누어 스트리밍
                    response_text = response.get("response", "")
                    if response_text:
                        words = response_text.split()
                        
                        yield {
                            "type": "log",
                            "level": "info",
                            "message": f"📤 응답 스트리밍 시작 - {len(words)}개 단어",
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        for i, word in enumerate(words):
                            await asyncio.sleep(0.05)  # 스트리밍 효과 (더 빠르게)
                            yield {
                                "type": "token",
                                "content": word + " ",
                                "agent_type": response.get("agent_type", "orchestrator"),
                                "session_id": session_id,
                                "is_final": i == len(words) - 1,
                                "progress": (i + 1) / len(words)
                            }
                            
                            # 10단어마다 진행 로그
                            if (i + 1) % 10 == 0:
                                yield {
                                    "type": "log",
                                    "level": "debug",
                                    "message": f"📤 진행률: {((i + 1) / len(words) * 100):.1f}%",
                                    "session_id": session_id,
                                    "timestamp": datetime.now().isoformat()
                                }
                        
                        yield {
                            "type": "log",
                            "level": "success",
                            "message": "🎉 응답 스트리밍 완료",
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
            else:
                yield {
                    "type": "log",
                    "level": "warning",
                    "message": "⚠️ 멀티에이전트 시스템을 사용할 수 없습니다",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 간단한 응답 제공
                simple_response = f"죄송합니다. 현재 에이전트 시스템이 초기화되지 않았습니다. 메시지: {message}"
                yield {
                    "type": "token",
                    "content": simple_response,
                    "agent_type": "fallback",
                    "session_id": session_id,
                    "is_final": True
                }
                    
        except Exception as e:
            logger.error("Error in stream processing", 
                        error=str(e),
                        session_id=session_id,
                        agent_mode=agent_mode)
            
            yield {
                "type": "log",
                "level": "error",
                "message": f"❌ 처리 중 오류 발생: {str(e)}",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {"stage": "error", "error": str(e)}
            }
            
            yield {
                "type": "error",
                "content": f"처리 중 오류가 발생했습니다: {str(e)}",
                "error": str(e),
                "agent_type": "error",
                "session_id": session_id
            }

    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """세션의 대화 기록 조회 (ConversationManager 중심)"""
        try:
            if self.conversation_manager:
                # ConversationManager에서 히스토리 조회 (Azure SQL 포함)
                return self.conversation_manager.get_conversation_history(session_id)
            else:
                return []
        except Exception as e:
            logger.error("Failed to get conversation history", 
                        error=str(e),
                        session_id=session_id)
            return []

    async def clear_session(self, session_id: str):
        """세션 삭제 (ConversationManager 중심)"""
        try:
            if self.conversation_manager:
                # ConversationManager에서 세션 정리 (Azure SQL 포함)
                self.conversation_manager.clear_session(session_id)
                logger.info("Session cleared via ConversationManager", session_id=session_id)
            
            # 백워드 호환성을 위해 SessionManager도 정리
            if self.session_manager and hasattr(self.session_manager, 'end_session'):
                self.session_manager.end_session(session_id)
                logger.info("Session cleared via SessionManager (compatibility)", session_id=session_id)
                
        except Exception as e:
            logger.error("Failed to clear session", 
                        error=str(e),
                        session_id=session_id)
            raise

    async def get_session_stats(self) -> Dict[str, Any]:
        """통합 세션 통계 (ConversationManager 중심 + STORM 지원)"""
        try:
            stats = {
                "conversation_manager": {},
                "session_manager": {},
                "storm_service": {},
                "service_status": {
                    "initialized": self.initialized,
                    "backend_available": BACKEND_AVAILABLE,
                    "agent_count": self.agent_count,
                    "storm_available": self.storm_service is not None
                }
            }
            
            # ConversationManager 통계 (메인)
            if self.conversation_manager:
                stats["conversation_manager"] = self.conversation_manager.get_session_stats()
            
            # SessionManager 통계 (호환성)
            if self.session_manager:
                stats["session_manager"] = self.session_manager.get_session_stats()
            
            # STORM 서비스 통계
            if self.storm_service:
                stats["storm_service"] = await self.storm_service.get_storm_capabilities()
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get session stats", error=str(e))
            return {"error": str(e)}

    async def get_user_chat_stats(self, user_id: str) -> Dict[str, Any]:
        """사용자별 채팅 통계"""
        try:
            # ConversationManager 기반 통계
            if self.conversation_manager:
                all_sessions = self.conversation_manager.get_active_sessions()
                user_sessions = []
                total_messages = 0
                storm_usage = 0
                
                for session_id in all_sessions:
                    history = self.conversation_manager.get_conversation_history(session_id)
                    if history:
                        # 사용자 메시지 확인
                        user_found = False
                        for msg in history:
                            if isinstance(msg, dict):
                                source = msg.get("source", "")
                                metadata = msg.get("metadata", {})
                            else:
                                source = getattr(msg, 'source', '')
                                metadata = getattr(msg, 'metadata', {})
                            
                            if source == user_id:
                                user_found = True
                                break
                        
                        if user_found:
                            user_sessions.append(session_id)
                            total_messages += len(history)
                            
                            # STORM 사용 통계 (메타데이터에서 확인)
                            for msg in history:
                                if isinstance(msg, dict):
                                    metadata = msg.get("metadata", {})
                                else:
                                    metadata = getattr(msg, 'metadata', {})
                                
                                if metadata.get("storm_research", False):
                                    storm_usage += 1
                
                return {
                    "user_id": user_id,
                    "total_sessions": len(user_sessions),
                    "active_sessions": len(user_sessions),
                    "total_messages": total_messages,
                    "average_response_time": 1.5,  # 기본값
                    "agent_usage": {
                        "conversation_manager": len(user_sessions),
                        "storm": storm_usage,
                        "storm_interactive": 0  # 추후 구현
                    },
                    "success_rate": 0.95,
                    "popular_queries": [],
                    "last_activity": datetime.now() if user_sessions else None,
                    "most_active_hour": 14  # 기본값
                }
            else:
                return {"user_id": user_id, "total_sessions": 0, "total_messages": 0}
                
        except Exception as e:
            logger.error("Failed to get user chat stats", error=str(e), user_id=user_id)
            return {"user_id": user_id, "error": str(e)}

    async def cleanup(self):
        """서비스 정리"""
        try:
            if self.conversation_manager:
                # ConversationManager 정리
                self.conversation_manager.cleanup_inactive_sessions()
            
            if self.session_manager:
                # SessionManager 정리 (호환성)
                if hasattr(self.session_manager, 'cleanup'):
                    await self.session_manager.cleanup()
            
            if self.storm_service:
                # STORM 서비스 정리
                await self.storm_service.cleanup()
            
            if self.multi_agent_system:
                # 멀티에이전트 시스템 정리
                if hasattr(self.multi_agent_system, 'cleanup'):
                    await self.multi_agent_system.cleanup()
            
            logger.info("Agent Service cleanup completed")
            
        except Exception as e:
            logger.error("Error during service cleanup", error=str(e))

    # 기존 메서드들 유지...
    async def analyze_query_complexity(self, message: str) -> Dict[str, Any]:
        """
        쿼리 복잡도 분석
        """
        try:
            if self.multi_agent_system and hasattr(self.multi_agent_system, 'analyze_complexity'):
                return await self.multi_agent_system.analyze_complexity(message)
            else:
                # 기본 복잡도 분석 구현
                return await self._basic_complexity_analysis(message)
        except Exception as e:
            logger.error("Failed to analyze query complexity", 
                        error=str(e))
            return {
                "sub_queries": [message],
                "agents_involved": ["orchestrator"],
                "complexity_score": 0.5
            }
    
    async def submit_feedback(self, session_id: str, rating: int, comment: str):
        """
        피드백 제출
        """
        try:
            if self.session_manager and hasattr(self.session_manager, 'submit_feedback'):
                await self.session_manager.submit_feedback(session_id, rating, comment)
            logger.info("Feedback submitted", 
                       session_id=session_id, 
                       rating=rating)
        except Exception as e:
            logger.error("Failed to submit feedback", 
                        error=str(e),
                        session_id=session_id)
            raise
    
    async def update_chat_stats(
        self,
        user_id: str,
        session_id: str,
        processing_time: float,
        success: bool
    ):
        """
        채팅 통계 업데이트
        """
        try:
            if self.session_manager and hasattr(self.session_manager, 'update_stats'):
                await self.session_manager.update_stats(
                    user_id, session_id, processing_time, success
                )
        except Exception as e:
            logger.warning("Failed to update chat stats", 
                          error=str(e),
                          user_id=user_id)
    
    # Private methods
    
    async def _basic_complexity_analysis(self, message: str) -> Dict[str, Any]:
        """기본 복잡도 분석"""
        # 간단한 휴리스틱 기반 분석
        word_count = len(message.split())
        complexity_score = min(word_count / 50.0, 1.0)
        
        return {
            "sub_queries": [message],
            "agents_involved": ["orchestrator"],
            "complexity_score": complexity_score
        }

    async def _save_user_message(
        self, 
        session_id: str, 
        user_id: str, 
        message: str
    ):
        """사용자 메시지 저장"""
        try:
            if self.session_manager and hasattr(self.session_manager, 'save_message'):
                await self.session_manager.save_message(
                    session_id=session_id,
                    user_id=user_id,
                    message=message,
                    role="user"
                )
        except Exception as e:
            logger.warning("Failed to save user message", 
                          error=str(e),
                          session_id=session_id)

    async def _save_agent_message(
        self, 
        session_id: str, 
        response: str, 
        agent_type: str,
        metadata: Dict[str, Any]
    ):
        """에이전트 메시지 저장"""
        try:
            if self.session_manager and hasattr(self.session_manager, 'save_message'):
                await self.session_manager.save_message(
                    session_id=session_id,
                    user_id="system",
                    message=response,
                    role="assistant",
                    agent_type=agent_type,
                    metadata=metadata
                )
        except Exception as e:
            logger.warning("Failed to save agent message", 
                          error=str(e),
                          session_id=session_id)

    async def _create_fallback_response(
        self, 
        message: str, 
        error: str
    ) -> Dict[str, Any]:
        """폴백 응답 생성"""
        return {
            "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "agent_name": "Fallback_Agent",
            "agent_type": "fallback",
            "agent_description": "폴백 에이전트",
            "confidence": 0.1,
            "tools_used": [],
            "execution_time": 0.0,
            "metadata": {
                "error": error,
                "fallback": True
            }
        }

    async def _create_default_response(self, message: str) -> Dict[str, Any]:
        """기본 응답 생성"""
        return {
            "response": f"안녕하세요! '{message}'에 대한 답변을 준비하고 있습니다.",
            "agent_name": "Default_Agent",
            "agent_type": "default",
            "agent_description": "기본 에이전트",
            "confidence": 0.5,
            "tools_used": [],
            "execution_time": 0.0,
            "metadata": {
                "default_response": True
            }
        } 

    def _extract_topic_from_message(self, message: str) -> str:
        """메시지에서 연구 주제 추출"""
        # 연구 키워드 제거하고 주제 추출
        remove_keywords = ["연구해줘", "연구하고", "연구 해줘", "리서치", "조사해줘", "분석해줘", "정리해줘", "써줘", "작성해줘", "에 대해", "에대해", "에관해", "에 관해"]
        
        topic = message
        for keyword in remove_keywords:
            topic = topic.replace(keyword, "")
        
        # 전처리
        topic = topic.strip()
        topic = topic.replace("  ", " ")  # 이중 공백 제거
        
        return topic if topic else "알 수 없는 주제"
    
    def _extract_storm_topic_from_history(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """대화 기록에서 STORM 주제 추출"""
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                metadata = msg.get("metadata", {})
                if metadata.get("storm_setup_question") and "storm_topic" in metadata:
                    return metadata["storm_topic"]
        return None