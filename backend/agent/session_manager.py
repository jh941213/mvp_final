import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio
import logging

try:
    import pyodbc
    from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
    AZURE_SQL_AVAILABLE = True
except ImportError:
    AZURE_SQL_AVAILABLE = False

from config.config import get_database_url, check_azure_sql_config

logger = logging.getLogger(__name__)

Base = declarative_base()

class ConversationHistory(Base):
    __tablename__ = 'conversation_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UNIQUEIDENTIFIER, nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
    message_data = Column(Text, nullable=False)  # JSON 형태의 메시지 데이터
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    agent_type = Column(String(100), nullable=True)
    message_type = Column(String(50), nullable=True)  # 'user', 'assistant', 'system'

class SessionState(Base):
    __tablename__ = 'session_state'
    
    session_id = Column(UNIQUEIDENTIFIER, primary_key=True)
    user_id = Column(String(255), nullable=True, index=True)
    agent_state = Column(Text, nullable=True)  # JSON 형태의 에이전트 상태
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Integer, default=1)  # 1: active, 0: inactive

@dataclass
class SessionInfo:
    session_id: str
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    created_at: Optional[datetime] = None
    is_active: bool = True

class AzureSQLSessionManager:
    """Azure SQL을 사용한 세션 관리자"""
    
    def __init__(self, connection_string: str):
        if not AZURE_SQL_AVAILABLE:
            raise ImportError("Azure SQL 사용을 위해 pyodbc와 sqlalchemy가 필요합니다.")
        
        self.connection_string = connection_string
        self.engine = create_engine(connection_string, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 테이블 생성
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Azure SQL 테이블 생성 완료")
        except Exception as e:
            logger.error(f"Azure SQL 테이블 생성 실패: {e}")
            raise
    
    def create_session(self, user_id: Optional[str] = None, thread_id: Optional[str] = None) -> SessionInfo:
        """새로운 세션 생성"""
        session_id = str(uuid.uuid4())
        
        with self.SessionLocal() as db_session:
            try:
                # 세션 상태 저장
                session_state = SessionState(
                    session_id=session_id,
                    user_id=user_id,
                    agent_state=json.dumps({}),  # 초기 상태는 빈 dict
                    created_at=datetime.utcnow(),
                    is_active=1
                )
                db_session.add(session_state)
                db_session.commit()
                
                logger.info(f"새 세션 생성: {session_id}")
                return SessionInfo(
                    session_id=session_id,
                    user_id=user_id,
                    thread_id=thread_id,
                    created_at=datetime.utcnow(),
                    is_active=True
                )
            except Exception as e:
                db_session.rollback()
                logger.error(f"세션 생성 실패: {e}")
                raise
    
    def save_message(self, session_id: str, message_data: Dict[str, Any], 
                    agent_type: str = None, message_type: str = "user") -> bool:
        """메시지를 데이터베이스에 저장"""
        with self.SessionLocal() as db_session:
            try:
                conversation = ConversationHistory(
                    session_id=session_id,
                    user_id=None,  # 필요시 추가
                    thread_id=None,  # 필요시 추가
                    message_data=json.dumps(message_data, ensure_ascii=False),
                    timestamp=datetime.utcnow(),
                    agent_type=agent_type,
                    message_type=message_type
                )
                db_session.add(conversation)
                db_session.commit()
                logger.debug(f"메시지 저장 완료: {session_id}")
                return True
            except Exception as e:
                db_session.rollback()
                logger.error(f"메시지 저장 실패: {e}")
                return False
    
    def load_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """세션의 대화 히스토리 로드"""
        with self.SessionLocal() as db_session:
            try:
                conversations = db_session.query(ConversationHistory)\
                    .filter(ConversationHistory.session_id == session_id)\
                    .order_by(ConversationHistory.timestamp.desc())\
                    .limit(limit)\
                    .all()
                
                history = []
                for conv in conversations:
                    history.append({
                        'id': conv.id,
                        'session_id': str(conv.session_id),
                        'message_data': json.loads(conv.message_data),
                        'timestamp': conv.timestamp.isoformat(),
                        'agent_type': conv.agent_type,
                        'message_type': conv.message_type
                    })
                
                # 시간 순으로 정렬 (오래된 것부터)
                history.reverse()
                logger.info(f"대화 히스토리 로드 완료: {session_id}, {len(history)}개 메시지")
                return history
            except Exception as e:
                logger.error(f"대화 히스토리 로드 실패: {e}")
                return []
    
    def save_agent_state(self, session_id: str, agent_state: Dict[str, Any]) -> bool:
        """에이전트 상태 저장"""
        with self.SessionLocal() as db_session:
            try:
                session_state = db_session.query(SessionState)\
                    .filter(SessionState.session_id == session_id)\
                    .first()
                
                if session_state:
                    session_state.agent_state = json.dumps(agent_state, ensure_ascii=False)
                    session_state.updated_at = datetime.utcnow()
                else:
                    session_state = SessionState(
                        session_id=session_id,
                        agent_state=json.dumps(agent_state, ensure_ascii=False),
                        created_at=datetime.utcnow(),
                        is_active=1
                    )
                    db_session.add(session_state)
                
                db_session.commit()
                logger.debug(f"에이전트 상태 저장 완료: {session_id}")
                return True
            except Exception as e:
                db_session.rollback()
                logger.error(f"에이전트 상태 저장 실패: {e}")
                return False
    
    def load_agent_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """에이전트 상태 로드"""
        with self.SessionLocal() as db_session:
            try:
                session_state = db_session.query(SessionState)\
                    .filter(SessionState.session_id == session_id)\
                    .first()
                
                if session_state and session_state.agent_state:
                    state = json.loads(session_state.agent_state)
                    logger.debug(f"에이전트 상태 로드 완료: {session_id}")
                    return state
                else:
                    logger.info(f"에이전트 상태 없음: {session_id}")
                    return {}
            except Exception as e:
                logger.error(f"에이전트 상태 로드 실패: {e}")
                return None
    
    def deactivate_session(self, session_id: str) -> bool:
        """세션 비활성화"""
        with self.SessionLocal() as db_session:
            try:
                session_state = db_session.query(SessionState)\
                    .filter(SessionState.session_id == session_id)\
                    .first()
                
                if session_state:
                    session_state.is_active = 0
                    session_state.updated_at = datetime.utcnow()
                    db_session.commit()
                    logger.info(f"세션 비활성화 완료: {session_id}")
                    return True
                else:
                    logger.warning(f"세션을 찾을 수 없음: {session_id}")
                    return False
            except Exception as e:
                db_session.rollback()
                logger.error(f"세션 비활성화 실패: {e}")
                return False
    
    def get_active_sessions(self, user_id: Optional[str] = None) -> List[SessionInfo]:
        """활성 세션 목록 조회"""
        with self.SessionLocal() as db_session:
            try:
                query = db_session.query(SessionState)\
                    .filter(SessionState.is_active == 1)
                
                if user_id:
                    query = query.filter(SessionState.user_id == user_id)
                
                sessions = query.order_by(SessionState.updated_at.desc()).all()
                
                result = []
                for session in sessions:
                    result.append(SessionInfo(
                        session_id=str(session.session_id),
                        user_id=session.user_id,
                        created_at=session.created_at,
                        is_active=True
                    ))
                
                logger.info(f"활성 세션 조회 완료: {len(result)}개")
                return result
            except Exception as e:
                logger.error(f"활성 세션 조회 실패: {e}")
                return []
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """오래된 세션 정리"""
        with self.SessionLocal() as db_session:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_old)
                
                # 대화 히스토리 삭제
                deleted_conversations = db_session.query(ConversationHistory)\
                    .filter(ConversationHistory.timestamp < cutoff_date)\
                    .delete()
                
                # 세션 상태 삭제
                deleted_sessions = db_session.query(SessionState)\
                    .filter(SessionState.updated_at < cutoff_date)\
                    .delete()
                
                db_session.commit()
                logger.info(f"오래된 세션 정리 완료: {deleted_sessions}개 세션, {deleted_conversations}개 대화")
                return deleted_sessions
            except Exception as e:
                db_session.rollback()
                logger.error(f"오래된 세션 정리 실패: {e}")
                return 0

