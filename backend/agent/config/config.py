"""
Azure SQL 연결 설정 및 API 키 관리
"""
import os
from typing import Optional

# Azure SQL 설정 불러오기
try:
    from azure_sql_config import get_azure_sql_config, get_azure_sql_connection_string, set_environment_variables
    # 환경 변수 자동 설정
    set_environment_variables()
except ImportError:
    # 환경 변수에서 직접 읽기
    pass

class AzureSQLConfig:
    """Azure SQL 연결 설정"""
    
    # Azure SQL 연결 문자열 (환경 변수에서 읽음)
    CONNECTION_STRING = os.getenv("AZURE_SQL_CONNECTION_STRING")
    
    # 개별 설정 옵션들
    SERVER = os.getenv("AZURE_SQL_SERVER", "your-server.database.windows.net")
    DATABASE = os.getenv("AZURE_SQL_DATABASE", "your-database")
    USERNAME = os.getenv("AZURE_SQL_USERNAME", "your-username")
    PASSWORD = os.getenv("AZURE_SQL_PASSWORD", "your-password")
    
    # 기본 연결 문자열 생성
    @classmethod
    def get_connection_string(cls) -> Optional[str]:
        """Azure SQL 연결 문자열 반환"""
        if cls.CONNECTION_STRING:
            return cls.CONNECTION_STRING
        
        if all([cls.SERVER, cls.DATABASE, cls.USERNAME, cls.PASSWORD]):
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={cls.SERVER};"
                f"DATABASE={cls.DATABASE};"
                f"UID={cls.USERNAME};"
                f"PWD={cls.PASSWORD};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )
        
        return None
    
    # SQLAlchemy 연결 URL 생성
    @classmethod
    def get_sqlalchemy_url(cls) -> Optional[str]:
        """SQLAlchemy 연결 URL 반환"""
        if cls.CONNECTION_STRING:
            return f"mssql+pyodbc:///?odbc_connect={cls.CONNECTION_STRING}"
        
        if all([cls.SERVER, cls.DATABASE, cls.USERNAME, cls.PASSWORD]):
            return (
                f"mssql+pyodbc://{cls.USERNAME}:{cls.PASSWORD}@{cls.SERVER}/"
                f"{cls.DATABASE}?driver=ODBC+Driver+17+for+SQL+Server"
                f"&encrypt=yes&trustServerCertificate=no&connectionTimeout=30"
            )
        
        return None
    
    # 테스트용 인메모리 SQLite 설정
    @classmethod
    def get_test_db_url(cls) -> str:
        """테스트용 인메모리 SQLite URL 반환"""
        return "sqlite:///:memory:"
    
    # 개발용 로컬 SQLite 설정
    @classmethod
    def get_dev_db_url(cls) -> str:
        """개발용 로컬 SQLite URL 반환"""
        return "sqlite:///./ktds_sessions.db"


# 현재 사용할 데이터베이스 설정 결정
def get_database_url() -> str:
    """현재 환경에 맞는 데이터베이스 URL 반환"""
    # 1. Azure SQL 연결 설정이 있으면 우선 사용
    azure_url = AzureSQLConfig.get_sqlalchemy_url()
    if azure_url:
        return azure_url
    
    # 2. 테스트 모드 확인
    if os.getenv("TESTING", "").lower() == "true":
        return AzureSQLConfig.get_test_db_url()
    
    # 3. 개발 모드 (기본값)
    return AzureSQLConfig.get_dev_db_url()


# 환경 변수 확인 유틸리티
def check_azure_sql_config() -> dict:
    """Azure SQL 설정 상태 확인"""
    return {
        "connection_string_provided": bool(AzureSQLConfig.CONNECTION_STRING),
        "server_provided": bool(AzureSQLConfig.SERVER),
        "database_provided": bool(AzureSQLConfig.DATABASE),
        "username_provided": bool(AzureSQLConfig.USERNAME),
        "password_provided": bool(AzureSQLConfig.PASSWORD),
        "can_connect": bool(AzureSQLConfig.get_connection_string()),
        "current_db_url": get_database_url()
    }


class APIKeysConfig:
    """API 키 설정"""
    
    # Gemini API 키
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDgYXrzEKHHcmQNAnSN4PfOKd2FEYEC8Iw")
    
    # Friendli AI API 키
    FRIENDLI_API_KEY = os.getenv("FRIENDLI_API_KEY", "flp_SdYLO1i2ReY4ew9etGwfrjdAwimTP0DA9HcXyYfm3hh061")
    
    # OpenAI API 키 (필요한 경우)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
    
    @classmethod
    def get_gemini_api_key(cls) -> str:
        """Gemini API 키 반환"""
        return cls.GEMINI_API_KEY
    
    @classmethod
    def get_friendli_api_key(cls) -> str:
        """Friendli AI API 키 반환"""
        return cls.FRIENDLI_API_KEY
    
    @classmethod
    def get_openai_api_key(cls) -> str:
        """OpenAI API 키 반환"""
        return cls.OPENAI_API_KEY


def check_api_keys_config() -> dict:
    """API 키 설정 상태 확인"""
    return {
        "gemini_api_key_provided": bool(APIKeysConfig.GEMINI_API_KEY and APIKeysConfig.GEMINI_API_KEY != "your_gemini_api_key_here"),
        "friendli_api_key_provided": bool(APIKeysConfig.FRIENDLI_API_KEY and APIKeysConfig.FRIENDLI_API_KEY != "flp_SdYLO1i2ReY4ew9etGwfrjdAwimTP0DA9HcXyYfm3hh061"),
        "openai_api_key_provided": bool(APIKeysConfig.OPENAI_API_KEY and APIKeysConfig.OPENAI_API_KEY != "your_openai_api_key_here"),
        "gemini_api_key": APIKeysConfig.GEMINI_API_KEY[:20] + "..." if len(APIKeysConfig.GEMINI_API_KEY) > 20 else APIKeysConfig.GEMINI_API_KEY,
        "friendli_api_key": APIKeysConfig.FRIENDLI_API_KEY[:20] + "..." if len(APIKeysConfig.FRIENDLI_API_KEY) > 20 else APIKeysConfig.FRIENDLI_API_KEY,
        "openai_api_key": APIKeysConfig.OPENAI_API_KEY[:20] + "..." if len(APIKeysConfig.OPENAI_API_KEY) > 20 else APIKeysConfig.OPENAI_API_KEY,
        "models": {
            "gemini_image_generation_model": "gemini-2.0-flash-preview-image-generation",
            "friendli_chat_model": "K-intelligence/Midm-2.0-Base-Instruct"
        }
    } 