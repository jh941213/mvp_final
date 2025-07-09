"""
KTDS MagenticOne 멀티에이전트 시스템 (그래프 기반 워크플로우)
쿼리 분류 후 적절한 에이전트로 라우팅하는 그래프 아키텍처
"""

import asyncio
import time
import uuid
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.conditions import MaxMessageTermination  
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_core.models import UserMessage, SystemMessage

from agents.hr_agent import create_hr_agent
from agents.bulletin_board_agent import create_bulletin_agent
from agents.project_management_agent import create_project_agent
from agents.ktds_info_agent import create_ktds_info_agent
from agents.midm import create_midm_agent
from tools.search_tools import create_search_agent
from session_manager import SessionManager
import os


class QueryClassification(BaseModel):
    """쿼리 분류 결과를 위한 Pydantic 모델"""
    classification: Literal["simple", "complex"]
    reason: str


class QueryClassifier:
    """쿼리 분류기 - 멀티에이전트 필요 여부 판단 (gpt-4.1-nano 고정)"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.model_name = os.getenv("OPENAI_MODEL_NAME")  # 고정 모델
        self.client = AzureOpenAIChatCompletionClient(
            model=self.model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            api_version="2024-12-01-preview"
        )
    
    async def classify_query(self, query: str) -> Literal["simple", "complex"]:
        """쿼리를 분류하여 처리 방식을 결정"""
        
        classification_prompt = f"""다음 사용자 쿼리를 분석하여 처리 방식을 결정하고 JSON 형식으로 답변하세요.

        쿼리: "{query}"

        분류 기준:
        1. SIMPLE (간단한 처리): 
        - 일반적인 인사, 감사 인사, 단순 대화
        - 간단한 질문/답변
        - 단순 대화

        2. COMPLEX (멀티에이전트 필요):
        - HR 관련 업무 (휴가, 급여, 복리후생 등)
        - 게시판 관련 업무 (공지사항, 게시물 작성/조회 등)
        - 프로젝트 관리 업무 (일정, 리소스, 진행상황 등)
        - 웹 검색 관련 업무 (최신 정보, 뉴스, 기술 동향 등)
        - KTDS 외부 정보 검색 (회사 정보, 기술 솔루션 등)
        - 복잡한 업무 처리가 필요한 경우
        - 여러 도메인에 걸친 작업

        응답 형식:
        {{
            "classification": "simple" 또는 "complex",
            "reason": "분류한 이유를 간단히 설명"
        }}"""
        
        try:
            # Structured output 사용 - extra_create_args로 response_format 설정
            response = await self.client.create(
                messages=[UserMessage(content=classification_prompt, source="user")],
                extra_create_args={
                    "response_format": QueryClassification,
                    "temperature": 0.1
                }
            )
            
            # Structured output 파싱
            if isinstance(response.content, str):
                import json
                result_data = json.loads(response.content)
                classification = result_data.get("classification", "complex")
                reason = result_data.get("reason", "")
            else:
                # 혹시 이미 파싱된 경우
                classification = response.content.classification
                reason = response.content.reason
            
            if self.verbose:
                print(f"🔍 쿼리 분류 결과: {classification} ('{query}')")
                print(f"   이유: {reason}")
            
            return classification
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️ 쿼리 분류 실패: {str(e)}, 복잡한 처리로 기본 설정")
            return "complex"


class SimpleKTDSAgent:
    """간단한 KTDS 에이전트 - 일반 대화 처리"""
    
    def __init__(self, verbose: bool = False, model_name: str = "midm"):
        self.verbose = verbose
        self.model_name = model_name
        
        # 믿음(Midm) 모델 사용
        if model_name == "midm":
            # Friendli AI Midm-2.0 클라이언트 사용
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            from autogen_ext.models.openai._model_info import ModelInfo
            
            # Midm 모델 정보 정의
            midm_model_info = ModelInfo(
                vision=False,
                function_calling=True,
                json_output=True,
                max_tokens=4096,
                max_input_tokens=8192,
                family="midm"
            )
            
            self.client = OpenAIChatCompletionClient(
                model=os.getenv("FRIENDLY_MODEL_NAME"),
                model_info=midm_model_info,
                api_key=os.getenv("FRIENDLY_API_KEY"),
                base_url=os.getenv("FRIENDLY_BASE_URL"),
            )
        else:
            # 기존 KTDS 프롬프트
            system_prompt = """
            당신과 미래사이 KT의 믿음 2.0 모델입니다.
            """
        
        try:
            # 메시지 구성 - 시스템 메시지부터 시작
            messages = [SystemMessage(content=system_prompt, source="system")]
            
            # 대화 히스토리가 있으면 추가 (시스템 메시지 제외)
            if conversation_history:
                for msg in conversation_history:
                    if msg.get("role") == "user":
                        messages.append(UserMessage(content=msg["content"], source="user"))
                    elif msg.get("role") in ["assistant", "agent"]:
                        messages.append(SystemMessage(content=f"Assistant: {msg['content']}", source="assistant"))
            
            # 현재 사용자 메시지 추가
            messages.append(UserMessage(content=query, source="user"))
            
            response = self.client.create(
                messages=messages,
                extra_create_args={"temperature": 0.3}
            )
            
            if self.verbose:
                print(f"💬 간단한 응답 생성 완료 (모델: {self.model_name})")
            
            return response.content.strip()
            
        except Exception as e:
            if self.verbose:
                print(f"❌ 간단한 응답 생성 실패: {str(e)}")
            return "안녕하세요! KTDS AI 어시스턴트 믿음입니다. 죄송하지만 잠시 후 다시 시도해 주세요."


class KTDSMagenticOneSystem:
    """KTDS MagenticOne 멀티에이전트 시스템 (쿼리 분류 포함)"""
    
    def __init__(self, verbose: bool = False, enable_session_manager: bool = True, model_name: str = "midm"):
        """MagenticOne 시스템 초기화"""
        self.verbose = verbose
        self.enable_session_manager = enable_session_manager
        self.model_name = model_name
        
        if self.verbose:
            print(f"🎯 KTDS MagenticOne 시스템 초기화 중... (모델: {model_name})")
        
        # 쿼리 분류기 및 간단한 에이전트 초기화 (QueryClassifier는 gpt-4.1-nano 고정)
        self.query_classifier = QueryClassifier(verbose=verbose)
        self.simple_agent = SimpleKTDSAgent(verbose=verbose, model_name=model_name)
        
        # 세션 관리자 초기화
        self.session_manager = None
        if self.enable_session_manager:
            try:
                self.session_manager = SessionManager()
                if self.verbose:
                    print("💾 세션 관리자 초기화 완료!")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ 세션 관리자 초기화 실패: {str(e)}")
                    print("   Azure SQL 연결 설정을 확인하세요.")
                self.session_manager = None
        
        # Orchestrator용 모델 클라이언트 설정 (동적 모델 사용)
        if model_name == "midm":
            # 복잡한 쿼리에서는 Azure OpenAI 사용 (Orchestrator는 Azure OpenAI가 더 안정적)
            self.orchestrator_client = AzureOpenAIChatCompletionClient(
                model=os.getenv("OPENAI_MODEL_NAME"),
                api_key=os.getenv("OPENAI_API_KEY"),
                azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
                api_version="2024-12-01-preview"
            )
        else:
            self.orchestrator_client = AzureOpenAIChatCompletionClient(
                model=model_name,
                api_key=os.getenv("OPENAI_API_KEY"),
                azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
                api_version="2024-12-01-preview"
            )
        
        # Worker 에이전트들 생성 (지연 로딩)
        self._team = None
        self._agents_initialized = False
        
        if self.verbose:
            print("✅ KTDS MagenticOne 시스템 초기화 완료!")
            print(f"   🔍 쿼리 분류기: 활성화")
            print(f"   💬 간단한 에이전트: 활성화")
            print(f"   🤖 멀티에이전트 팀: 지연 로딩")
    
    def _initialize_agents(self):
        """필요시에만 에이전트들 초기화 (지연 로딩)"""
        if self._agents_initialized:
            return
        
        if self.verbose:
            print("🤖 멀티에이전트 팀 초기화 중...")
        
        # Worker 에이전트들 생성 (동적 모델 사용)
        if self.verbose:
            print("🏢 HR 에이전트 생성 중...")
        self.hr_agent = create_hr_agent(model_name=self.model_name)
        
        if self.verbose:
            print("📋 게시판 에이전트 생성 중...")
        self.bulletin_agent = create_bulletin_agent(model_name=self.model_name)
        
        if self.verbose:
            print("📊 프로젝트 관리 에이전트 생성 중...")
        self.project_agent = create_project_agent(model_name=self.model_name)
        
        if self.verbose:
            print("🔍 KTDS 정보 에이전트 생성 중...")
        self.ktds_info_agent = create_ktds_info_agent(model_name=self.model_name)
        
        if self.verbose:
            print("💬 믿음(MI:DM) 에이전트 생성 중...")
        self.midm_agent = create_midm_agent()
        
        if self.verbose:
            print("🔍 검색 에이전트 생성 중...")
        self.search_agent = create_search_agent(self.orchestrator_client, model_name=self.model_name)
        
        # MagenticOneGroupChat 팀 생성
        if self.verbose:
            print("🤝 MagenticOne 팀 구성 중...")
        self._team = MagenticOneGroupChat(
            participants=[
                self.hr_agent,
                self.bulletin_agent, 
                self.project_agent,
                self.ktds_info_agent,
                self.midm_agent,
                self.search_agent
            ],
            model_client=self.orchestrator_client,
            termination_condition=MaxMessageTermination(10),
            max_turns=10
        )
        
        self._agents_initialized = True
        
        if self.verbose:
            print("✅ 멀티에이전트 팀 초기화 완료!")
            print(f"   📋 Orchestrator: MagenticOneOrchestrator")
            print(f"   🏢 Worker 1: {self.hr_agent.name}")
            print(f"   📋 Worker 2: {self.bulletin_agent.name}")
            print(f"   📊 Worker 3: {self.project_agent.name}")
            print(f"   🔍 Worker 4: {self.ktds_info_agent.name}")
            print(f"   💬 Worker 5: {self.midm_agent.name}")
            print(f"   🌐 Worker 6: {self.search_agent.name}")
    
    @property
    def team(self):
        """팀 프로퍼티 - 필요시에만 초기화"""
        if not self._agents_initialized:
            self._initialize_agents()
        return self._team
    
    async def process_query(self, query: str, user_id: str = "user", session_id: Optional[str] = None, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """사용자 질문을 처리합니다 (쿼리 분류 포함)"""
        try:
            start_time = time.time()
            
            # 세션 ID가 없으면 새로 생성
            if session_id is None and self.session_manager:
                session_id = self.session_manager.create_session(user_id)
                if self.verbose:
                    print(f"🆕 새 세션 생성: {session_id}")
            
            if self.verbose:
                print(f"\n🎯 쿼리 처리 시작: '{query}' (사용자: {user_id}, 세션: {session_id})")
            
            # 1단계: 쿼리 분류
            classification = await self.query_classifier.classify_query(query)
            
            # 2단계: 분류에 따른 처리
            if classification == "simple":
                # 간단한 쿼리 - SimpleKTDSAgent로 처리
                if self.verbose:
                    print("💬 간단한 쿼리로 분류 - SimpleKTDSAgent로 처리")
                
                response = await self.simple_agent.process_simple_query(query, conversation_history)
                
            else:
                # 복잡한 쿼리 - MagenticOne 멀티에이전트로 처리
                if self.verbose:
                    print("🤖 복잡한 쿼리로 분류 - MagenticOne 멀티에이전트로 처리")
                
                # 이전 대화 히스토리를 로드하여 팀 상태 복원
                if self.session_manager and session_id:
                    try:
                        history = self.session_manager.get_conversation_history(session_id)
                        if self.verbose and history:
                            print(f"📚 이전 대화 히스토리 로드: {len(history)}개 메시지")
                    except Exception as e:
                        if self.verbose:
                            print(f"⚠️ 히스토리 로드 실패: {str(e)}")
                
                # MagenticOneGroupChat 실행
                result = await self.team.run(task=query)
                
                # 마지막 응답 메시지 추출
                response = result.messages[-1].content if result.messages else "응답을 생성할 수 없습니다."
            
            # 3단계: 대화 히스토리 저장
            if self.session_manager and session_id:
                try:
                    self.session_manager.save_conversation_turn(
                        session_id=session_id,
                        user_message=query,
                        assistant_response=response
                    )
                    if self.verbose:
                        print("💾 대화 히스토리 저장 완료")
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️ 히스토리 저장 실패: {str(e)}")
            
            processing_time = round(time.time() - start_time, 2)
            
            if self.verbose:
                print(f"✅ 처리 완료 ({processing_time}초, 분류: {classification})")
            
            return response
            
        except Exception as e:
            error_msg = f"쿼리 처리 중 오류가 발생했습니다: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            return "죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해 주세요."
    
    async def run_stream(self, query: str):
        """스트림 방식으로 실행 (복잡한 쿼리만 지원)"""
        if self.verbose:
            print(f"\n🎯 스트림 쿼리 시작: '{query}'")
        
        # 먼저 쿼리 분류
        classification = await self.query_classifier.classify_query(query)
        
        if classification == "simple":
            # 간단한 쿼리는 스트림 없이 일반 응답
            response = await self.simple_agent.process_simple_query(query)
            yield response
        else:
            # 복잡한 쿼리만 스트림 처리
            try:
                async for event in self.team.run_stream(task=query):
                    yield event
            except Exception as e:
                if self.verbose:
                    print(f"❌ 스트림 처리 중 오류: {str(e)}")
                yield f"스트림 처리 중 오류가 발생했습니다."
    
    def get_system_status(self) -> dict:
        """시스템 상태 정보 반환"""
        status = {
            "system_name": "KTDS MagenticOne 멀티에이전트 시스템 (쿼리 분류 포함)",
            "architecture": "Query Classification → Simple Agent | MagenticOne (Orchestrator + Workers)",
            "query_classifier": "활성화",
            "simple_agent": "활성화",
            "orchestrator": "MagenticOneOrchestrator",
            "workers": [],
            "total_tools": 0,
            "model": self.model_name,
            "max_turns": 10,
            "session_manager": self.session_manager is not None,
            "agents_initialized": self._agents_initialized
        }
        
        # 에이전트가 초기화된 경우에만 상세 정보 추가
        if self._agents_initialized:
            status["workers"] = [
                {
                    "name": self.hr_agent.name,
                    "description": self.hr_agent.description,
                    "tools": len(self.hr_agent._tools) if hasattr(self.hr_agent, '_tools') else 0
                },
                {
                    "name": self.bulletin_agent.name,
                    "description": self.bulletin_agent.description, 
                    "tools": len(self.bulletin_agent._tools) if hasattr(self.bulletin_agent, '_tools') else 0
                },
                {
                    "name": self.project_agent.name,
                    "description": self.project_agent.description,
                    "tools": len(self.project_agent._tools) if hasattr(self.project_agent, '_tools') else 0
                },
                {
                    "name": self.ktds_info_agent.name,
                    "description": self.ktds_info_agent.description,
                    "tools": len(self.ktds_info_agent._tools) if hasattr(self.ktds_info_agent, '_tools') else 0
                },
                {
                    "name": self.midm_agent.name,
                    "description": self.midm_agent.description,
                    "tools": len(self.midm_agent._tools) if hasattr(self.midm_agent, '_tools') else 0
                },
                {
                    "name": self.search_agent.name,
                    "description": self.search_agent.description,
                    "tools": len(self.search_agent._tools) if hasattr(self.search_agent, '_tools') else 0
                }
            ]
            
            status["total_tools"] = sum([
                len(self.hr_agent._tools) if hasattr(self.hr_agent, '_tools') else 0,
                len(self.bulletin_agent._tools) if hasattr(self.bulletin_agent, '_tools') else 0,
                len(self.project_agent._tools) if hasattr(self.project_agent, '_tools') else 0,
                len(self.ktds_info_agent._tools) if hasattr(self.ktds_info_agent, '_tools') else 0,
                len(self.midm_agent._tools) if hasattr(self.midm_agent, '_tools') else 0,
                len(self.search_agent._tools) if hasattr(self.search_agent, '_tools') else 0
            ])
        
        return status
    
    # 세션 관리 메서드들
    def create_session(self, user_id: str) -> Optional[str]:
        """새 세션을 생성합니다"""
        if self.session_manager:
            return self.session_manager.create_session(user_id)
        return None
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보를 조회합니다"""
        if self.session_manager:
            return self.session_manager.get_session_info(session_id)
        return None
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """대화 히스토리를 조회합니다"""
        if self.session_manager:
            return self.session_manager.get_conversation_history(session_id)
        return []
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 모든 세션을 조회합니다"""
        if self.session_manager:
            return self.session_manager.get_user_sessions(user_id)
        return []
    
    def end_session(self, session_id: str) -> bool:
        """세션을 종료합니다"""
        if self.session_manager:
            return self.session_manager.end_session(session_id)
        return False
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """오래된 세션들을 정리합니다"""
        if self.session_manager:
            return self.session_manager.cleanup_old_sessions(days)
        return 0
    
    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계를 조회합니다"""
        if self.session_manager:
            return self.session_manager.get_session_stats()
        return {}


# 전역 시스템 인스턴스
_magentic_system: Optional[KTDSMagenticOneSystem] = None


def get_magentic_system(verbose: bool = False, model_name: str = "midm") -> KTDSMagenticOneSystem:
    """전역 MagenticOne 시스템 인스턴스 반환 (싱글톤)"""
    global _magentic_system
    if _magentic_system is None:
        _magentic_system = KTDSMagenticOneSystem(verbose=verbose, model_name=model_name)
    return _magentic_system





# 전역 시스템 인스턴스
_magentic_system: Optional[KTDSMagenticOneSystem] = None


def get_magentic_system(verbose: bool = False, model_name: str = "midm") -> KTDSMagenticOneSystem:
    """전역 MagenticOne 시스템 인스턴스 반환 (싱글톤)"""
    global _magentic_system
    if _magentic_system is None:
        _magentic_system = KTDSMagenticOneSystem(verbose=verbose, model_name=model_name)
    return _magentic_system


 