#!/usr/bin/env python3
"""
STORM 에이전트 서비스
ParallelStormResearchSystem을 백엔드 서비스로 통합
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import uuid

from app.core.logging_config import get_logger
from app.core.config import get_settings
from app.models.chat_models import (
    StormConfig, StormStats, StormInteraction, 
    StormHumanInteraction, StormHumanResponse
)

logger = get_logger("storm_service")

# STORM 시스템 임포트
STORM_AVAILABLE = False
try:
    import sys
    from pathlib import Path
    
    # storm_research2.py 경로 추가
    storm_path = str(Path(__file__).parent.parent.parent)
    if storm_path not in sys.path:
        sys.path.insert(0, storm_path)
    
    from backend.agent.storm_research import ParallelStormResearchSystem
    STORM_AVAILABLE = True
    logger.info("✅ STORM system imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ STORM system not available: {e}")
    STORM_AVAILABLE = False

class StormService:
    """
    STORM 에이전트 서비스 클래스
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.initialized = False
        self.storm_system = None
        self.active_sessions = {}  # 활성 세션들
        self.human_interactions = {}  # 대기 중인 Human-in-the-Loop 상호작용들
        
    async def initialize(self):
        """서비스 초기화"""
        if self.initialized:
            return
            
        try:
            logger.info("Initializing STORM Service...")
            
            if STORM_AVAILABLE:
                # STORM 시스템 초기화
                self.storm_system = ParallelStormResearchSystem(max_workers=4)
                logger.info("✅ STORM system initialized successfully")
            else:
                logger.warning("⚠️ STORM system not available")
                
            self.initialized = True
            logger.info("STORM Service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize STORM Service", error=str(e))
            raise
    
    async def process_storm_research(
        self,
        topic: str,
        user_id: str,
        session_id: str,
        config: StormConfig = None
    ) -> Dict[str, Any]:
        """
        STORM 연구 프로세스 실행
        """
        if not self.initialized:
            await self.initialize()
            
        if not STORM_AVAILABLE or not self.storm_system:
            raise ValueError("STORM system not available")
            
        try:
            logger.info("Starting STORM research",
                       topic=topic,
                       user_id=user_id,
                       session_id=session_id)
            
            start_time = time.time()
            
            # 편집자 수 결정
            editor_count = config.editor_count if config else 3
            editor_count = min(editor_count, 8)  # 최대 8개로 제한
            
            # 설정에 맞는 새로운 STORM 시스템 생성
            custom_storm_system = ParallelStormResearchSystem(max_workers=editor_count)
            
            # STORM 연구 실행 (Human-in-the-Loop 비활성화)
            final_article = ""
            total_processing_time = 0
            outline_sections = 0
            editors_count = 0
            interviews_completed = 0
            
            async for update_event in custom_storm_system.run_parallel_storm_research(
                topic=topic,
                enable_human_loop=False,
                editor_count=editor_count
            ):
                if update_event.get("type") == "storm_complete":
                    final_article = update_event.get("content", "")
                    total_processing_time = update_event.get("processing_time", 0)
                    if custom_storm_system.state:
                        if custom_storm_system.state.outline:
                            outline_sections = len(custom_storm_system.state.outline.sections)
                        if custom_storm_system.state.editors:
                            editors_count = len(custom_storm_system.state.editors)
                        if custom_storm_system.state.interview_results:
                            interviews_completed = len(custom_storm_system.state.interview_results)
                    break
            
            # 결과 구성
            result = {
                "response": final_article,
                "session_id": session_id,
                "agent_name": "STORM_Research_Agent",
                "agent_type": "storm",
                "agent_description": "병렬 STORM 연구 에이전트",
                "confidence": 0.95,
                "tools_used": [
                    "tavily_search",
                    "multi_agent_interviews",
                    "parallel_processing",
                    "wiki_writing"
                ],
                "execution_time": total_processing_time,
                "metadata": {
                    "storm_research": True,
                    "topic": topic,
                    "research_steps": custom_storm_system.total_steps,
                    "parallel_workers": editor_count,
                    "processing_time": total_processing_time,
                    "word_count": len(final_article.split()),
                    "outline_sections": outline_sections,
                    "editors_count": editors_count,
                    "interviews_completed": interviews_completed
                }
            }
            
            logger.info("✅ STORM research completed successfully",
                       processing_time=total_processing_time,
                       word_count=result["metadata"]["word_count"],
                       editors_count=result["metadata"]["editors_count"])
            
            return result
            
        except Exception as e:
            logger.error("Failed to process STORM research",
                        error=str(e),
                        topic=topic,
                        session_id=session_id)
            raise
    
    async def process_storm_interactive(
        self,
        topic: str,
        user_id: str,
        session_id: str,
        config: StormConfig = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        STORM 연구 인터랙티브 스트리밍 처리 (Human-in-the-Loop)
        """
        if not self.initialized:
            await self.initialize()
            
        if not STORM_AVAILABLE:
            raise ValueError("STORM system not available")
            
        try:
            logger.info("Starting STORM interactive research (streaming)",
                       topic=topic,
                       user_id=user_id,
                       session_id=session_id)
            
            editor_count = config.editor_count if config else 3
            editor_count = min(editor_count, 8)
            
            # 각 요청마다 새로운 STORM 시스템 인스턴스를 생성하여 독립성 보장
            custom_storm_system = ParallelStormResearchSystem(max_workers=editor_count)
            
            # storm_research.py에서 yield된 모든 이벤트를 그대로 yield
            async for event in custom_storm_system.run_parallel_storm_research(
                topic=topic,
                enable_human_loop=True,
                editor_count=editor_count
            ):
                yield event
            
        except Exception as e:
            logger.error("Error in STORM interactive research (streaming)",
                        error=str(e),
                        topic=topic,
                        session_id=session_id)
            yield {
                "type": "storm_error",
                "content": f"❌ STORM 연구 스트림 오류: {str(e)}",
                "session_id": session_id,
                "error": str(e)
            }
        finally:
            # 세션 정리 (필요에 따라) - 이 부분은 agent_service.py나 chat.py에서 관리될 수 있음
            pass
    
    async def handle_human_response(
        self,
        session_id: str,
        interaction_id: str,
        response: StormHumanResponse
    ) -> Dict[str, Any]:
        """
        Human-in-the-Loop 사용자 응답 처리
        """
        if session_id not in self.human_interactions:
            return {"error": "해당 세션의 상호작용을 찾을 수 없습니다."}
        
        interaction = self.human_interactions[session_id]
        
        if interaction["interaction_id"] != interaction_id:
            return {"error": "잘못된 상호작용 ID입니다."}
        
        # 응답 저장
        interaction["response"] = {
            "action": response.action,
            "feedback": response.feedback,
            "modifications": response.modifications,
            "timestamp": response.timestamp
        }
        
        return {"success": True, "message": "응답이 처리되었습니다."}
    
    async def get_storm_capabilities(self) -> Dict[str, Any]:
        """
        STORM 시스템 능력 및 상태 조회
        """
        return {
            "available": STORM_AVAILABLE,
            "initialized": self.initialized,
            "max_workers": 8,
            "supported_features": [
                "parallel_research",
                "multi_agent_interviews",
                "wiki_style_writing",
                "outline_generation",
                "section_writing",
                "reference_management",
                "human_in_the_loop",
                "interactive_streaming",
                "configurable_editors"
            ],
            "research_steps": [
                "초기 아웃라인 생성",
                "편집자 관점 생성",
                "병렬 인터뷰 진행",
                "아웃라인 개선",
                "병렬 섹션 작성",
                "최종 아티클 작성"
            ],
            "interactive_features": [
                "편집자 수 설정 (1-8명)",
                "편집자 검토 및 승인",
                "아웃라인 검토 및 수정",
                "실시간 진행 상황 모니터링",
                "섹션별 검토"
            ]
        }
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        세션 상태 조회
        """
        if session_id not in self.active_sessions:
            return {"error": "세션을 찾을 수 없습니다."}
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "topic": session["topic"],
            "user_id": session["user_id"],
            "current_step": session["current_step"],
            "total_steps": session["total_steps"],
            "start_time": session["start_time"],
            "elapsed_time": time.time() - session["start_time"],
            "has_interaction": session_id in self.human_interactions,
            "completed": session.get("completed", False)
        }
    
    async def cleanup(self):
        """서비스 정리"""
        try:
            if self.storm_system:
                # STORM 시스템 정리
                if hasattr(self.storm_system, 'cleanup'):
                    await self.storm_system.cleanup()
                    
                # 모델 클라이언트 정리
                if hasattr(self.storm_system, 'model_client'):
                    await self.storm_system.model_client.close()
                if hasattr(self.storm_system, 'long_context_model'):
                    await self.storm_system.long_context_model.close()
            
            # 활성 세션 정리
            self.active_sessions.clear()
            self.human_interactions.clear()
                    
            logger.info("STORM Service cleanup completed")
            
        except Exception as e:
            logger.error("Error during STORM service cleanup", error=str(e)) 