class InMemorySessionManager:
    """메모리 기반 세션 관리자 (테스트용)"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionInfo] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        logger.info("메모리 기반 세션 관리자 초기화 완료")
    
    def create_session(self, user_id: Optional[str] = None, thread_id: Optional[str] = None) -> SessionInfo:
        session_id = str(uuid.uuid4())
        session_info = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at=datetime.utcnow(),
            is_active=True
        )
        self.sessions[session_id] = session_info
        self.conversations[session_id] = []
        self.agent_states[session_id] = {}
        logger.info(f"새 세션 생성: {session_id}")
        return session_info
    
    def save_message(self, session_id: str, message_data: Dict[str, Any], 
                    agent_type: str = None, message_type: str = "user") -> bool:
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            'session_id': session_id,
            'message_data': message_data,
            'timestamp': datetime.utcnow().isoformat(),
            'agent_type': agent_type,
            'message_type': message_type
        })
        return True
    
    def load_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.conversations.get(session_id, [])[-limit:]
    
    def save_agent_state(self, session_id: str, agent_state: Dict[str, Any]) -> bool:
        self.agent_states[session_id] = agent_state
        return True
    
    def load_agent_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.agent_states.get(session_id, {})
    
    def deactivate_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            return True
        return False
    
    def get_active_sessions(self, user_id: Optional[str] = None) -> List[SessionInfo]:
        active_sessions = [s for s in self.sessions.values() if s.is_active]
        if user_id:
            active_sessions = [s for s in active_sessions if s.user_id == user_id]
        return active_sessions

class SessionManager:
    """통합 세션 관리자 - 환경 설정에 따라 Azure SQL 또는 In-Memory 관리자 사용"""
    
    def __init__(self):
        """환경 설정에 따라 적절한 세션 관리자 초기화"""
        self.manager = None
        self.manager_type = "none"
        
        try:
            # 환경 설정 확인
            config_status = check_azure_sql_config()
            database_url = get_database_url()
            
            if config_status['can_connect'] and database_url.startswith('mssql'):
                # Azure SQL 사용
                self.manager = AzureSQLSessionManager(database_url)
                self.manager_type = "azure_sql"
                logger.info("Azure SQL 세션 관리자 초기화 완료")
            else:
                # In-Memory 사용 (개발/테스트)
                self.manager = InMemorySessionManager()
                self.manager_type = "in_memory"
                logger.info("In-Memory 세션 관리자 초기화 완료")
                
        except Exception as e:
            logger.error(f"세션 관리자 초기화 실패: {e}")
            # 폴백으로 In-Memory 관리자 사용
            self.manager = InMemorySessionManager()
            self.manager_type = "in_memory_fallback"
            logger.info("폴백으로 In-Memory 세션 관리자 사용")
    
    def create_session(self, user_id: Optional[str] = None, thread_id: Optional[str] = None) -> str:
        """새로운 세션 생성 - 세션 ID 반환"""
        if self.manager:
            session_info = self.manager.create_session(user_id, thread_id)
            return session_info.session_id
        return str(uuid.uuid4())
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        if self.manager:
            sessions = self.manager.get_active_sessions()
            for session in sessions:
                if session.session_id == session_id:
                    return {
                        'session_id': session.session_id,
                        'user_id': session.user_id,
                        'thread_id': session.thread_id,
                        'created_at': session.created_at.isoformat() if session.created_at else None,
                        'is_active': session.is_active
                    }
        return None
    
    def save_conversation_turn(self, session_id: str, user_message: str, assistant_response: str) -> bool:
        """대화 턴 저장"""
        if not self.manager:
            return False
        
        # 사용자 메시지 저장
        user_success = self.manager.save_message(
            session_id=session_id,
            message_data={'content': user_message, 'role': 'user'},
            message_type='user'
        )
        
        # 어시스턴트 응답 저장
        assistant_success = self.manager.save_message(
            session_id=session_id,
            message_data={'content': assistant_response, 'role': 'assistant'},
            message_type='assistant'
        )
        
        return user_success and assistant_success
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """대화 히스토리 조회"""
        if self.manager:
            return self.manager.load_conversation_history(session_id, limit)
        return []
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 모든 세션 조회"""
        if self.manager:
            sessions = self.manager.get_active_sessions(user_id)
            return [
                {
                    'session_id': s.session_id,
                    'user_id': s.user_id,
                    'thread_id': s.thread_id,
                    'created_at': s.created_at.isoformat() if s.created_at else None,
                    'is_active': s.is_active
                }
                for s in sessions
            ]
        return []
    
    def end_session(self, session_id: str) -> bool:
        """세션 종료"""
        if self.manager:
            return self.manager.deactivate_session(session_id)
        return False
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """오래된 세션 정리"""
        if self.manager and hasattr(self.manager, 'cleanup_old_sessions'):
            return self.manager.cleanup_old_sessions(days)
        return 0
    
    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 조회"""
        if self.manager:
            active_sessions = self.manager.get_active_sessions()
            return {
                'manager_type': self.manager_type,
                'total_active_sessions': len(active_sessions),
                'unique_users': len(set(s.user_id for s in active_sessions if s.user_id)),
                'database_url': get_database_url() if self.manager_type != "none" else None
            }
        return {'manager_type': 'none', 'total_active_sessions': 0}
    
    def save_agent_state(self, session_id: str, agent_state: Dict[str, Any]) -> bool:
        """에이전트 상태 저장"""
        if self.manager:
            return self.manager.save_agent_state(session_id, agent_state)
        return False
    
    def load_agent_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """에이전트 상태 로드"""
        if self.manager:
            return self.manager.load_agent_state(session_id)
        return None 