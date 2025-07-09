#!/bin/bash

# Azure SQL 자동 설정 스크립트 (Cron Job용)
# 매일 자동으로 실행되어 Azure SQL 리소스를 재생성

# 로그 파일 설정
LOG_FILE="/tmp/azure_sql_setup_$(date +%Y%m%d).log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "=================================================="
echo "Azure SQL 자동 설정 시작 - $(date)"
echo "=================================================="

# 디렉토리 변경
cd "$(dirname "$0")"

# Azure 로그인 상태 확인
if ! az account show &>/dev/null; then
    echo "❌ Azure에 로그인되어 있지 않습니다."
    echo "cron job 실행 전에 'az login --use-device-code' 또는 서비스 주체 설정이 필요합니다."
    exit 1
fi

# 기존 리소스 자동 정리
echo "🔄 기존 kdb-chatsession 서버 자동 정리 중..."
RESOURCE_GROUP="kdb"
EXISTING_SERVERS=$(az sql server list --resource-group $RESOURCE_GROUP --query "[?contains(name, 'kdb-chatsession')].name" --output tsv)

if [ ! -z "$EXISTING_SERVERS" ]; then
    echo "기존 서버 발견: $EXISTING_SERVERS"
    for server in $EXISTING_SERVERS; do
        echo "서버 '$server' 삭제 중..."
        az sql server delete --name $server --resource-group $RESOURCE_GROUP --yes
        echo "서버 '$server' 삭제 완료"
    done
fi

# 새로운 서버 생성
echo "🚀 새로운 Azure SQL 서버 생성 중..."
TIMESTAMP=$(date +%s)
SERVER_NAME="kdb-chatsession-${TIMESTAMP}"
DATABASE_NAME="chatsession-db"
ADMIN_USER="kdbadmin"
ADMIN_PASSWORD="ChatSession123!"

# SQL Server 생성
echo "서버 생성: $SERVER_NAME"
az sql server create \
    --name $SERVER_NAME \
    --resource-group $RESOURCE_GROUP \
    --location eastus \
    --admin-user $ADMIN_USER \
    --admin-password "$ADMIN_PASSWORD" \
    --enable-public-network true

# 데이터베이스 생성
echo "데이터베이스 생성: $DATABASE_NAME"
az sql db create \
    --resource-group $RESOURCE_GROUP \
    --server $SERVER_NAME \
    --name $DATABASE_NAME \
    --service-objective Basic

# 방화벽 규칙 설정
echo "방화벽 규칙 설정"
az sql server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --server $SERVER_NAME \
    --name AllowAllIPs \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255

# 설정 파일 업데이트
FULL_SERVER_NAME="${SERVER_NAME}.database.windows.net"
CONNECTION_STRING="DRIVER={ODBC Driver 17 for SQL Server};Server=${FULL_SERVER_NAME};Database=${DATABASE_NAME};UID=${ADMIN_USER};PWD=${ADMIN_PASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

echo "설정 파일 업데이트 중..."
cat > azure_sql_config.py << EOF
"""
Azure SQL 연결 설정 파일
자동 생성일: $(date)
"""

# Azure SQL 연결 정보
AZURE_SQL_CONFIG = {
    "CONNECTION_STRING": "$CONNECTION_STRING",
    "SERVER": "$FULL_SERVER_NAME",
    "DATABASE": "$DATABASE_NAME",
    "USERNAME": "$ADMIN_USER",
    "PASSWORD": "$ADMIN_PASSWORD",
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

def set_environment_variables():
    """환경 변수 설정"""
    import os
    
    os.environ["AZURE_SQL_CONNECTION_STRING"] = AZURE_SQL_CONFIG["CONNECTION_STRING"]
    os.environ["AZURE_SQL_SERVER"] = AZURE_SQL_CONFIG["SERVER"]
    os.environ["AZURE_SQL_DATABASE"] = AZURE_SQL_CONFIG["DATABASE"]
    os.environ["AZURE_SQL_USERNAME"] = AZURE_SQL_CONFIG["USERNAME"]
    os.environ["AZURE_SQL_PASSWORD"] = AZURE_SQL_CONFIG["PASSWORD"]
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
EOF

# 환경 변수 설정 스크립트 업데이트
cat > set_azure_env.sh << EOF
#!/bin/bash
# Azure SQL 환경 변수 설정 스크립트
# 자동 생성일: $(date)

export AZURE_SQL_CONNECTION_STRING="$CONNECTION_STRING"
export AZURE_SQL_SERVER="$FULL_SERVER_NAME"
export AZURE_SQL_DATABASE="$DATABASE_NAME"
export AZURE_SQL_USERNAME="$ADMIN_USER"
export AZURE_SQL_PASSWORD="$ADMIN_PASSWORD"
export ODBCINI="/opt/homebrew/etc/odbc.ini"
export ODBCSYSINI="/opt/homebrew/etc"

echo "✅ Azure SQL 환경 변수 설정 완료"
echo "서버: $FULL_SERVER_NAME"
echo "데이터베이스: $DATABASE_NAME"
echo "사용자명: $ADMIN_USER"
echo "설정 시간: $(date)"
EOF

chmod +x set_azure_env.sh

# 완료 메시지
echo "=================================================="
echo "✅ Azure SQL 자동 설정 완료 - $(date)"
echo "=================================================="
echo "서버명: $FULL_SERVER_NAME"
echo "데이터베이스: $DATABASE_NAME"
echo "사용자명: $ADMIN_USER"
echo "로그 파일: $LOG_FILE"
echo "=================================================="

# 슬랙 알림이나 이메일 알림을 여기에 추가할 수 있습니다
# curl -X POST -H 'Content-type: application/json' --data '{"text":"Azure SQL 자동 설정 완료"}' YOUR_SLACK_WEBHOOK_URL 