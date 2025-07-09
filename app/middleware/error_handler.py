"""
FastAPI 에러 핸들링 미들웨어
HTTP 예외 및 시스템 에러에 대한 표준화된 응답 제공
"""

import logging
import traceback
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)

def add_error_handlers(app: FastAPI) -> None:
    """
    FastAPI 앱에 에러 핸들러 추가
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """
        HTTP 예외 처리
        """
        logger.warning(f"HTTP 에러 {exc.status_code}: {exc.detail} - {request.url}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "HTTP_EXCEPTION",
                    "code": exc.status_code,
                    "message": exc.detail,
                    "path": str(request.url.path)
                }
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """
        Starlette HTTP 예외 처리
        """
        logger.warning(f"Starlette HTTP 에러 {exc.status_code}: {exc.detail} - {request.url}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "HTTP_EXCEPTION",
                    "code": exc.status_code,
                    "message": exc.detail,
                    "path": str(request.url.path)
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        요청 검증 에러 처리
        """
        logger.warning(f"검증 에러: {exc.errors()} - {request.url}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "VALIDATION_ERROR",
                    "code": 422,
                    "message": "요청 데이터 검증 실패",
                    "details": exc.errors(),
                    "path": str(request.url.path)
                }
            }
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """
        Pydantic 검증 에러 처리
        """
        logger.warning(f"Pydantic 검증 에러: {exc.errors()} - {request.url}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "VALIDATION_ERROR",
                    "code": 422,
                    "message": "데이터 검증 실패",
                    "details": exc.errors(),
                    "path": str(request.url.path)
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        일반 예외 처리 (마지막 처리기)
        """
        logger.error(f"예상치 못한 에러: {type(exc).__name__}: {str(exc)} - {request.url}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "INTERNAL_SERVER_ERROR",
                    "code": 500,
                    "message": "서버 내부 오류가 발생했습니다",
                    "path": str(request.url.path)
                }
            }
        )
    
    logger.info("✅ 에러 핸들러 설정 완료") 