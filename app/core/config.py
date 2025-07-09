#!/usr/bin/env python3
"""
FastAPI 애플리케이션 설정
환경변수를 통한 설정 관리
"""

import os
from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache

class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    """
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # 환경 설정
    ENVIRONMENT: str = "development"  # development, production, test
    TESTING: bool = False
    
    # CORS 설정
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"
    )
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            # 콤마로 구분된 문자열을 리스트로 변환
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    # Azure SQL 설정
    AZURE_SQL_SERVER: Optional[str] = None
    AZURE_SQL_DATABASE: Optional[str] = None
    AZURE_SQL_USERNAME: Optional[str] = None
    AZURE_SQL_PASSWORD: Optional[str] = None
    AZURE_SQL_CONNECTION_STRING: Optional[str] = None
    AZURE_SQL_PORT: Optional[int] = 1433
    AZURE_SQL_ENCRYPT: Optional[bool] = True
    AZURE_SQL_TRUST_SERVER_CERTIFICATE: Optional[bool] = False
    AZURE_SQL_CONNECTION_TIMEOUT: Optional[int] = 30
    
    # ODBC 설정
    ODBCINI: Optional[str] = None
    ODBCSYSINI: Optional[str] = None
    
    # Azure OpenAI 설정
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_ENDPOINT: Optional[str] = None
    OPENAI_API_VERSION: str = "2024-12-01-preview"
    
    # Legacy Azure OpenAI 설정 (하위 호환성)
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_MODEL: Optional[str] = None
    AZURE_OPENAI_VERSION: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = None
    AZURE_OPENAI_EMBEDDING: Optional[str] = None
    
    # Azure AI Search 설정
    AZURE_SEARCH_ENDPOINT: Optional[str] = None
    AZURE_SEARCH_KEY: Optional[str] = None
    AZURE_SEARCH_INDEX: Optional[str] = None
    
    # 세션 관리 설정
    SESSION_MANAGER_MODE: str = "memory"  # azure 또는 memory
    SESSION_MANAGER_TYPE: str = "in_memory"  # azure_sql, in_memory, in_memory_fallback
    USE_AZURE_SQL: bool = False
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_SESSIONS_PER_USER: int = 10
    
    # 에이전트 시스템 설정
    AGENT_TIMEOUT_SECONDS: int = 30
    MAX_AGENT_ITERATIONS: int = 10
    ENABLE_VERBOSE_LOGGING: bool = False
    
    # API 설정
    API_PREFIX: str = "/api/v1"
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 추가 필드 허용

@lru_cache()
def get_settings() -> Settings:
    """
    설정 인스턴스를 캐시하여 반환
    """
    return Settings()

def get_azure_sql_config():
    """
    Azure SQL 설정을 딕셔너리로 반환
    """
    settings = get_settings()
    return {
        'server': settings.AZURE_SQL_SERVER,
        'database': settings.AZURE_SQL_DATABASE,
        'username': settings.AZURE_SQL_USERNAME,
        'password': settings.AZURE_SQL_PASSWORD,
        'connection_string': settings.AZURE_SQL_CONNECTION_STRING,
        'mode': settings.SESSION_MANAGER_MODE,
    }

def get_azure_openai_config():
    """
    Azure OpenAI 설정을 딕셔너리로 반환
    """
    settings = get_settings()
    return {
        'api_key': settings.OPENAI_API_KEY or settings.AZURE_OPENAI_API_KEY,
        'endpoint': settings.OPENAI_API_ENDPOINT or settings.AZURE_OPENAI_ENDPOINT,
        'api_version': settings.OPENAI_API_VERSION or settings.AZURE_OPENAI_API_VERSION,
    }

def get_openai_config():
    """
    OpenAI 설정을 딕셔너리로 반환 (새로운 함수)
    """
    settings = get_settings()
    return {
        'api_key': settings.OPENAI_API_KEY or settings.AZURE_OPENAI_API_KEY,
        'endpoint': settings.OPENAI_API_ENDPOINT or settings.AZURE_OPENAI_ENDPOINT,
        'api_version': settings.OPENAI_API_VERSION or settings.AZURE_OPENAI_API_VERSION,
    }

def get_azure_search_config():
    """
    Azure AI Search 설정을 딕셔너리로 반환
    """
    settings = get_settings()
    return {
        'endpoint': settings.AZURE_SEARCH_ENDPOINT,
        'key': settings.AZURE_SEARCH_KEY,
        'index': settings.AZURE_SEARCH_INDEX,
    }

def validate_configuration():
    """
    필수 설정이 올바르게 구성되었는지 확인
    """
    settings = get_settings()
    errors = []
    
    # Azure OpenAI 검증
    if not (settings.OPENAI_API_KEY or settings.AZURE_OPENAI_API_KEY):
        errors.append("OPENAI_API_KEY 또는 AZURE_OPENAI_API_KEY가 설정되지 않았습니다.")
    
    if not (settings.OPENAI_API_ENDPOINT or settings.AZURE_OPENAI_ENDPOINT):
        errors.append("OPENAI_API_ENDPOINT 또는 AZURE_OPENAI_ENDPOINT가 설정되지 않았습니다.")
    
    # Azure SQL 검증 (azure 모드일 때만)
    if settings.SESSION_MANAGER_MODE == "azure":
        if not settings.AZURE_SQL_SERVER:
            errors.append("Azure 모드에서 AZURE_SQL_SERVER가 설정되지 않았습니다.")
        if not settings.AZURE_SQL_DATABASE:
            errors.append("Azure 모드에서 AZURE_SQL_DATABASE가 설정되지 않았습니다.")
        if not settings.AZURE_SQL_USERNAME:
            errors.append("Azure 모드에서 AZURE_SQL_USERNAME이 설정되지 않았습니다.")
        if not settings.AZURE_SQL_PASSWORD:
            errors.append("Azure 모드에서 AZURE_SQL_PASSWORD가 설정되지 않았습니다.")
    
    return errors

def print_configuration():
    """
    현재 설정 상태를 출력
    """
    settings = get_settings()
    
    print("🔧 FastAPI 서버 설정")
    print("=" * 50)
    print(f"서버: {settings.HOST}:{settings.PORT}")
    print(f"디버그 모드: {settings.DEBUG}")
    print(f"로그 레벨: {settings.LOG_LEVEL}")
    print(f"세션 관리 모드: {settings.SESSION_MANAGER_MODE}")
    print(f"에이전트 타임아웃: {settings.AGENT_TIMEOUT_SECONDS}초")
    print(f"API 접두사: {settings.API_PREFIX}")
    print(f"CORS 허용 도메인: {', '.join(settings.ALLOWED_ORIGINS)}")
    
    # 설정 검증
    errors = validate_configuration()
    if errors:
        print("\n❌ 설정 오류:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ 모든 설정이 올바르게 구성되었습니다.")

if __name__ == "__main__":
    print_configuration() 