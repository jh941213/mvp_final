"""
멀티턴 대화 컨텍스트 관리 시스템
AutoGen의 BufferedChatCompletionContext를 참고하여 구현
Azure SQL 영구 저장 지원
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MessageRole(Enum):
    """메시지 역할 정의"""
    USER = "user"
    ASSISTANT = "assistant" 
    SYSTEM = "system"
    AGENT = "agent"

@dataclass
class ChatMessage:
    """채팅 메시지 데이터 클래스"""
    content: str
    role: MessageRole
    timestamp: str
    source: Optional[str] = None  # agent name or user
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "content": self.content,
            "role": self.role.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """딕셔너리에서 생성"""
        return cls(
            content=data["content"],
            role=MessageRole(data["role"]),
            timestamp=data["timestamp"],
            source=data.get("source"),
            metadata=data.get("metadata", {})
        )

class BufferedConversationContext:
    """
    AutoGen의 BufferedChatCompletionContext를 참고한 대화 컨텍스트 관리자
    최근 N개의 메시지만 유지하여 토큰 사용량 최적화
    Azure SQL 상태 저장/복원 지원
    """
    
    def __init__(self, buffer_size: int = 10, system_message: Optional[str] = None, session_id: Optional[str] = None, session_manager=None):
        """
        Args:
            buffer_size: 유지할 최대 메시지 수
            system_message: 시스템 메시지
            session_id: 세션 ID (저장용)
            session_manager: SessionManager 인스턴스 (Azure SQL 저장용)
        """
        self.buffer_size = buffer_size
        self.system_message = system_message
        self.session_id = session_id
        self.session_manager = session_manager
        self.messages: List[ChatMessage] = []
        
        # 시스템 메시지가 있으면 추가
        if system_message:
            self.add_system_message(system_message)
    
    def add_system_message(self, content: str) -> None:
        """시스템 메시지 추가"""
        message = ChatMessage(
            content=content,
            role=MessageRole.SYSTEM,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="system"
        )
        # 시스템 메시지는 맨 앞에 유지
        system_messages = [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
        if system_messages:
            # 기존 시스템 메시지 제거
            self.messages = [msg for msg in self.messages if msg.role != MessageRole.SYSTEM]
        
        self.messages.insert(0, message)
        self._save_to_azure_sql()
        logger.debug("System message added to context")
    
    def add_user_message(self, content: str, source: str = "user", metadata: Optional[Dict[str, Any]] = None) -> None:
        """사용자 메시지 추가"""
        message = ChatMessage(
            content=content,
            role=MessageRole.USER,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            metadata=metadata
        )
        self._add_message(message)
    
    def add_assistant_message(self, content: str, source: str = "assistant", metadata: Optional[Dict[str, Any]] = None) -> None:
        """어시스턴트 메시지 추가"""
        message = ChatMessage(
            content=content,
            role=MessageRole.ASSISTANT,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            metadata=metadata
        )
        self._add_message(message)
    
    def add_agent_message(self, content: str, agent_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """에이전트 메시지 추가"""
        message = ChatMessage(
            content=content,
            role=MessageRole.AGENT,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=agent_name,
            metadata=metadata
        )
        self._add_message(message)
    
    def _add_message(self, message: ChatMessage) -> None:
        """메시지 추가 및 버퍼 관리"""
        self.messages.append(message)
        
        # 시스템 메시지는 제외하고 버퍼 관리
        system_messages = [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
        other_messages = [msg for msg in self.messages if msg.role != MessageRole.SYSTEM]
        
        # 버퍼 크기 초과시 오래된 메시지 제거
        if len(other_messages) > self.buffer_size:
            other_messages = other_messages[-self.buffer_size:]
        
        self.messages = system_messages + other_messages
        
        # Azure SQL에 저장
        self._save_to_azure_sql()
        
        logger.debug(f"Message added. Context size: {len(self.messages)} (system: {len(system_messages)}, others: {len(other_messages)})")
    
    def _save_to_azure_sql(self) -> None:
        """Azure SQL에 대화 컨텍스트 상태 저장"""
        if self.session_manager and self.session_id:
            try:
                state_data = self.save_state()
                self.session_manager.save_agent_state(self.session_id, {
                    'conversation_context': state_data,
                    'context_type': 'buffered_conversation',
                    'last_updated': datetime.now(timezone.utc).isoformat()
                })
                logger.debug(f"Conversation context saved to Azure SQL for session {self.session_id}")
            except Exception as e:
                logger.warning(f"Failed to save conversation context to Azure SQL: {e}")
    
    def _load_from_azure_sql(self) -> bool:
        """Azure SQL에서 대화 컨텍스트 상태 복원"""
        if self.session_manager and self.session_id:
            try:
                agent_state = self.session_manager.load_agent_state(self.session_id)
                if agent_state and 'conversation_context' in agent_state:
                    context_data = agent_state['conversation_context']
                    self.load_state(context_data)
                    logger.info(f"Conversation context loaded from Azure SQL for session {self.session_id}")
                    return True
            except Exception as e:
                logger.warning(f"Failed to load conversation context from Azure SQL: {e}")
        return False
    
    def get_messages(self) -> List[ChatMessage]:
        """모든 메시지 반환"""
        return self.messages.copy()
    
    def get_recent_messages(self, count: int) -> List[ChatMessage]:
        """최근 N개 메시지 반환 (시스템 메시지 제외)"""
        other_messages = [msg for msg in self.messages if msg.role != MessageRole.SYSTEM]
        system_messages = [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
        
        recent_others = other_messages[-count:] if count > 0 else other_messages
        return system_messages + recent_others
    
    def get_context_for_llm(self) -> List[Dict[str, Any]]:
        """LLM API 호출용 컨텍스트 반환"""
        return [msg.to_dict() for msg in self.messages]
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """대화 요약 정보 반환"""
        user_msgs = [msg for msg in self.messages if msg.role == MessageRole.USER]
        assistant_msgs = [msg for msg in self.messages if msg.role == MessageRole.ASSISTANT]
        agent_msgs = [msg for msg in self.messages if msg.role == MessageRole.AGENT]
        
        return {
            "total_messages": len(self.messages),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "agent_messages": len(agent_msgs),
            "buffer_size": self.buffer_size,
            "oldest_message": self.messages[0].timestamp if self.messages else None,
            "latest_message": self.messages[-1].timestamp if self.messages else None,
            "session_id": self.session_id,
            "azure_sql_enabled": self.session_manager is not None
        }
    
    def clear(self) -> None:
        """모든 메시지 제거 (시스템 메시지 유지)"""
        system_messages = [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
        self.messages = system_messages
        self._save_to_azure_sql()
        logger.info("Conversation context cleared")
    
    def save_state(self) -> Dict[str, Any]:
        """현재 상태를 딕셔너리로 저장"""
        return {
            "buffer_size": self.buffer_size,
            "system_message": self.system_message,
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages]
        }
    
    def load_state(self, state: Dict[str, Any]) -> None:
        """상태를 딕셔너리에서 복원"""
        self.buffer_size = state.get("buffer_size", 10)
        self.system_message = state.get("system_message")
        self.session_id = state.get("session_id", self.session_id)
        
        messages_data = state.get("messages", [])
        self.messages = [ChatMessage.from_dict(msg_data) for msg_data in messages_data]
        
        logger.info(f"Conversation context loaded: {len(self.messages)} messages")

class ConversationManager:
    """
    여러 세션의 대화 컨텍스트를 관리하는 매니저
    AutoGen의 상태 관리 방식을 참고
    Azure SQL 영구 저장 지원
    """
    
    def __init__(self, default_buffer_size: int = 10, default_system_message: Optional[str] = None, session_manager=None):
        """
        Args:
            default_buffer_size: 기본 버퍼 크기
            default_system_message: 기본 시스템 메시지
            session_manager: SessionManager 인스턴스 (Azure SQL 저장용)
        """
        self.default_buffer_size = default_buffer_size
        self.default_system_message = default_system_message
        self.session_manager = session_manager
        self.contexts: Dict[str, BufferedConversationContext] = {}
        
        storage_type = "Azure SQL" if session_manager else "메모리"
        logger.info(f"ConversationManager initialized with buffer_size={default_buffer_size}, storage={storage_type}")
    
    def get_or_create_context(self, session_id: str, buffer_size: Optional[int] = None, system_message: Optional[str] = None) -> BufferedConversationContext:
        """세션의 대화 컨텍스트 가져오기 또는 생성"""
        if session_id not in self.contexts:
            context = BufferedConversationContext(
                buffer_size=buffer_size or self.default_buffer_size,
                system_message=system_message or self.default_system_message,
                session_id=session_id,
                session_manager=self.session_manager
            )
            
            # Azure SQL에서 기존 상태 복원 시도
            if not context._load_from_azure_sql():
                logger.info(f"New conversation context created for session: {session_id}")
            
            self.contexts[session_id] = context
        
        return self.contexts[session_id]
    
    def add_conversation_turn(self, session_id: str, user_message: str, assistant_response: str, agent_name: str = "assistant", metadata: Optional[Dict[str, Any]] = None) -> None:
        """대화 턴 추가 (사용자 메시지 + 어시스턴트 응답)"""
        context = self.get_or_create_context(session_id)
        
        # 사용자 메시지 추가
        context.add_user_message(user_message, metadata=metadata)
        
        # 어시스턴트 응답 추가
        context.add_assistant_message(assistant_response, source=agent_name, metadata=metadata)
        
        logger.debug(f"Conversation turn added to session {session_id}")
    
    def get_context_for_session(self, session_id: str) -> Optional[BufferedConversationContext]:
        """세션의 대화 컨텍스트 반환"""
        return self.contexts.get(session_id)
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """세션의 대화 히스토리 반환"""
        context = self.contexts.get(session_id)
        if not context:
            # 메모리에 없으면 Azure SQL에서 복원 시도
            context = self.get_or_create_context(session_id)
            if not context.get_messages():
                return []
        
        messages = context.get_recent_messages(limit) if limit else context.get_messages()
        return [msg.to_dict() for msg in messages]
    
    def clear_session(self, session_id: str) -> bool:
        """세션 삭제"""
        if session_id in self.contexts:
            del self.contexts[session_id]
            
            # Azure SQL에서도 삭제
            if self.session_manager:
                try:
                    self.session_manager.end_session(session_id)
                    logger.info(f"Session context cleared from Azure SQL: {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to clear session from Azure SQL: {e}")
            
            logger.info(f"Session context cleared: {session_id}")
            return True
        return False
    
    def save_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 상태 저장"""
        context = self.contexts.get(session_id)
        if context:
            return context.save_state()
        return None
    
    def load_session_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """세션 상태 복원"""
        try:
            context = BufferedConversationContext(
                buffer_size=10, 
                session_id=session_id,
                session_manager=self.session_manager
            )
            context.load_state(state)
            self.contexts[session_id] = context
            logger.info(f"Session state loaded: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to load session state for {session_id}: {e}")
            return False
    
    def get_active_sessions(self) -> List[str]:
        """활성 세션 ID 목록 반환"""
        return list(self.contexts.keys())
    
    def get_session_stats(self) -> Dict[str, Any]:
        """전체 세션 통계 반환"""
        total_sessions = len(self.contexts)
        total_messages = sum(len(ctx.get_messages()) for ctx in self.contexts.values())
        
        return {
            "total_active_sessions": total_sessions,
            "total_messages": total_messages,
            "default_buffer_size": self.default_buffer_size,
            "session_ids": list(self.contexts.keys()),
            "azure_sql_enabled": self.session_manager is not None,
            "storage_type": "Azure SQL" if self.session_manager else "메모리"
        }
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """비활성 세션 정리"""
        from datetime import timedelta
        
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for session_id, context in self.contexts.items():
            messages = context.get_messages()
            if messages:
                last_message_time = datetime.fromisoformat(messages[-1].timestamp.replace('Z', '+00:00'))
                if last_message_time < cutoff_time:
                    sessions_to_remove.append(session_id)
            else:
                # 메시지가 없는 세션도 제거
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.contexts[session_id]
        
        # Azure SQL에서도 정리
        if self.session_manager:
            try:
                cleaned_count = self.session_manager.cleanup_old_sessions(max_age_hours // 24)
                logger.info(f"Cleaned up {cleaned_count} old sessions from Azure SQL")
            except Exception as e:
                logger.warning(f"Failed to cleanup old sessions from Azure SQL: {e}")
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions")
        return len(sessions_to_remove) 