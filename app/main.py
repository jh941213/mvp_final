#!/usr/bin/env python3
"""
KTDS MagenticOne FastAPI 백엔드 서버
멀티에이전트 시스템과 세션 관리를 REST API로 제공
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
import logging
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from app.api.routes import chat, session, health, system
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.middleware.error_handler import add_error_handlers
from app.services.agent_service import AgentService

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

# 설정 로드
settings = get_settings()

# 전역 에이전트 서비스
agent_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    """
    global agent_service
    
    # 시작 시 초기화
    logger.info("🚀 KTDS MagenticOne 서버 시작 중...")
    
    try:
        # 에이전트 서비스 초기화
        agent_service = AgentService()
        await agent_service.initialize()
        
        # FastAPI 앱에 서비스 주입
        app.state.agent_service = agent_service
        
        logger.info("✅ 에이전트 서비스 초기화 완료")
        logger.info(f"🌐 서버가 {settings.HOST}:{settings.PORT}에서 실행 중")
        
    except Exception as e:
        logger.error(f"❌ 서버 시작 실패: {e}")
        raise
    
    yield
    
    # 종료 시 정리
    logger.info("🛑 KTDS MagenticOne 서버 종료 중...")
    if agent_service:
        await agent_service.cleanup()
    logger.info("✅ 서버 종료 완료")

# FastAPI 앱 생성
app = FastAPI(
    title="KTDS MagenticOne API",
    description="KTDS 멀티에이전트 시스템 REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 에러 핸들러 추가
add_error_handlers(app)

# API 라우터 등록
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(session.router, prefix="/api/v1", tags=["session"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])

@app.get("/")
async def root():
    """
    루트 엔드포인트
    """
    return {
        "message": "KTDS MagenticOne API 서버",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

def get_agent_service():
    """
    에이전트 서비스 의존성 주입
    """
    return agent_service

# 의존성 주입을 위한 함수
app.dependency_overrides[AgentService] = get_agent_service

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 