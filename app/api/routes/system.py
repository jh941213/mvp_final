#!/usr/bin/env python3
"""
시스템 관리 API 라우터
시스템 설정, 통계, 관리 기능
"""

from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends

from app.models.system_models import (
    SystemStatsResponse,
    SystemConfigResponse,
    ConfigResponse,
    LogConfigRequest,
    MaintenanceMode,
    LogLevel
)
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.services.agent_service import AgentService

router = APIRouter()
logger = get_logger("system")

@router.get("/system/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    agent_service: AgentService = Depends()
):
    """
    시스템 통계 조회
    """
    try:
        import time
        import psutil
        
        # 기본 시스템 통계
        uptime_seconds = time.time() - getattr(get_system_stats, '_start_time', time.time())
        
        # 성능 지표
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # 에이전트 통계
        agent_calls_total = 0
        active_sessions = 0
        active_users = 0
        
        if agent_service and agent_service.session_manager:
            if hasattr(agent_service.session_manager, 'get_system_stats'):
                agent_stats = await agent_service.session_manager.get_system_stats()
                agent_calls_total = agent_stats.get('total_calls', 0)
                active_sessions = agent_stats.get('active_sessions', 0)
                active_users = agent_stats.get('active_users', 0)
        
        return SystemStatsResponse(
            uptime_seconds=uptime_seconds,
            total_requests=getattr(get_system_stats, '_total_requests', 0),
            successful_requests=getattr(get_system_stats, '_successful_requests', 0),
            failed_requests=getattr(get_system_stats, '_failed_requests', 0),
            active_users=active_users,
            active_sessions=active_sessions,
            average_response_time_ms=150.0,  # TODO: 실제 측정 구현
            peak_concurrent_users=getattr(get_system_stats, '_peak_users', 0),
            data_processed_mb=getattr(get_system_stats, '_data_processed', 0.0),
            agent_calls_total=agent_calls_total,
            last_reset=datetime.now()
        )
        
    except Exception as e:
        logger.error("Failed to get system stats", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="시스템 통계 조회에 실패했습니다."
        )

# 시작 시간 저장
setattr(get_system_stats, '_start_time', datetime.now().timestamp())

@router.get("/system/config", response_model=SystemConfigResponse)
async def get_system_config():
    """
    시스템 설정 조회
    """
    try:
        settings = get_settings()
        
        configs = []
        
        # 공개 가능한 설정들
        public_configs = {
            "HOST": settings.HOST,
            "PORT": settings.PORT,
            "DEBUG": settings.DEBUG,
            "LOG_LEVEL": settings.LOG_LEVEL,
            "SESSION_MANAGER_MODE": settings.SESSION_MANAGER_MODE,
            "ALLOWED_ORIGINS": ",".join(settings.ALLOWED_ORIGINS),
        }
        
        for key, value in public_configs.items():
            configs.append(ConfigResponse(
                config_key=key,
                config_value=value,
                description=f"{key} 설정",
                is_sensitive=False,
                last_updated=datetime.now()
            ))
        
        # 민감한 설정들 (마스킹)
        sensitive_configs = {
            "AZURE_SQL_SERVER": settings.AZURE_SQL_SERVER,
            "AZURE_OPENAI_ENDPOINT": settings.AZURE_OPENAI_ENDPOINT,
            "AZURE_SEARCH_ENDPOINT": settings.AZURE_SEARCH_ENDPOINT,
        }
        
        for key, value in sensitive_configs.items():
            if value:
                # URL이나 서버 주소는 일부만 표시
                masked_value = f"{value[:10]}***{value[-5:]}" if len(value) > 15 else "***"
            else:
                masked_value = "설정되지 않음"
                
            configs.append(ConfigResponse(
                config_key=key,
                config_value=masked_value,
                description=f"{key} 설정 (마스킹됨)",
                is_sensitive=True,
                last_updated=datetime.now()
            ))
        
        return SystemConfigResponse(
            configs=configs,
            environment="production" if not settings.DEBUG else "development",
            last_reload=datetime.now()
        )
        
    except Exception as e:
        logger.error("Failed to get system config", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="시스템 설정 조회에 실패했습니다."
        )

