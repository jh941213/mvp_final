#!/usr/bin/env python3
"""
FastAPI 로깅 설정
구조화된 로깅과 색상 출력 지원
"""

import logging
import sys
from typing import Any, Dict
from pathlib import Path
import structlog
from rich.logging import RichHandler
from rich.console import Console

def setup_logging():
    """
    애플리케이션 로깅 설정
    """
    
    # Rich Console 설정
    console = Console(force_terminal=True)
    
    # 기본 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            RichHandler(
                console=console,
                show_time=True,
                show_path=True,
                markup=True,
                rich_tracebacks=True
            )
        ]
    )
    
    # structlog 설정
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer(colors=True)
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    # FastAPI 관련 로거 설정
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.INFO)
    
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(logging.INFO)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

class StructuredLogger:
    """
    구조화된 로깅을 위한 래퍼 클래스
    """
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
    
    def info(self, message: str, **kwargs):
        """정보 로그"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """경고 로그"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """오류 로그"""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """치명적 오류 로그"""
        self.logger.critical(message, **kwargs)

def get_logger(name: str) -> StructuredLogger:
    """
    구조화된 로거 인스턴스 반환
    """
    return StructuredLogger(name)

# 로그 필터 클래스들
class HealthCheckFilter(logging.Filter):
    """
    헬스체크 요청 필터링
    """
    def filter(self, record):
        return "GET /api/v1/health" not in record.getMessage()

class StaticFileFilter(logging.Filter):
    """
    정적 파일 요청 필터링
    """
    def filter(self, record):
        message = record.getMessage()
        static_paths = ["/static/", "/favicon.ico", "/robots.txt"]
        return not any(path in message for path in static_paths)

def configure_request_logging():
    """
    요청 로깅 설정
    """
    # Uvicorn 액세스 로그에 필터 추가
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.addFilter(HealthCheckFilter())
    access_logger.addFilter(StaticFileFilter())

# 컨텍스트 관리용 로거
class LogContext:
    """
    로그 컨텍스트 관리
    """
    
    @staticmethod
    def set_user_context(user_id: str):
        """사용자 컨텍스트 설정"""
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(user_id=user_id)
    
    @staticmethod
    def set_session_context(session_id: str):
        """세션 컨텍스트 설정"""
        structlog.contextvars.bind_contextvars(session_id=session_id)
    
    @staticmethod
    def set_request_context(request_id: str, method: str, path: str):
        """요청 컨텍스트 설정"""
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=method,
            path=path
        )
    
    @staticmethod
    def clear_context():
        """컨텍스트 초기화"""
        structlog.contextvars.clear_contextvars()

def log_request_middleware():
    """
    요청 로깅 미들웨어 데코레이터
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = get_logger("request")
            try:
                result = await func(*args, **kwargs)
                logger.info("Request completed successfully")
                return result
            except Exception as e:
                logger.error("Request failed", error=str(e))
                raise
        return wrapper
    return decorator

# 기본 로거 인스턴스들
app_logger = get_logger("app")
agent_logger = get_logger("agent")
session_logger = get_logger("session")
api_logger = get_logger("api") 