#!/usr/bin/env python3
"""
헬스체크 API 라우터
시스템 상태 및 서비스 헬스 체크
"""

import time
import psutil
import platform
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.models.system_models import (
    HealthResponse, 
    SystemStatusResponse, 
    ServiceHealthInfo,
    SystemStatus,
    ServiceStatus,
    PerformanceMetrics
)
from app.core.logging_config import get_logger
from app.services.agent_service import AgentService

router = APIRouter()
logger = get_logger("health")

# 서버 시작 시간
_start_time = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    기본 헬스체크
    """
    try:
        uptime = time.time() - _start_time
        
        return HealthResponse(
            status=SystemStatus.HEALTHY,
            timestamp=datetime.now(),
            version="1.0.0",
            uptime_seconds=uptime
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service Unavailable")

@router.get("/health/detailed", response_model=SystemStatusResponse)
async def detailed_health_check(agent_service: AgentService = Depends()):
    """
    상세 헬스체크 - 모든 서비스 상태 포함
    """
    try:
        # 시스템 정보 수집
        system_info = await _get_system_info()
        
        # 서비스별 헬스체크
        services = []
        
        # 에이전트 서비스 체크
        agent_health = await _check_agent_service(agent_service)
        services.append(agent_health)
        
        # 세션 관리자 체크
        session_health = await _check_session_manager(agent_service)
        services.append(session_health)
        
        # Azure 서비스들 체크
        azure_services = await _check_azure_services(agent_service)
        services.extend(azure_services)
        
        # 전체 상태 결정
        overall_status = _determine_overall_status(services)
        
        # 성능 지표 수집
        performance_metrics = await _get_performance_metrics()
        
        return SystemStatusResponse(
            overall_status=overall_status,
            services=services,
            system_info=system_info,
            performance_metrics=performance_metrics,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Health check failed")

@router.get("/health/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """
    성능 지표 조회
    """
    try:
        metrics = await _get_performance_metrics()
        return PerformanceMetrics(**metrics, timestamp=datetime.now())
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@router.get("/health/ready")
async def readiness_check(agent_service: AgentService = Depends()):
    """
    준비 상태 체크 (Kubernetes readiness probe)
    """
    try:
        # 에이전트 서비스 준비 상태 확인
        if agent_service and hasattr(agent_service, 'is_ready'):
            is_ready = await agent_service.is_ready()
            if not is_ready:
                raise HTTPException(status_code=503, detail="Service not ready")
        
        return {"status": "ready", "timestamp": datetime.now()}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/health/live")
async def liveness_check():
    """
    생존 상태 체크 (Kubernetes liveness probe)
    """
    try:
        # 기본적인 생존 상태만 체크
        uptime = time.time() - _start_time
        
        # 5초 이상 실행된 경우에만 LIVE로 간주
        if uptime < 5:
            raise HTTPException(status_code=503, detail="Service starting")
        
        return {"status": "alive", "uptime_seconds": uptime, "timestamp": datetime.now()}
    except Exception as e:
        logger.error("Liveness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not alive")

# Helper functions

async def _get_system_info() -> Dict[str, Any]:
    """시스템 정보 수집"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_mb": round(memory.total / 1024 / 1024, 2),
            "memory_available_mb": round(memory.available / 1024 / 1024, 2),
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            "uptime_seconds": time.time() - _start_time
        }
    except Exception as e:
        logger.warning("Failed to get system info", error=str(e))
        return {"error": "Failed to collect system info"}

async def _check_agent_service(agent_service: AgentService) -> ServiceHealthInfo:
    """에이전트 서비스 헬스체크"""
    start_time = time.time()
    
    try:
        if not agent_service:
            return ServiceHealthInfo(
                name="Agent Service",
                status=ServiceStatus.DOWN,
                response_time_ms=0,
                last_check=datetime.now(),
                error_message="Agent service not initialized"
            )
        
        # 간단한 에이전트 상태 체크
        status = ServiceStatus.UP
        error_message = None
        
        # 에이전트 초기화 상태 확인
        if hasattr(agent_service, 'is_initialized'):
            if not agent_service.is_initialized():
                status = ServiceStatus.DEGRADED
                error_message = "Agent service not fully initialized"
        
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealthInfo(
            name="Agent Service",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now(),
            error_message=error_message,
            details={
                "agent_count": getattr(agent_service, 'agent_count', 0),
                "initialized": getattr(agent_service, 'initialized', False)
            }
        )
        
    except Exception as e:
        return ServiceHealthInfo(
            name="Agent Service",
            status=ServiceStatus.DOWN,
            response_time_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(),
            error_message=str(e)
        )

async def _check_session_manager(agent_service: AgentService) -> ServiceHealthInfo:
    """세션 관리자 헬스체크"""
    start_time = time.time()
    
    try:
        status = ServiceStatus.UP
        error_message = None
        details = {}
        
        # 세션 관리자 상태 확인
        if agent_service and hasattr(agent_service, 'session_manager'):
            session_manager = agent_service.session_manager
            if session_manager:
                details["mode"] = getattr(session_manager, 'mode', 'unknown')
                details["active_sessions"] = getattr(session_manager, 'get_session_count', lambda: 0)()
            else:
                status = ServiceStatus.DOWN
                error_message = "Session manager not available"
        else:
            status = ServiceStatus.UNKNOWN
            error_message = "Cannot check session manager"
        
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealthInfo(
            name="Session Manager",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now(),
            error_message=error_message,
            details=details
        )
        
    except Exception as e:
        return ServiceHealthInfo(
            name="Session Manager",
            status=ServiceStatus.DOWN,
            response_time_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(),
            error_message=str(e)
        )

