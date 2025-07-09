#!/usr/bin/env python3
"""
세션 관리 API 라우터 (ConversationManager 중심)
ConversationManager를 통한 통합 세션 관리
"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.session_models import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse,
    SessionHistoryResponse,
    SessionUpdateRequest,
    SessionStatsResponse,
    SessionQueryParams,
    SessionStatus
)
from app.core.logging_config import get_logger
from app.services.agent_service import AgentService

router = APIRouter()
logger = get_logger("session")

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    agent_service: AgentService = Depends()
):
    """
    새 세션 생성 (ConversationManager 기반)
    """
    try:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        # ConversationManager에서 세션 컨텍스트 생성
        conversation_manager_available = bool(agent_service.conversation_manager)
        azure_sql_enabled = False
        
        if agent_service.conversation_manager:
            # 새 대화 컨텍스트 생성
            context = agent_service.conversation_manager.get_or_create_context(session_id)
            conv_stats = agent_service.conversation_manager.get_session_stats()
            azure_sql_enabled = conv_stats.get("azure_sql_enabled", False)
            
            logger.info("ConversationManager session created", 
                       session_id=session_id, 
                       user_id=request.user_id,
                       azure_sql_enabled=azure_sql_enabled)
        else:
            logger.warning("ConversationManager not available", session_id=session_id)
        
        # 세션 메타데이터 구성
        session_metadata = request.metadata or {}
        session_metadata.update({
            "conversation_manager": conversation_manager_available,
            "azure_sql_storage": azure_sql_enabled,
            "multiturn_conversation": True,
            "session_continuity": True,
            "created_timestamp": now.isoformat()
        })
        
        return SessionResponse(
            session_id=session_id,
            user_id=request.user_id,
            session_name=request.session_name,
            status=SessionStatus.ACTIVE,
            created_at=now,
            last_activity=now,
            message_count=0,
            metadata=session_metadata
        )
        
    except Exception as e:
        logger.error("Failed to create session", 
                    error=str(e),
                    user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail="세션 생성에 실패했습니다."
        )

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    status: Optional[SessionStatus] = Query(None, description="상태 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    agent_service: AgentService = Depends()
):
    """
    세션 목록 조회 (ConversationManager 기반)
    """
    try:
        sessions = []
        total_count = 0
        
        if agent_service.conversation_manager:
            # ConversationManager에서 활성 세션 목록 조회
            active_sessions = agent_service.conversation_manager.get_active_sessions()
            
            # 각 세션의 정보 수집
            for session_id in active_sessions:
                try:
                    context = agent_service.conversation_manager.get_context_for_session(session_id)
                    if context:
                        summary = context.get_conversation_summary()
                        history = agent_service.conversation_manager.get_conversation_history(session_id)
                        
                        # 사용자 ID 필터링 (메시지에서 추출)
                        session_user_id = "unknown"
                        if history:
                            for msg in history:
                                if msg.get("role") == "user" and msg.get("source"):
                                    session_user_id = msg.get("source")
                                    break
                        
                        # 필터 적용
                        if user_id and session_user_id != user_id:
                            continue
                        
                        # 세션 정보 구성
                        last_message_time = now = datetime.now()
                        if summary.get("latest_message"):
                            try:
                                last_message_time = datetime.fromisoformat(summary["latest_message"].replace('Z', '+00:00'))
                            except:
                                pass
                        
                        # 첫 번째 사용자 메시지로 세션 이름 생성
                        session_name = None
                        if history:
                            for msg in history:
                                if msg.get("role") == "user" and msg.get("content"):
                                    first_content = msg["content"][:20]
                                    session_name = first_content + ("..." if len(msg["content"]) > 20 else "")
                                    break
                        
                        if not session_name:
                            session_name = f"새 대화 {datetime.now().strftime('%m/%d %H:%M')}"
                        
                        session_response = SessionResponse(
                            session_id=session_id,
                            user_id=session_user_id,
                            session_name=session_name,
                            status=SessionStatus.ACTIVE,
                            created_at=datetime.fromisoformat(summary.get("oldest_message", now.isoformat()).replace('Z', '+00:00')) if summary.get("oldest_message") else now,
                            last_activity=last_message_time,
                            message_count=summary.get("total_messages", 0),
                            metadata={
                                "conversation_manager": True,
                                "azure_sql_enabled": summary.get("azure_sql_enabled", False),
                                "buffer_size": summary.get("buffer_size", 20),
                                "user_messages": summary.get("user_messages", 0),
                                "assistant_messages": summary.get("assistant_messages", 0)
                            }
                        )
                        sessions.append(session_response)
                        
                except Exception as session_error:
                    logger.warning(f"Failed to process session {session_id}: {session_error}")
                    continue
            
            total_count = len(sessions)
            
            # 페이징 적용
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            sessions = sessions[start_idx:end_idx]
        
        has_next = (page * page_size) < total_count
        
        return SessionListResponse(
            sessions=sessions,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error("Failed to list sessions", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="세션 목록 조회에 실패했습니다."
        )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    agent_service: AgentService = Depends()
):
    """
    특정 세션 정보 조회 (ConversationManager 기반)
    """
    try:
        if not agent_service.conversation_manager:
            raise HTTPException(
                status_code=503,
                detail="ConversationManager를 사용할 수 없습니다."
            )
        
        # ConversationManager에서 세션 정보 조회
        context = agent_service.conversation_manager.get_context_for_session(session_id)
        if not context:
            raise HTTPException(
                status_code=404,
                detail="세션을 찾을 수 없습니다."
            )
        
        summary = context.get_conversation_summary()
        history = agent_service.conversation_manager.get_conversation_history(session_id)
        
        # 사용자 ID 추출
        user_id = "unknown"
        if history:
            for msg in history:
                if msg.get("role") == "user" and msg.get("source"):
                    user_id = msg.get("source")
                    break
        
        # 시간 정보 처리
        now = datetime.now()
        created_at = now
        last_activity = now
        
        if summary.get("oldest_message"):
            try:
                created_at = datetime.fromisoformat(summary["oldest_message"].replace('Z', '+00:00'))
            except:
                pass
                
        if summary.get("latest_message"):
            try:
                last_activity = datetime.fromisoformat(summary["latest_message"].replace('Z', '+00:00'))
            except:
                pass
        
        # 세션 이름 설정
        session_name = None
        if summary.get("total_messages") > 0:
            # 첫 번째 사용자 메시지에서 세션 이름 추출
            for msg in history:
                if msg.get("role") == "user" and msg.get("content"):
                    first_content = msg["content"][:20]
                    session_name = first_content + ("..." if len(msg["content"]) > 20 else "")
                    break
        
        if not session_name:
            session_name = f"새 대화 {datetime.now().strftime('%m/%d %H:%M')}"
        
        # 메타데이터 구성
        session_metadata = {
            "conversation_manager": True,
            "azure_sql_enabled": agent_service.conversation_manager.session_manager is not None,
            "session_continuity": True,
            "multiturn_conversation": True,
            "message_summary": summary
        }
        
        return SessionResponse(
            session_id=session_id,
            user_id=user_id,
            session_name=session_name,
            status=SessionStatus.ACTIVE,
            created_at=created_at,
            last_activity=last_activity,
            message_count=len(history),
            metadata=session_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session info", 
                    error=str(e),
                    session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="세션 정보 조회에 실패했습니다."
        )

@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    agent_service: AgentService = Depends()
):
    """
    세션 정보 업데이트 (세션 이름 변경 등)
    """
    try:
        if not agent_service.conversation_manager:
            raise HTTPException(
                status_code=503,
                detail="ConversationManager를 사용할 수 없습니다."
            )
        
        # 기존 세션 확인
        context = agent_service.conversation_manager.get_context_for_session(session_id)
        if not context:
            raise HTTPException(
                status_code=404,
                detail="세션을 찾을 수 없습니다."
            )
        
        # 세션 이름 업데이트
        if request.session_name is not None:
            # ConversationManager에 세션 메타데이터 업데이트
            # (실제 구현에서는 세션 메타데이터를 저장하는 방식으로 구현)
            logger.info("Session name updated", 
                       session_id=session_id,
                       old_name=getattr(context, 'session_name', None),
                       new_name=request.session_name)
        
        # 업데이트된 세션 정보 반환
        updated_session = await get_session(session_id, agent_service)
        
        # 세션 이름이 요청에 포함되어 있으면 덮어쓰기
        if request.session_name is not None:
            updated_session.session_name = request.session_name
            updated_session.metadata = updated_session.metadata or {}
            updated_session.metadata["updated_session_name"] = request.session_name
            updated_session.metadata["name_updated_at"] = datetime.now().isoformat()
        
        logger.info("Session updated successfully", 
                   session_id=session_id,
                   updates={"session_name": request.session_name})
        
        return updated_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update session", 
                    error=str(e),
                    session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="세션 업데이트에 실패했습니다."
        )

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    agent_service: AgentService = Depends()
):
    """
    세션 삭제 (ConversationManager 기반)
    """
    try:
        if not agent_service.conversation_manager:
            raise HTTPException(
                status_code=503,
                detail="ConversationManager를 사용할 수 없습니다."
            )
        
        # 세션 존재 여부 확인
        context = agent_service.conversation_manager.get_context_for_session(session_id)
        if not context:
            raise HTTPException(
                status_code=404,
                detail="세션을 찾을 수 없습니다."
            )
        
        # ConversationManager에서 세션 삭제
        success = agent_service.conversation_manager.clear_session(session_id)
        
        if success:
            logger.info("Session deleted successfully", session_id=session_id)
            return {
                "message": "세션이 성공적으로 삭제되었습니다.",
                "session_id": session_id,
                "success": True
            }
        else:
            logger.warning("Session deletion failed", session_id=session_id)
            raise HTTPException(
                status_code=500,
                detail="세션 삭제에 실패했습니다."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete session", 
                    error=str(e),
                    session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="세션 삭제 중 오류가 발생했습니다."
        )

@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    agent_service: AgentService = Depends()
):
    """
    세션의 대화 기록 조회 (ConversationManager 기반)
    """
    try:
        if not agent_service.conversation_manager:
            raise HTTPException(
                status_code=503,
                detail="ConversationManager를 사용할 수 없습니다."
            )
        
        # ConversationManager에서 대화 기록 조회 (Azure SQL 포함)
        messages = await agent_service.get_conversation_history(session_id)
        
        # 세션 정보 조회
        try:
            session_info = await get_session(session_id, agent_service)
        except HTTPException as he:
            if he.status_code == 404:
                session_info = SessionResponse(
                    session_id=session_id,
                    user_id="unknown",
                    session_name=f"새 대화 {datetime.now().strftime('%m/%d %H:%M')}",
                    status=SessionStatus.ACTIVE,
                    created_at=datetime.now(),
                    last_activity=datetime.now(),
                    message_count=len(messages),
                    metadata={
                        "conversation_manager": True,
                        "azure_sql_enabled": False,
                        "session_not_found": True
                    }
                )
            else:
                raise
        
        # MessageResponse 형태로 변환
        from app.models.session_models import MessageResponse
        from app.models.chat_models import ChatMessage
        
        message_responses = []
        for i, msg in enumerate(messages):
            # msg가 딕셔너리인지 객체인지 확인
            if isinstance(msg, dict):
                # 딕셔너리인 경우
                role = msg.get("role", "assistant")
                content = msg.get("content", "")
                timestamp_str = msg.get("timestamp", datetime.now().isoformat())
                metadata = msg.get("metadata", {})
            else:
                # 객체인 경우 (ChatMessage 클래스의 인스턴스)
                role = getattr(msg, 'role', 'assistant')
                if hasattr(role, 'value'):
                    role = role.value
                content = getattr(msg, 'content', '')
                timestamp_str = getattr(msg, 'timestamp', datetime.now().isoformat())
                metadata = getattr(msg, 'metadata', {})
            
            # 메시지 타임스탬프 처리
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
            
            # ChatMessage 객체 생성
            chat_message = ChatMessage(
                role=role,
                content=content,
                timestamp=timestamp,
                metadata=metadata
            )
            
            message_response = MessageResponse(
                message_id=f"{session_id}_{i}",
                session_id=session_id,
                message=chat_message,
                created_at=timestamp
            )
            message_responses.append(message_response)
        
        return SessionHistoryResponse(
            session_id=session_id,
            messages=message_responses,
            total_messages=len(message_responses),
            session_info=session_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session history", 
                    error=str(e),
                    session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="세션 기록 조회에 실패했습니다."
        )

from pydantic import BaseModel
from typing import List, Optional

class SummaryMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class SummaryRequest(BaseModel):
    messages: List[SummaryMessage]
    user_id: Optional[str] = "kim.db@kt.com"
    model: Optional[str] = "gpt-4.1-nano"

@router.post("/sessions/{session_id}/summary")
async def generate_session_summary(
    session_id: str,
    request: SummaryRequest,
    agent_service: AgentService = Depends()
):
    """
    GPT-4.1-nano를 사용하여 세션 대화 내역을 요약하고 세션 제목을 생성합니다.
    """
    try:
        # 프론트엔드에서 전달받은 메시지 사용
        messages = [msg.dict() for msg in request.messages]
        
        if not messages or len(messages) < 2:
            raise HTTPException(
                status_code=400,
                detail="요약하기에 충분한 대화 내역이 없습니다."
            )
        
        # 대화 내용을 텍스트로 변환 (최근 10개 메시지만)
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        conversation_text = ""
        
        for msg in recent_messages:
            role = "사용자" if msg.get("role") == "user" else "어시스턴트"
            content = msg.get("content", "")
            if content:
                conversation_text += f"{role}: {content}\n\n"
        
        if not conversation_text.strip():
            raise HTTPException(
                status_code=400,
                detail="요약할 대화 내용이 없습니다."
            )
        
        # GPT-4.1-nano로 요약 요청 (Azure OpenAI 직접 호출)
        summary_prompt = f"""다음 대화를 간단하고 명확한 제목으로 요약해주세요. 제목은 한국어로 20자 이내로 작성하고, 대화의 핵심 주제를 포함해야 합니다.

