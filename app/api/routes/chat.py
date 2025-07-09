#!/usr/bin/env python3
"""
채팅 API 라우터 - 백업
"""

import time
import uuid
import json
import os
from datetime import datetime
from typing import Dict, Any, List, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse

from app.models.chat_models import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    AgentInfo,
    MessageRole,
    AgentType,
    ChatStats,
    MultihopQuery,
    StormRequest,
    StormResponse,
    StormConfig,
    ModelConfig,
    get_available_models,
    get_default_model,
    get_model_by_name
)
from app.core.logging_config import get_logger, LogContext
from app.services.agent_service import AgentService

router = APIRouter()
logger = get_logger("chat")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agents(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    agent_service: AgentService = Depends()
):
    """
    멀티에이전트와 채팅 (STORM 모드 지원)
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # 로그 컨텍스트 설정
    LogContext.set_request_context(request_id, "POST", "/chat")
    LogContext.set_user_context(request.user_id)
    
    try:
        logger.info("Chat request received", 
                   user_id=request.user_id, 
                   message_length=len(request.message),
                   session_id=request.session_id,
                   agent_mode=request.agent_mode)
        
        # 에이전트 서비스 사용 가능성 확인
        if not agent_service:
            raise HTTPException(
                status_code=503, 
                detail="Agent service not available"
            )
        
        # 세션 ID가 없으면 새로 생성
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info("New session created", session_id=session_id)
        
        LogContext.set_session_context(session_id)
        
        # 멀티에이전트 시스템에 메시지 전달 (agent_mode 지원)
        try:
            # ConversationManager로 세션 연속성 확인
            session_exists = False
            conversation_count = 0
            
            if agent_service.conversation_manager:
                context = agent_service.conversation_manager.get_context_for_session(session_id)
                if context:
                    session_exists = True
                    history = await agent_service.get_conversation_history(session_id)
                    conversation_count = len(history)
                    logger.info("Continuing existing ConversationManager session", 
                               session_id=session_id,
                               message_count=conversation_count)
            
            # STORM 모드 또는 일반 모드 처리
            agent_response = await agent_service.process_message(
                message=request.message,
                user_id=request.user_id,
                session_id=session_id,
                context=request.context,
                agent_mode=request.agent_mode or "normal",
                model_name=request.model_name
            )
            
            processing_time = time.time() - start_time
            
            # 세션 메타데이터 구성
            session_metadata = agent_response.get("metadata", {})
            session_metadata.update({
                "session_exists": session_exists,
                "conversation_manager": bool(agent_service.conversation_manager),
                "session_continuity": True,
                "conversation_count": conversation_count,
                "multiturn_support": True,
                "agent_mode": request.agent_mode or "normal",
                "storm_enabled": request.agent_mode == "storm",
                "azure_sql_storage": session_metadata.get("azure_sql_storage", False),
                "processing_time": processing_time
            })
            
            # 응답 구성
            response = ChatResponse(
                response=agent_response.get("response", "죄송합니다. 응답을 생성할 수 없습니다."),
                session_id=session_id,
                agent_info=AgentInfo(
                    name=agent_response.get("agent_name", "Enhanced_MagenticOne_Agent"),
                    type=_map_agent_type(agent_response.get("agent_type", "orchestrator")),
                    capabilities=agent_response.get("tools_used", []),
                    description=agent_response.get("agent_description", "Enhanced AI 에이전트"),
                    confidence=agent_response.get("confidence", 0.8),
                    tools_used=agent_response.get("tools_used", []),
                    execution_time=agent_response.get("execution_time", processing_time)
                ),
                conversation_history=await _get_conversation_history(agent_service, session_id),
                suggested_actions=agent_response.get("suggested_actions", []),
                metadata=session_metadata,
                processing_time=processing_time
            )
            
            # 백그라운드에서 통계 업데이트
            background_tasks.add_task(
                _update_chat_stats,
                agent_service,
                request.user_id,
                session_id,
                processing_time,
                True,
                request.agent_mode or "normal"
            )
            
            logger.info("Chat response generated successfully",
                       session_id=session_id,
                       processing_time=processing_time,
                       agent_type=response.agent_info.type,
                       agent_mode=request.agent_mode)
            
            return response
            
        except Exception as agent_error:
            logger.error("Agent processing failed", 
                        error=str(agent_error),
                        session_id=session_id,
                        agent_mode=request.agent_mode)
            
            # 백그라운드에서 실패 통계 업데이트
            background_tasks.add_task(
                _update_chat_stats,
                agent_service,
                request.user_id,
                session_id,
                time.time() - start_time,
                False,
                request.agent_mode or "normal"
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"에이전트 처리 중 오류가 발생했습니다: {str(agent_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in chat endpoint", 
                    error=str(e),
                    request_id=request_id)
        raise HTTPException(
            status_code=500,
            detail="예상치 못한 오류가 발생했습니다."
        )
    finally:
        LogContext.clear_context()

@router.post("/stream")
async def chat_stream(request: ChatRequest, agent_service: AgentService = Depends()):
    """채팅 스트리밍 엔드포인트 - 실시간 응답"""
    try:
        logger.info("Streaming chat request received", 
                   extra={
                       "user_id": request.user_id,
                       "session_id": request.session_id,
                       "agent_mode": request.agent_mode,
                       "message_length": len(request.message)
                   })

        async def generate_response():
            try:
                logger.info("Processing message stream",
                           extra={
                               "user_id": request.user_id,
                               "session_id": request.session_id,
                               "agent_mode": request.agent_mode
                           })

                # STORM 모드인 경우 스트리밍 처리
                if request.agent_mode == "storm":
                    storm_config = request.context.get("storm_config", {}) if request.context else {}
                    topic = storm_config.get("topic", request.message)
                    editor_count = storm_config.get("editor_count", 1)
                    human_in_the_loop = storm_config.get("human_in_the_loop", False)
                    
                    logger.info("Starting STORM research",
                               extra={
                                   "user_id": request.user_id,
                                   "session_id": request.session_id,
                                   "topic": topic
                               })

                    # 진행상황 스트리밍
                    storm_system = agent_service.storm_service.storm_system
                    
                    final_result = None
                    error_occurred = False
                    
                    try:
                        async for progress in storm_system.run_parallel_storm_research(
                            topic=topic,
                            enable_human_loop=human_in_the_loop,
                            editor_count=editor_count
                        ):
                            # 스트리밍 데이터 전송
                            yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"
                            
                            # 최종 결과 저장
                            if progress.get("type") == "storm_complete":
                                final_result = progress.get("content", "")
                                
                    except Exception as storm_error:
                        error_occurred = True
                        error_msg = f"STORM 연구 중 오류 발생: {str(storm_error)}"
                        logger.error(error_msg)
                        yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
                    
                    # 최종 결과 처리 및 파일 저장
                    if final_result and not error_occurred:
                        # 마크다운 파일 저장
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"storm_article_{timestamp}.md"
                        file_path = f"generated_articles/{filename}"
                        
                        # 디렉토리 생성
                        import os
                        os.makedirs("generated_articles", exist_ok=True)
                        
                        # 파일 저장
                        try:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(final_result)
                            
                            # 최종 완료 메시지와 다운로드 링크 전송
                            completion_data = {
                                "type": "storm_final_complete",
                                "message": "🎉 STORM 연구 완료! 결과를 확인하세요.",
                                "content": final_result,
                                "file_path": file_path,
                                "filename": filename,
                                "download_url": f"/api/v1/download/{filename}",
                                "word_count": len(final_result.split()),
                                "char_count": len(final_result)
                            }
                            yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
                            
                        except Exception as file_error:
                            yield f"data: {json.dumps({'type': 'error', 'message': f'파일 저장 실패: {str(file_error)}'}, ensure_ascii=False)}\n\n"
                    
                    elif not error_occurred:
                        # 결과가 없는 경우
                        yield f"data: {json.dumps({'type': 'error', 'message': 'STORM 연구가 완료되었지만 결과를 생성하지 못했습니다.'}, ensure_ascii=False)}\n\n"

                # 일반 채팅 모드
                else:
                    response = await agent_service.process_message(
                        message=request.message,
                        session_id=request.session_id,
                        user_id=request.user_id,
                        agent_mode=request.agent_mode or "auto",
                        model_name=request.model_name,
                        context=request.context
                    )
                    
                    # 일반 응답 스트리밍
                    for chunk in response.content.split('\n'):
                        if chunk.strip():
                            yield f"data: {json.dumps({'type': 'message', 'content': chunk}, ensure_ascii=False)}\n\n"
                    
                    yield f"data: {json.dumps({'type': 'complete'}, ensure_ascii=False)}\n\n"

            except Exception as e:
                error_msg = f"처리 중 오류 발생: {str(e)}"
                logger.error(error_msg)
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )

    except Exception as e:
        logger.error(f"Streaming endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 파일 다운로드 엔드포인트 추가
@router.get("/download/{filename}")
async def download_file(filename: str):
    """생성된 마크다운 파일 다운로드"""
    try:
        file_path = f"generated_articles/{filename}"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='text/markdown'
        )
        
    except Exception as e:
        logger.error(f"File download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# STORM 단순 연구 API 제거됨 - 모든 요청은 /chat 엔드포인트를 통해 처리
# 프론트엔드에서 agent_mode='storm'과 함께 /chat으로 요청하도록 통합됨

@router.get("/chat/capabilities")
async def get_chat_capabilities(
    agent_service: AgentService = Depends()
):
    """
    채팅 시스템 능력 조회 (STORM 포함)
    """
    try:
        capabilities = {
            "agents": [
                {
                    "type": "hr",
                    "name": "HR 에이전트",
                    "description": "인사 업무 전문 에이전트",
                    "available": True
                },
                {
                    "type": "bulletin",
                    "name": "게시판 에이전트",
                    "description": "공지사항 및 게시판 관리",
                    "available": True
                },
                {
                    "type": "project",
                    "name": "프로젝트 에이전트",
                    "description": "프로젝트 관리 전문 에이전트",
                    "available": True
                },
                {
                    "type": "ktds_info",
                    "name": "KTDS 정보 에이전트",
                    "description": "회사 정보 및 안내",
                    "available": True
                },
                {
                    "type": "storm",
                    "name": "STORM 연구 에이전트",
                    "description": "심층 연구 및 위키 작성",
                    "available": agent_service.storm_service is not None
                }
            ],
            "features": {
                "streaming": False,
                "session_management": True,
                "conversation_history": True,
                "multi_turn": True,
                "storm_research": agent_service.storm_service is not None,
                "model_selection": True
            }
        }
        
        return capabilities
        
    except Exception as e:
        logger.error("Failed to get chat capabilities", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="채팅 시스템 능력 조회에 실패했습니다."
        )

@router.get("/chat/models")
async def get_available_chat_models():
    """
    사용 가능한 AI 모델 목록 조회
    """
    try:
        models = get_available_models()
        default_model = get_default_model()
        
        return {
            "models": [
                {
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "provider": model.provider,
                    "context_window": model.context_window,
                    "max_tokens": model.max_tokens,
                    "capabilities": model.capabilities,
                    "is_default": model.is_default
                }
                for model in models.values()
            ],
            "default_model": default_model.name
        }
        
    except Exception as e:
        logger.error("Failed to get available models", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="사용 가능한 모델 목록을 불러올 수 없습니다."
        )

@router.get("/chat/history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(
    session_id: str,
    agent_service: AgentService = Depends()
):
    """
    세션의 채팅 기록 조회
    """
    try:
        history = await _get_conversation_history(agent_service, session_id)
        return history
    except Exception as e:
        logger.error("Failed to get chat history", 
                    session_id=session_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="채팅 기록을 불러올 수 없습니다."
        )

@router.get("/chat/stats/{user_id}", response_model=ChatStats)
async def get_chat_stats(
    user_id: str,
    agent_service: AgentService = Depends()
):
    """
    사용자의 채팅 통계 조회
    """
    try:
        stats = await agent_service.get_user_chat_stats(user_id)
        
        return ChatStats(
            total_messages=stats.get("total_messages", 0),
            avg_response_time=stats.get("average_response_time", 0.0),
            active_sessions=stats.get("active_sessions", 0),
            agent_usage=stats.get("agent_usage", {})
        )
        
    except Exception as e:
        logger.error("Failed to get chat stats", 
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="채팅 통계를 불러올 수 없습니다."
        )

@router.post("/chat/analyze", response_model=MultihopQuery)
async def analyze_query_complexity(
    request: ChatRequest,
    agent_service: AgentService = Depends()
):
    """
    쿼리 복잡도 분석 (멀티홉 쿼리 감지)
    """
    try:
        analysis = await agent_service.analyze_query_complexity(request.message)
        
        return MultihopQuery(
            query=request.message,
            hops=analysis.get("sub_queries", []),
            context=analysis.get("context", {})
        )
        
    except Exception as e:
        logger.error("Failed to analyze query complexity", 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="쿼리 분석에 실패했습니다."
        )

@router.delete("/chat/session/{session_id}")
async def clear_chat_session(
    session_id: str,
    agent_service: AgentService = Depends()
):
    """
    채팅 세션 삭제
    """
    try:
        await agent_service.clear_session(session_id)
        return {"message": "세션이 성공적으로 삭제되었습니다.", "session_id": session_id}
    except Exception as e:
        logger.error("Failed to clear chat session", 
                    session_id=session_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="세션 삭제에 실패했습니다."
        )

# Helper functions

def _map_agent_type(agent_type_str: str) -> AgentType:
    """문자열을 AgentType enum으로 매핑"""
    mapping = {
        "hr": AgentType.HR,
        "bulletin": AgentType.BULLETIN, 
        "project": AgentType.PROJECT,
        "ktds_info": AgentType.KTDS_INFO,
        "orchestrator": AgentType.ORCHESTRATOR,
        "storm": AgentType.STORM,
        "conversation_orchestrator": AgentType.ORCHESTRATOR,
        "fallback": AgentType.ORCHESTRATOR,
        "default": AgentType.ORCHESTRATOR
    }
    return mapping.get(agent_type_str.lower(), AgentType.ORCHESTRATOR)

async def _get_conversation_history(
    agent_service: AgentService, 
    session_id: str
) -> List[ChatMessage]:
    """세션의 대화 기록 조회"""
    try:
        if hasattr(agent_service, 'get_conversation_history'):
            history = await agent_service.get_conversation_history(session_id)
            
            # 히스토리를 ChatMessage 객체로 변환
            chat_messages = []
            for msg in history:
                try:
                    # ChatMessage 객체인지 확인
                    if isinstance(msg, ChatMessage):
                        # 이미 ChatMessage 객체인 경우 그대로 사용
                        chat_messages.append(msg)
                        continue
                    
                    # 딕셔너리인지 확인 (ConversationManager에서 반환되는 형태)
                    if isinstance(msg, dict):
                        # ConversationManager에서 반환되는 딕셔너리 구조 처리
                        role = msg.get("role", "assistant")
                        content = msg.get("content", "")
                        timestamp = msg.get("timestamp", datetime.now().isoformat())
                        source = msg.get("source", None)
                        metadata = msg.get("metadata", {})
                        
                        # role이 MessageRole enum인지 확인
                        if isinstance(role, MessageRole):
                            role = role.value
                        
                        # timestamp가 문자열인 경우 datetime으로 변환
                        if isinstance(timestamp, str):
                            try:
                                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            except:
                                timestamp = datetime.now()
                        
                        # ChatMessage 객체 생성
                        chat_message = ChatMessage(
                            role=MessageRole(role),
                            content=content,
                            timestamp=timestamp,
                            metadata=metadata or {}
                        )
                        chat_messages.append(chat_message)
                    else:
                        # 다른 객체인 경우 (일반 객체)
                        role = getattr(msg, 'role', 'assistant')
                        if hasattr(role, 'value'):
                            role = role.value
                        content = getattr(msg, 'content', '')
                        timestamp = getattr(msg, 'timestamp', datetime.now())
                        metadata = getattr(msg, 'metadata', {})
                        
                        # ChatMessage 객체 생성
                        chat_message = ChatMessage(
                            role=MessageRole(role),
                            content=content,
                            timestamp=timestamp,
                            metadata=metadata or {}
                        )
                        chat_messages.append(chat_message)
                    
                except Exception as msg_error:
                    logger.warning("Failed to process message in history", 
                                  session_id=session_id, 
                                  error=str(msg_error),
                                  message_type=type(msg).__name__)
                    continue
            
            return chat_messages
        else:
            return []
    except Exception as e:
        logger.warning("Failed to get conversation history", 
                      session_id=session_id, 
                      error=str(e))
        return []

async def _update_chat_stats(
    agent_service: AgentService,
    user_id: str,
    session_id: str,
    processing_time: float,
    success: bool,
    agent_mode: str = "normal"
):
    """백그라운드에서 채팅 통계 업데이트"""
    try:
        if hasattr(agent_service, 'update_chat_stats'):
            await agent_service.update_chat_stats(
                user_id=user_id,
                session_id=session_id,
                processing_time=processing_time,
                success=success
            )
        
        # STORM 모드 통계 추가 로깅
        if agent_mode == "storm":
            logger.info("STORM usage recorded",
                       user_id=user_id,
                       session_id=session_id,
                       success=success,
                       processing_time=processing_time)
                       
    except Exception as e:
        logger.warning("Failed to update chat stats", 
                      user_id=user_id, 
                      agent_mode=agent_mode,
                      error=str(e))
