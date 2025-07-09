#!/usr/bin/env python3
"""
시스템 관리 관련 Pydantic 모델
헬스체크, 상태 모니터링, 설정 API 스키마
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class SystemStatus(str, Enum):
    """시스템 상태 열거형"""
    HEALTHY = "healthy"
    WARNING = "warning"  
    ERROR = "error"
    MAINTENANCE = "maintenance"

class ServiceStatus(str, Enum):
    """서비스 상태 열거형"""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class HealthResponse(BaseModel):
    """헬스체크 응답 모델"""
    status: SystemStatus = Field(..., description="전체 시스템 상태")
    timestamp: datetime = Field(default_factory=datetime.now, description="체크 시간")
    version: str = Field(..., description="애플리케이션 버전")
    uptime_seconds: float = Field(..., description="업타임 (초)")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-07-08T14:30:00Z",
                "version": "1.0.0",
                "uptime_seconds": 3600.5
            }
        }

class ServiceHealthInfo(BaseModel):
    """서비스 헬스 정보"""
    name: str = Field(..., description="서비스 이름")
    status: ServiceStatus = Field(..., description="서비스 상태")
    response_time_ms: float = Field(..., description="응답 시간 (밀리초)")
    last_check: datetime = Field(..., description="마지막 체크 시간")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 상세 정보")

class SystemStatusResponse(BaseModel):
    """시스템 상태 응답 모델"""
    overall_status: SystemStatus = Field(..., description="전체 시스템 상태")
    services: List[ServiceHealthInfo] = Field(..., description="서비스별 상태")
    system_info: Dict[str, Any] = Field(..., description="시스템 정보")
    performance_metrics: Dict[str, float] = Field(..., description="성능 지표")
    timestamp: datetime = Field(default_factory=datetime.now, description="조회 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "overall_status": "healthy",
                "services": [],
                "system_info": {
                    "python_version": "3.11.0",
                    "platform": "darwin",
                    "memory_usage_mb": 256.5
                },
                "performance_metrics": {
                    "avg_response_time_ms": 150.5,
                    "requests_per_minute": 45.2,
                    "error_rate": 0.01
                },
                "timestamp": "2024-07-08T14:30:00Z"
            }
        }

class ConfigResponse(BaseModel):
    """설정 응답 모델"""
    config_key: str = Field(..., description="설정 키")
    config_value: Any = Field(..., description="설정 값")
    description: Optional[str] = Field(None, description="설정 설명")
    is_sensitive: bool = Field(False, description="민감 정보 여부")
    last_updated: Optional[datetime] = Field(None, description="마지막 업데이트 시간")

class SystemConfigResponse(BaseModel):
    """시스템 설정 응답 모델"""
    configs: List[ConfigResponse] = Field(..., description="설정 목록")
    environment: str = Field(..., description="환경 (dev/prod)")
    last_reload: Optional[datetime] = Field(None, description="마지막 설정 리로드 시간")

class ErrorResponse(BaseModel):
    """오류 응답 모델"""
    error_code: str = Field(..., description="오류 코드")
    error_message: str = Field(..., description="오류 메시지")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="오류 상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="오류 발생 시간")
    request_id: Optional[str] = Field(None, description="요청 ID")
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "AGENT_TIMEOUT",
                "error_message": "에이전트 응답 시간 초과",
                "details": {"timeout_seconds": 30, "agent_type": "hr"},
                "timestamp": "2024-07-08T14:30:00Z",
                "request_id": "req_123456"
            }
        }

class PerformanceMetrics(BaseModel):
    """성능 지표 모델"""
    cpu_usage_percent: float = Field(..., description="CPU 사용률 (%)")
    memory_usage_mb: float = Field(..., description="메모리 사용량 (MB)")
    disk_usage_percent: float = Field(..., description="디스크 사용률 (%)")
    network_in_mb: float = Field(..., description="네트워크 입력 (MB)")
    network_out_mb: float = Field(..., description="네트워크 출력 (MB)")
    active_sessions: int = Field(..., description="활성 세션 수")
    requests_per_minute: float = Field(..., description="분당 요청 수")
    average_response_time_ms: float = Field(..., description="평균 응답 시간 (ms)")
    error_rate_percent: float = Field(..., description="오류율 (%)")
    timestamp: datetime = Field(default_factory=datetime.now, description="측정 시간")

class SystemAlert(BaseModel):
    """시스템 알림 모델"""
    alert_id: str = Field(..., description="알림 ID")
    level: str = Field(..., description="알림 레벨 (info/warning/error/critical)")
    title: str = Field(..., description="알림 제목")
    message: str = Field(..., description="알림 메시지")
    source: str = Field(..., description="알림 소스")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    resolved_at: Optional[datetime] = Field(None, description="해결 시간")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")

class SystemStatsResponse(BaseModel):
    """시스템 통계 응답 모델"""
    uptime_seconds: float = Field(..., description="업타임 (초)")
    total_requests: int = Field(..., description="총 요청 수")
    successful_requests: int = Field(..., description="성공한 요청 수")
    failed_requests: int = Field(..., description="실패한 요청 수")
    active_users: int = Field(..., description="활성 사용자 수")
    active_sessions: int = Field(..., description="활성 세션 수")
    average_response_time_ms: float = Field(..., description="평균 응답 시간 (ms)")
    peak_concurrent_users: int = Field(..., description="최대 동시 사용자 수")
    data_processed_mb: float = Field(..., description="처리된 데이터량 (MB)")
    agent_calls_total: int = Field(..., description="총 에이전트 호출 수")
    last_reset: datetime = Field(..., description="마지막 통계 리셋 시간")

class LogLevel(str, Enum):
    """로그 레벨 열거형"""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogConfigRequest(BaseModel):
    """로그 설정 요청 모델"""
    level: LogLevel = Field(..., description="로그 레벨")
    logger_name: Optional[str] = Field(None, description="특정 로거 이름")
    enable_file_logging: Optional[bool] = Field(None, description="파일 로깅 활성화")
    log_file_path: Optional[str] = Field(None, description="로그 파일 경로")

class MaintenanceMode(BaseModel):
    """유지보수 모드 모델"""
    enabled: bool = Field(..., description="유지보수 모드 활성화 여부")
    message: Optional[str] = Field(None, description="유지보수 메시지")
    estimated_duration_minutes: Optional[int] = Field(None, description="예상 소요 시간 (분)")
    allowed_ips: Optional[List[str]] = Field(default_factory=list, description="허용된 IP 목록")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간") 