대화 내용:
{conversation_text}

요구사항:
1. 한국어로 작성
2. 20자 이내
3. 핵심 주제 포함
4. 제목만 응답 (추가 설명 없이)

제목:"""

        # Azure OpenAI 직접 호출
        import openai
        import os
        from openai import AzureOpenAI
        
        # Azure OpenAI 클라이언트 초기화 (gpt-4.1 모델 설정 사용)
        client = AzureOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("OPENAI_ENDPOINT")
        )
        
        # GPT-4.1 호출 (동기 방식)
        response = client.chat.completions.create(
            model="gpt-4.1",  # gpt-4.1 모델 사용
            messages=[
                {"role": "system", "content": "당신은 대화 내용을 간결한 제목으로 요약하는 전문가입니다. 항상 한국어로 20자 이내의 명확한 제목을 생성합니다."},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=50,
            temperature=0.3,
            top_p=1.0,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        # 생성된 제목 정리
        session_title = response.choices[0].message.content.strip() if response.choices else ""
        
        # 제목이 너무 길거나 적절하지 않은 경우 폴백
        if not session_title or len(session_title) > 30:
            # 첫 번째 사용자 메시지 기반으로 폴백 제목 생성
            first_user_msg = next((msg.get("content", "") for msg in messages if msg.get("role") == "user"), "")
            if first_user_msg:
                session_title = first_user_msg[:20] + "..." if len(first_user_msg) > 20 else first_user_msg
            else:
                session_title = f"대화 세션 {datetime.now().strftime('%m/%d %H:%M')}"
        
        logger.info("Session summary generated", 
                   session_id=session_id,
                   title=session_title,
                   message_count=len(messages))
        
        return {
            "session_id": session_id,
            "session_title": session_title,
            "summary": session_title,  # 제목과 요약을 같게 처리
            "message_count": len(messages),
            "generated_at": datetime.now().isoformat(),
            "model_used": "gpt-4.1",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate session summary", 
                    error=str(e),
                    session_id=session_id)
        
        # 오류 발생 시 폴백 제목 생성
        try:
            messages = await agent_service.get_conversation_history(session_id)
            first_user_msg = next((msg.get("content", "") for msg in messages if msg.get("role") == "user"), "")
            fallback_title = first_user_msg[:20] + "..." if len(first_user_msg) > 20 else first_user_msg
            if not fallback_title:
                fallback_title = f"대화 세션 {datetime.now().strftime('%m/%d %H:%M')}"
            
            return {
                "session_id": session_id,
                "session_title": fallback_title,
                "summary": fallback_title,
                "message_count": len(messages) if messages else 0,
                "generated_at": datetime.now().isoformat(),
                "model_used": "fallback",
                "success": False,
                "error": "AI 요약 실패, 폴백 제목 사용"
            }
        except:
            return {
                "session_id": session_id,
                "session_title": f"대화 세션 {datetime.now().strftime('%m/%d %H:%M')}",
                "summary": f"대화 세션 {datetime.now().strftime('%m/%d %H:%M')}",
                "message_count": 0,
                "generated_at": datetime.now().isoformat(),
                "model_used": "fallback",
                "success": False,
                "error": "요약 생성 실패"
            }

@router.get("/users/{user_id}/sessions/stats", response_model=SessionStatsResponse)
async def get_user_session_stats(
    user_id: str,
    agent_service: AgentService = Depends()
):
    """
    사용자의 세션 통계 조회 (ConversationManager 기반)
    """
    try:
        stats = await agent_service.get_user_chat_stats(user_id)
        
        return SessionStatsResponse(
            user_id=user_id,
            total_sessions=stats.get("total_sessions", 0),
            active_sessions=stats.get("active_sessions", 0),
            total_messages=stats.get("total_messages", 0),
            average_session_duration=stats.get("average_response_time", 0.0),
            last_activity=stats.get("last_activity"),
            most_active_hour=stats.get("most_active_hour", 14)
        )
        
    except Exception as e:
        logger.error("Failed to get user session stats", 
                    error=str(e),
                    user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail="사용자 세션 통계 조회에 실패했습니다."
        )

@router.post("/sessions/{session_id}/close")
async def close_session(
    session_id: str,
    agent_service: AgentService = Depends()
):
    """
    세션 종료 (ConversationManager는 자동 관리하므로 정보성 응답)
    """
    try:
        if not agent_service.conversation_manager:
            raise HTTPException(
                status_code=503,
                detail="ConversationManager를 사용할 수 없습니다."
            )
        
        # ConversationManager는 세션을 자동으로 관리하므로 
        # 명시적 종료보다는 비활성화 정리를 수행
        context = agent_service.conversation_manager.get_context_for_session(session_id)
        session_exists = context is not None
        
        if session_exists:
            logger.info("Session close requested", 
                       session_id=session_id,
                       note="ConversationManager handles sessions automatically")
        
        return {
            "message": "세션 종료가 요청되었습니다. ConversationManager가 자동으로 관리합니다.",
            "session_id": session_id,
            "session_exists": session_exists,
            "auto_managed": True,
            "conversation_manager": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to close session", 
                    error=str(e),
                    session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="세션 종료에 실패했습니다."
        )

@router.get("/sessions/{session_id}/continuity")
async def check_session_continuity(
    session_id: str,
    agent_service: AgentService = Depends()
):
    """
    세션 연속성 상태 확인 (ConversationManager 기반)
    """
    try:
        if not agent_service.conversation_manager:
            return {
                "session_id": session_id,
                "session_exists": False,
                "continuity_supported": False,
                "conversation_manager": False,
                "error": "ConversationManager not available"
            }
        
        # ConversationManager 기능 확인
        conv_stats = agent_service.conversation_manager.get_session_stats()
        
        # 세션 존재 여부 및 정보 확인
        context = agent_service.conversation_manager.get_context_for_session(session_id)
        session_exists = context is not None
        session_info = None
        
        if session_exists:
            summary = context.get_conversation_summary()
            session_info = {
                "total_messages": summary.get("total_messages", 0),
                "user_messages": summary.get("user_messages", 0),
                "assistant_messages": summary.get("assistant_messages", 0),
                "azure_sql_enabled": summary.get("azure_sql_enabled", False),
                "buffer_size": summary.get("buffer_size", 20)
            }
        
        # 대화 히스토리 확인
        conversation_history = await agent_service.get_conversation_history(session_id)
        
        return {
            "session_id": session_id,
            "session_exists": session_exists,
            "continuity_supported": True,
            "conversation_manager": True,
            "azure_sql_enabled": conv_stats.get("azure_sql_enabled", False),
            "session_info": session_info,
            "conversation_count": len(conversation_history),
            "can_continue": session_exists,
            "multiturn_support": True,
            "buffer_management": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to check session continuity", 
                    error=str(e),
                    session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="세션 연속성 확인에 실패했습니다."
        ) 