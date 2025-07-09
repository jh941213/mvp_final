#!/usr/bin/env python3
"""
세션 관리 관련 Pydantic 모델
세션 생성, 조회, 관리 API 스키마
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from .chat_models import ChatMessage

class SessionStatus(str, Enum):
    """세션 상태 열거형"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CLOSED = "closed"

class SessionCreateRequest(BaseModel):
    """세션 생성 요청 모델"""
    user_id: str = Field(..., description="사용자 ID")
    session_name: Optional[str] = Field(None, description="세션 이름")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="세션 메타데이터")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "session_name": "급여 관련 문의",
                "metadata": {"department": "HR", "priority": "normal"}
            }
        }

class SessionResponse(BaseModel):
    """세션 응답 모델"""
    session_id: str = Field(..., description="세션 ID")
    user_id: str = Field(..., description="사용자 ID")
    session_name: Optional[str] = Field(None, description="세션 이름")
    status: SessionStatus = Field(..., description="세션 상태")
    created_at: datetime = Field(..., description="생성 시간")
    last_activity: datetime = Field(..., description="마지막 활동 시간")
    message_count: int = Field(..., description="메시지 수")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="세션 메타데이터")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "session_name": "급여 관련 문의",
                "status": "active",
                "created_at": "2024-07-08T14:30:00Z",
                "last_activity": "2024-07-08T14:45:00Z",
                "message_count": 5,
                "metadata": {"department": "HR"}
            }
        }

class SessionListResponse(BaseModel):
    """세션 목록 응답 모델"""
    sessions: List[SessionResponse] = Field(..., description="세션 목록")
    total_count: int = Field(..., description="총 세션 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    
    class Config:
        schema_extra = {
            "example": {
                "sessions": [],
                "total_count": 25,
                "page": 1,
                "page_size": 10,
                "has_next": True
            }
        }

class MessageResponse(BaseModel):
    """메시지 응답 모델"""
    message_id: str = Field(..., description="메시지 ID")
    session_id: str = Field(..., description="세션 ID")
    message: ChatMessage = Field(..., description="메시지 내용")
    created_at: datetime = Field(..., description="생성 시간")

class SessionHistoryResponse(BaseModel):
    """세션 기록 응답 모델"""
    session_id: str = Field(..., description="세션 ID")
    messages: List[MessageResponse] = Field(..., description="메시지 목록")
    total_messages: int = Field(..., description="총 메시지 수")
    session_info: SessionResponse = Field(..., description="세션 정보")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "messages": [],
                "total_messages": 5,
                "session_info": {}
            }
        }

class SessionUpdateRequest(BaseModel):
    """세션 업데이트 요청 모델"""
    session_name: Optional[str] = Field(None, description="세션 이름")
    status: Optional[SessionStatus] = Field(None, description="세션 상태")
    metadata: Optional[Dict[str, Any]] = Field(None, description="세션 메타데이터")

class SessionStatsResponse(BaseModel):
    """세션 통계 응답 모델"""
    user_id: str = Field(..., description="사용자 ID")
    total_sessions: int = Field(..., description="총 세션 수")
    active_sessions: int = Field(..., description="활성 세션 수")
    total_messages: int = Field(..., description="총 메시지 수")
    average_session_duration: float = Field(..., description="평균 세션 지속 시간 (분)")
    last_activity: Optional[datetime] = Field(None, description="마지막 활동 시간")
    most_active_hour: Optional[int] = Field(None, description="가장 활발한 시간대")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "total_sessions": 15,
                "active_sessions": 2,
                "total_messages": 87,
                "average_session_duration": 12.5,
                "last_activity": "2024-07-08T14:45:00Z",
                "most_active_hour": 14
            }
        }

class SessionQueryParams(BaseModel):
    """세션 쿼리 파라미터"""
    user_id: Optional[str] = Field(None, description="사용자 ID 필터")
    status: Optional[SessionStatus] = Field(None, description="상태 필터")
    page: int = Field(1, ge=1, description="페이지 번호")
    page_size: int = Field(10, ge=1, le=100, description="페이지 크기")
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서 (asc/desc)")
    search: Optional[str] = Field(None, description="검색어")

class SessionExportRequest(BaseModel):
    """세션 내보내기 요청 모델"""
    session_ids: List[str] = Field(..., description="내보낼 세션 ID 목록")
    format: str = Field("json", description="내보내기 형식 (json/csv)")
    include_metadata: bool = Field(True, description="메타데이터 포함 여부")

class SessionImportRequest(BaseModel):
    """세션 가져오기 요청 모델"""
    data: Dict[str, Any] = Field(..., description="가져올 세션 데이터")
    user_id: str = Field(..., description="대상 사용자 ID")
    merge_strategy: str = Field("append", description="병합 전략 (append/replace)")

class SessionBackupResponse(BaseModel):
    """세션 백업 응답 모델"""
    backup_id: str = Field(..., description="백업 ID")
    created_at: datetime = Field(..., description="백업 생성 시간")
    session_count: int = Field(..., description="백업된 세션 수")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    download_url: Optional[str] = Field(None, description="다운로드 URL") 