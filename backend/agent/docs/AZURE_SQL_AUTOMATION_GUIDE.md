# Azure SQL 자동화 완전 가이드

## 📋 개요

매일 삭제되는 Azure SQL 리소스를 자동으로 재생성하는 완전 자동화 솔루션입니다.

## 🚀 빠른 시작

### 1. 즉시 실행 (권장)

```bash
# 현재 디렉토리: /Users/kdb/ms_final_mvp/backend/agent
./quick_setup.sh
```

### 2. 환경 변수 설정

```bash
# 자동 생성된 환경 변수 적용
source ./set_azure_env.sh
```

### 3. 연결 테스트

```bash
# 세션 관리자 테스트
python3 test_session_manager.py
```

## 📁 자동화 스크립트 목록

### 1. `setup_azure_sql_auto.sh` (메인 스크립트)
- **기능**: 대화형 Azure SQL 리소스 생성
- **특징**: 색상 코딩된 로그, 사용자 확인 프롬프트
- **사용법**: `./setup_azure_sql_auto.sh`

### 2. `quick_setup.sh` (빠른 설정)
- **기능**: 간단한 실행 스크립트
- **특징**: 기존 리소스 정리 옵션 제공
- **사용법**: `./quick_setup.sh`

### 3. `cron_setup_azure.sh` (자동 실행용)
- **기능**: 사용자 상호작용 없이 자동 실행
- **특징**: 로그 파일 자동 생성, 완전 자동화
- **사용법**: `./cron_setup_azure.sh`

## ⏰ 자동화 스케줄링

### Cron Job 설정

```bash
# cron job 편집
crontab -e

# 매일 오전 9시에 자동 실행
0 9 * * * /Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh

# 주중(월-금) 오전 9시에만 실행
0 9 * * 1-5 /Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh
```

### macOS LaunchAgent 설정

```bash
# LaunchAgent 파일 생성
cat > ~/Library/LaunchAgents/com.kdb.azure-sql-setup.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kdb.azure-sql-setup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
EOF

# LaunchAgent 활성화
launchctl load ~/Library/LaunchAgents/com.kdb.azure-sql-setup.plist
```

## 🔧 생성되는 파일들

### 1. `azure_sql_config.py`
```python
# Azure SQL 연결 설정
AZURE_SQL_CONFIG = {
    "CONNECTION_STRING": "...",
    "SERVER": "kdb-chatsession-{timestamp}.database.windows.net",
    "DATABASE": "chatsession-db",
    "USERNAME": "kdbadmin",
    "PASSWORD": "ChatSession123!",
    # ...
}
```

### 2. `set_azure_env.sh`
```bash
# 환경 변수 설정 스크립트
export AZURE_SQL_CONNECTION_STRING="..."
export AZURE_SQL_SERVER="..."
export AZURE_SQL_DATABASE="..."
# ...
```

### 3. 로그 파일
```
/tmp/azure_sql_setup_YYYYMMDD.log
```

## 🔍 모니터링 및 상태 확인

### 1. Azure 리소스 확인

```bash
# 현재 SQL 서버 목록
az sql server list --resource-group kdb

# 데이터베이스 목록
az sql db list --resource-group kdb --server {SERVER_NAME}

# 방화벽 규칙 확인
az sql server firewall-rule list --resource-group kdb --server {SERVER_NAME}
```

### 2. 연결 테스트

```bash
# 세션 관리자 테스트
python3 test_session_manager.py

# 직접 연결 테스트
python3 -c "
import pyodbc
from azure_sql_config import get_azure_sql_connection_string
conn = pyodbc.connect(get_azure_sql_connection_string())
print('✅ 연결 성공!')
"
```

### 3. 로그 확인

```bash
# 최신 로그 확인
tail -f /tmp/azure_sql_setup_$(date +%Y%m%d).log

# 모든 로그 파일 확인
ls -la /tmp/azure_sql_setup_*.log
```

## ⚙️ 시스템 구성

### Azure SQL 설정
- **리소스 그룹**: `kdb`
- **위치**: `eastus`
- **서버명**: `kdb-chatsession-{timestamp}`
- **데이터베이스**: `chatsession-db`
- **관리자**: `kdbadmin`
- **비밀번호**: `ChatSession123!`
- **방화벽**: 모든 IP 허용 (0.0.0.0-255.255.255.255)

### 세션 관리 시스템
- **UUID 기반 세션 ID**: 고유 세션 식별
- **이중화 구조**: Azure SQL + 메모리 기반 Fallback
- **자동 Fallback**: 연결 실패 시 메모리 모드로 자동 전환
- **사용자별 히스토리**: 세션별 대화 기록 관리

## 🔐 보안 고려사항

### 1. 접근 제어
- Azure SQL 서버에 모든 IP 허용 설정 (개발/테스트 환경)
- 프로덕션 환경에서는 특정 IP 대역만 허용 권장

### 2. 인증 정보
- 비밀번호는 환경변수나 Azure Key Vault 사용 권장
- 현재 하드코딩된 비밀번호는 테스트 환경용

### 3. 네트워크 보안
- Azure SQL 서버에서 TLS 암호화 강제 사용
- 연결 문자열에 Encrypt=yes 설정

## 🛠️ 문제 해결

### 1. Azure CLI 로그인 문제
```bash
# 대화형 로그인
az login

# 디바이스 코드 로그인
az login --use-device-code

# 서비스 주체 로그인
az login --service-principal -u {APP_ID} -p {PASSWORD} --tenant {TENANT_ID}
```

### 2. 연결 실패 문제
```bash
# ODBC 드라이버 확인
odbcinst -q -d

# 환경 변수 확인
echo $ODBCINI
echo $ODBCSYSINI

# 드라이버 재설치
brew reinstall msodbcsql17
```

### 3. 권한 문제
```bash
# 스크립트 실행 권한 확인
chmod +x *.sh

# 디렉토리 접근 권한 확인
ls -la /Users/kdb/ms_final_mvp/backend/agent/
```

## 📊 성능 최적화

### 1. 연결 풀링
```python
# sqlalchemy 연결 풀 설정
engine = create_engine(
    connection_string,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 2. 세션 관리 최적화
- 세션 정보 캐싱
- 불필요한 세션 자동 정리
- 배치 처리로 성능 향상

## 🔄 업데이트 및 유지보수

### 1. 스크립트 업데이트
```bash
# 최신 버전 다운로드 (필요시)
git pull origin main

# 실행 권한 재설정
chmod +x *.sh
```

### 2. 정기 점검
- 매주 로그 파일 확인
- 월별 Azure 리소스 사용량 확인
- 분기별 보안 설정 검토

## 📞 지원 및 문의

문제가 발생하거나 추가 기능이 필요한 경우:
1. 로그 파일 확인
2. GitHub Issues 등록
3. 개발팀 문의

---

**Azure SQL 자동화 시스템** - 매일 삭제되는 리소스도 걱정 없이! 🚀 