async def _check_azure_services(agent_service: AgentService) -> list[ServiceHealthInfo]:
    """Azure 서비스들 헬스체크"""
    services = []
    
    # Azure SQL 체크
    sql_health = await _check_azure_sql(agent_service)
    services.append(sql_health)
    
    # Azure OpenAI 체크
    openai_health = await _check_azure_openai()
    services.append(openai_health)
    
    # Azure AI Search 체크
    search_health = await _check_azure_search()
    services.append(search_health)
    
    return services

async def _check_azure_sql(agent_service: AgentService) -> ServiceHealthInfo:
    """Azure SQL 헬스체크"""
    start_time = time.time()
    
    try:
        status = ServiceStatus.UNKNOWN
        error_message = None
        details = {}
        
        if agent_service and hasattr(agent_service, 'session_manager'):
            session_manager = agent_service.session_manager
            if session_manager and hasattr(session_manager, 'test_connection'):
                try:
                    connection_result = await session_manager.test_connection()
                    if connection_result:
                        status = ServiceStatus.UP
                        details["connection_mode"] = getattr(session_manager, 'mode', 'unknown')
                    else:
                        status = ServiceStatus.DEGRADED
                        error_message = "Connection test failed, using fallback"
                except Exception as e:
                    status = ServiceStatus.DEGRADED
                    error_message = f"Azure SQL error: {str(e)}"
        
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealthInfo(
            name="Azure SQL",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now(),
            error_message=error_message,
            details=details
        )
        
    except Exception as e:
        return ServiceHealthInfo(
            name="Azure SQL",
            status=ServiceStatus.DOWN,
            response_time_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(),
            error_message=str(e)
        )

async def _check_azure_openai() -> ServiceHealthInfo:
    """Azure OpenAI 헬스체크"""
    start_time = time.time()
    
    try:
        # 여기서는 기본적인 설정 확인만 수행
        # 실제 API 호출은 비용과 레이트 리밋 때문에 생략
        from app.core.config import get_azure_openai_config
        
        config = get_azure_openai_config()
        status = ServiceStatus.UP if config.get('api_key') and config.get('endpoint') else ServiceStatus.DOWN
        error_message = None if status == ServiceStatus.UP else "Configuration missing"
        
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealthInfo(
            name="Azure OpenAI",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now(),
            error_message=error_message,
            details={"configured": status == ServiceStatus.UP}
        )
        
    except Exception as e:
        return ServiceHealthInfo(
            name="Azure OpenAI",
            status=ServiceStatus.DOWN,
            response_time_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(),
            error_message=str(e)
        )

async def _check_azure_search() -> ServiceHealthInfo:
    """Azure AI Search 헬스체크"""
    start_time = time.time()
    
    try:
        from app.core.config import get_azure_search_config
        
        config = get_azure_search_config()
        status = ServiceStatus.UP if config.get('endpoint') and config.get('key') else ServiceStatus.DOWN
        error_message = None if status == ServiceStatus.UP else "Configuration missing"
        
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealthInfo(
            name="Azure AI Search",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now(),
            error_message=error_message,
            details={"configured": status == ServiceStatus.UP}
        )
        
    except Exception as e:
        return ServiceHealthInfo(
            name="Azure AI Search",
            status=ServiceStatus.DOWN,
            response_time_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(),
            error_message=str(e)
        )

def _determine_overall_status(services: list[ServiceHealthInfo]) -> SystemStatus:
    """전체 시스템 상태 결정"""
    if not services:
        return SystemStatus.WARNING
    
    down_count = sum(1 for s in services if s.status == ServiceStatus.DOWN)
    degraded_count = sum(1 for s in services if s.status == ServiceStatus.DEGRADED)
    
    if down_count > 0:
        return SystemStatus.ERROR
    elif degraded_count > 0:
        return SystemStatus.WARNING
    else:
        return SystemStatus.HEALTHY

async def _get_performance_metrics() -> Dict[str, float]:
    """성능 지표 수집"""
    try:
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        memory_usage_mb = (memory.total - memory.available) / 1024 / 1024
        
        # 디스크 사용률
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        # 네트워크 I/O
        network = psutil.net_io_counters()
        network_in_mb = network.bytes_recv / 1024 / 1024
        network_out_mb = network.bytes_sent / 1024 / 1024
        
        return {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_mb": memory_usage_mb,
            "disk_usage_percent": disk_usage_percent,
            "network_in_mb": network_in_mb,
            "network_out_mb": network_out_mb,
            "active_sessions": 0,  # 실제 세션 수는 서비스에서 가져와야 함
            "requests_per_minute": 0.0,  # 실제 요청 수는 미들웨어에서 수집해야 함
            "average_response_time_ms": 0.0,  # 실제 응답시간은 미들웨어에서 수집해야 함
            "error_rate_percent": 0.0  # 실제 오류율은 미들웨어에서 수집해야 함
        }
        
    except Exception as e:
        logger.warning("Failed to collect performance metrics", error=str(e))
        return {
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0.0,
            "disk_usage_percent": 0.0,
            "network_in_mb": 0.0,
            "network_out_mb": 0.0,
            "active_sessions": 0,
            "requests_per_minute": 0.0,
            "average_response_time_ms": 0.0,
            "error_rate_percent": 0.0
        } 