@router.post("/system/log-config")
async def update_log_config(
    request: LogConfigRequest
):
    """
    로그 설정 업데이트
    """
    try:
        import logging
        
        # 로그 레벨 업데이트
        if request.logger_name:
            target_logger = logging.getLogger(request.logger_name)
        else:
            target_logger = logging.getLogger()
        
        target_logger.setLevel(getattr(logging, request.level.value))
        
        logger.info("Log configuration updated", 
                   level=request.level.value,
                   logger_name=request.logger_name)
        
        return {
            "message": "로그 설정이 업데이트되었습니다.",
            "level": request.level.value,
            "logger_name": request.logger_name or "root"
        }
        
    except Exception as e:
        logger.error("Failed to update log config", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="로그 설정 업데이트에 실패했습니다."
        )

@router.get("/system/maintenance", response_model=MaintenanceMode)
async def get_maintenance_mode():
    """
    유지보수 모드 상태 조회
    """
    try:
        # 유지보수 모드는 현재 구현되지 않음
        return MaintenanceMode(
            enabled=False,
            message=None,
            estimated_duration_minutes=None,
            allowed_ips=[],
            start_time=None,
            end_time=None
        )
        
    except Exception as e:
        logger.error("Failed to get maintenance mode", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="유지보수 모드 조회에 실패했습니다."
        )

@router.post("/system/maintenance")
async def set_maintenance_mode(
    maintenance: MaintenanceMode
):
    """
    유지보수 모드 설정
    """
    try:
        # TODO: 실제 유지보수 모드 구현
        logger.info("Maintenance mode requested", 
                   enabled=maintenance.enabled,
                   message=maintenance.message)
        
        return {
            "message": f"유지보수 모드가 {'활성화' if maintenance.enabled else '비활성화'}되었습니다.",
            "maintenance_mode": maintenance.dict()
        }
        
    except Exception as e:
        logger.error("Failed to set maintenance mode", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="유지보수 모드 설정에 실패했습니다."
        )

@router.post("/system/restart")
async def restart_system():
    """
    시스템 재시작 (에이전트 서비스만)
    """
    try:
        # TODO: 실제 재시작 구현 (graceful shutdown & restart)
        logger.warning("System restart requested")
        
        return {
            "message": "시스템 재시작이 요청되었습니다.",
            "status": "pending",
            "estimated_downtime_seconds": 30
        }
        
    except Exception as e:
        logger.error("Failed to restart system", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="시스템 재시작에 실패했습니다."
        )

@router.get("/system/version")
async def get_system_version():
    """
    시스템 버전 정보 조회
    """
    try:
        import sys
        import platform
        
        return {
            "application_version": "1.0.0",
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "build_date": "2025-07-08",
            "commit_hash": "latest",
            "environment": "production" if not get_settings().DEBUG else "development"
        }
        
    except Exception as e:
        logger.error("Failed to get system version", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="시스템 버전 정보 조회에 실패했습니다."
        )

@router.get("/system/environment")
async def get_environment_info():
    """
    환경 정보 조회
    """
    try:
        import os
        import platform
        import psutil
        
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_space_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "timezone": str(datetime.now().astimezone().tzinfo),
            "environment_variables_count": len([k for k in os.environ.keys() if not k.startswith('_')]),
            "hostname": platform.node()
        }
        
    except Exception as e:
        logger.error("Failed to get environment info", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="환경 정보 조회에 실패했습니다."
        )

@router.post("/system/reset-stats")
async def reset_system_stats():
    """
    시스템 통계 리셋
    """
    try:
        # 통계 카운터 리셋
        setattr(get_system_stats, '_total_requests', 0)
        setattr(get_system_stats, '_successful_requests', 0)
        setattr(get_system_stats, '_failed_requests', 0)
        setattr(get_system_stats, '_peak_users', 0)
        setattr(get_system_stats, '_data_processed', 0.0)
        setattr(get_system_stats, '_start_time', datetime.now().timestamp())
        
        logger.info("System statistics reset")
        
        return {
            "message": "시스템 통계가 리셋되었습니다.",
            "reset_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to reset system stats", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="시스템 통계 리셋에 실패했습니다."
        ) 