# Azure SQL 연결 설정 가이드

## 1. 환경 변수 설정

### 방법 1: 연결 문자열 사용 (권장)
```bash
export AZURE_SQL_CONNECTION_STRING="Server=tcp:your-server.database.windows.net,1433;Database=your-database;User ID=your-username;Password=your-password;Encrypt=true;TrustServerCertificate=false;Connection Timeout=30;"
```

### 방법 2: 개별 설정 사용
```bash
export AZURE_SQL_SERVER="your-server.database.windows.net"
export AZURE_SQL_DATABASE="your-database"
export AZURE_SQL_USERNAME="your-username"
export AZURE_SQL_PASSWORD="your-password"
```

### 방법 3: .env 파일 사용
프로젝트 루트에 `.env` 파일을 생성하고 다음을 추가:
```env
AZURE_SQL_CONNECTION_STRING=Server=tcp:your-server.database.windows.net,1433;Database=your-database;User ID=your-username;Password=your-password;Encrypt=true;TrustServerCertificate=false;Connection Timeout=30;

# 또는 개별 설정
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
```

## 2. 필수 패키지 설치

### macOS에서 ODBC 드라이버 설치
```bash
# Homebrew를 사용한 설치
brew install unixodbc
brew install --cask microsoft-azure-sql-edge

# 또는 Microsoft 공식 가이드 따라 설치
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-bionic-prod bionic main" > /etc/apt/sources.list.d/mssql-release.list'
sudo apt-get update
sudo apt-get install msodbcsql17
```

### Python 패키지 설치
```bash
pip install pyodbc sqlalchemy python-dotenv
```

## 3. 데이터베이스 테이블 생성

시스템이 자동으로 다음 테이블들을 생성합니다:

### conversation_history 테이블
```sql
CREATE TABLE conversation_history (
    id INT IDENTITY(1,1) PRIMARY KEY,
    session_id UNIQUEIDENTIFIER NOT NULL,
    user_id NVARCHAR(255) NOT NULL,
    thread_id NVARCHAR(255),
    user_message NTEXT,
    assistant_response NTEXT,
    created_at DATETIME2 DEFAULT GETDATE(),
    metadata NTEXT
);

CREATE INDEX idx_conversation_session_id ON conversation_history(session_id);
CREATE INDEX idx_conversation_user_id ON conversation_history(user_id);
CREATE INDEX idx_conversation_created_at ON conversation_history(created_at);
```

### user_sessions 테이블
```sql
CREATE TABLE user_sessions (
    session_id UNIQUEIDENTIFIER PRIMARY KEY,
    user_id NVARCHAR(255) NOT NULL,
    thread_id NVARCHAR(255),
    created_at DATETIME2 DEFAULT GETDATE(),
    last_activity DATETIME2 DEFAULT GETDATE(),
    is_active BIT DEFAULT 1,
    metadata NTEXT
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_created_at ON user_sessions(created_at);
CREATE INDEX idx_sessions_last_activity ON user_sessions(last_activity);
CREATE INDEX idx_sessions_is_active ON user_sessions(is_active);
```

## 4. 연결 테스트

### 설정 확인
```python
from backend.agent.config import check_azure_sql_config

config_status = check_azure_sql_config()
print(config_status)
```

### 세션 관리자 테스트
```python
from backend.agent.session_manager import SessionManager

# 세션 관리자 초기화 (Azure SQL 또는 In-Memory 자동 선택)
session_manager = SessionManager()

# 세션 생성
session_id = session_manager.create_session("test_user")
print(f"세션 생성됨: {session_id}")

# 대화 저장
session_manager.save_conversation_turn(
    session_id=session_id,
    user_message="안녕하세요",
    assistant_response="안녕하세요! 무엇을 도와드릴까요?"
)

# 대화 히스토리 조회
history = session_manager.get_conversation_history(session_id)
print(f"대화 히스토리: {len(history)}개 메시지")
```

## 5. 데이터베이스 연결 우선순위

시스템은 다음 순서로 데이터베이스 연결을 시도합니다:

1. **Azure SQL**: 환경 변수 설정이 완료된 경우
2. **SQLite (메모리)**: 테스트 모드 (`TESTING=true`)
3. **SQLite (파일)**: 개발 모드 (기본값)
4. **In-Memory**: 모든 연결 실패 시 fallback

## 6. 환경별 설정

### 개발 환경
```env
# 로컬 SQLite 사용
TESTING=false
```

### 테스트 환경
```env
# 인메모리 SQLite 사용
TESTING=true
```

### 운영 환경
```env
# Azure SQL 사용
AZURE_SQL_CONNECTION_STRING=your-production-connection-string
TESTING=false
```

## 7. 모니터링 및 관리

### 세션 통계 확인
```python
stats = session_manager.get_session_stats()
print(f"활성 세션: {stats['total_active_sessions']}")
print(f"관리자 타입: {stats['manager_type']}")
```

### 오래된 세션 정리
```python
# 30일 이상 된 세션 정리
cleaned_count = session_manager.cleanup_old_sessions(days=30)
print(f"정리된 세션: {cleaned_count}개")
```

## 8. 문제 해결

### ODBC 드라이버 문제
```
Error: Can't open lib 'ODBC Driver 17 for SQL Server'
```
→ Microsoft ODBC Driver 17 for SQL Server 설치 필요

### 연결 타임아웃
```
Connection Timeout Expired
```
→ 방화벽 설정 확인 및 연결 문자열의 서버 주소 확인

### 인증 실패
```
Login failed for user
```
→ 사용자명/비밀번호 확인 및 Azure SQL 방화벽 규칙 확인

## 9. 보안 고려사항

- 환경 변수 또는 .env 파일에 저장된 인증 정보는 소스 코드 저장소에 커밋하지 않음
- Azure SQL 방화벽 규칙을 적절히 설정하여 불필요한 접근 차단
- 연결 문자열에는 항상 `Encrypt=true` 설정 사용
- 정기적인 비밀번호 변경 및 액세스 키 로테이션 실시 