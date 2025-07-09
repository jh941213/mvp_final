"""
Azure SQL 연결 설정 파일
"""

# Azure SQL 연결 정보
AZURE_SQL_CONFIG = {
    "CONNECTION_STRING": "your_connection_string",
    "SERVER": "your_server",
    "DATABASE": "your_database",
    "USERNAME": "your_username",
    "PASSWORD": "your_password",
    "PORT": 1433,
    "ENCRYPT": True,
    "TRUST_SERVER_CERTIFICATE": False,
    "CONNECTION_TIMEOUT": 30
}

def get_azure_sql_connection_string():
    """Azure SQL 연결 문자열 반환"""
    return AZURE_SQL_CONFIG["CONNECTION_STRING"]

def get_azure_sql_config():
    """Azure SQL 설정 정보 반환"""
    return AZURE_SQL_CONFIG.copy()

# Azure 환경 변수에 설정하는 함수
def set_azure_environment_variables():
    """Azure 환경 변수 설정"""
    import os
    
    os.environ["AZURE_SQL_CONNECTION_STRING"] = AZURE_SQL_CONFIG["CONNECTION_STRING"]
    os.environ["AZURE_SQL_SERVER"] = AZURE_SQL_CONFIG["SERVER"]
    os.environ["AZURE_SQL_DATABASE"] = AZURE_SQL_CONFIG["DATABASE"]
    os.environ["AZURE_SQL_USERNAME"] = AZURE_SQL_CONFIG["USERNAME"]
    os.environ["AZURE_SQL_PASSWORD"] = AZURE_SQL_CONFIG["PASSWORD"]
    
    # Azure 관련 환경 변수 설정
    os.environ["AZURE_TENANT_ID"] = "your_tenant_id"
    os.environ["AZURE_CLIENT_ID"] = "your_client_id"
    os.environ["AZURE_CLIENT_SECRET"] = "your_client_secret"
    
    print("✅ Azure 환경 변수 설정 완료")

if __name__ == "__main__":
    set_azure_environment_variables()
    print("Azure SQL 연결 정보:")
    print(f"서버: {AZURE_SQL_CONFIG['SERVER']}")
    print(f"데이터베이스: {AZURE_SQL_CONFIG['DATABASE']}")
    print(f"사용자명: {AZURE_SQL_CONFIG['USERNAME']}")
    print("연결 문자열이 환경 변수에 설정되었습니다.") 