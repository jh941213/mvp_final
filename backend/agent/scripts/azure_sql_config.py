"""
Azure SQL 연결 설정 파일
"""

# Azure SQL 연결 정보
AZURE_SQL_CONFIG = {
    "CONNECTION_STRING": "DRIVER={ODBC Driver 17 for SQL Server};Server=kdb-chatsession-1751955774.database.windows.net;Database=chatsession-db;UID=kdbadmin;PWD=ChatSession123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
    "SERVER": "kdb-chatsession-1751955774.database.windows.net",
    "DATABASE": "chatsession-db",
    "USERNAME": "kdbadmin",
    "PASSWORD": "ChatSession123!",
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

# 환경 변수에 설정하는 함수
def set_environment_variables():
    """환경 변수 설정"""
    import os
    
    os.environ["AZURE_SQL_CONNECTION_STRING"] = AZURE_SQL_CONFIG["CONNECTION_STRING"]
    os.environ["AZURE_SQL_SERVER"] = AZURE_SQL_CONFIG["SERVER"]
    os.environ["AZURE_SQL_DATABASE"] = AZURE_SQL_CONFIG["DATABASE"]
    os.environ["AZURE_SQL_USERNAME"] = AZURE_SQL_CONFIG["USERNAME"]
    os.environ["AZURE_SQL_PASSWORD"] = AZURE_SQL_CONFIG["PASSWORD"]
    
    # ODBC 환경 변수 설정
    os.environ["ODBCINI"] = "/opt/homebrew/etc/odbc.ini"
    os.environ["ODBCSYSINI"] = "/opt/homebrew/etc"
    
    print("✅ Azure SQL 환경 변수 설정 완료")

if __name__ == "__main__":
    set_environment_variables()
    print("Azure SQL 연결 정보:")
    print(f"서버: {AZURE_SQL_CONFIG['SERVER']}")
    print(f"데이터베이스: {AZURE_SQL_CONFIG['DATABASE']}")
    print(f"사용자명: {AZURE_SQL_CONFIG['USERNAME']}")
    print("연결 문자열이 환경 변수에 설정되었습니다.")
