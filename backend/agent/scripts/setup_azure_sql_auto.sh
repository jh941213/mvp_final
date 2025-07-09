#!/bin/bash

# Azure SQL 자동 설정 스크립트
# 매일 삭제되는 리소스를 자동으로 재생성

set -e  # 오류 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 설정 변수
RESOURCE_GROUP="kdb"
LOCATION="eastus"
TIMESTAMP=$(date +%s)
SERVER_NAME="kdb-chatsession-${TIMESTAMP}"
DATABASE_NAME="chatsession-db"
ADMIN_USER="kdbadmin"
ADMIN_PASSWORD="ChatSession123!"
FIREWALL_RULE_NAME="AllowAllIPs"

log_info "🚀 Azure SQL 자동 설정 스크립트 시작"
log_info "======================================"

# 1. Azure 로그인 상태 확인
log_info "1. Azure 로그인 상태 확인 중..."
if ! az account show &>/dev/null; then
    log_error "Azure에 로그인되어 있지 않습니다. 'az login' 명령어를 실행해주세요."
    exit 1
fi

SUBSCRIPTION_NAME=$(az account show --query name --output tsv)
log_success "Azure 로그인 상태: $SUBSCRIPTION_NAME"

# 2. 리소스 그룹 확인
log_info "2. 리소스 그룹 확인 중..."
if ! az group show --name $RESOURCE_GROUP &>/dev/null; then
    log_warning "리소스 그룹 '$RESOURCE_GROUP'이 존재하지 않습니다."
    log_info "리소스 그룹 생성 중..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
    log_success "리소스 그룹 생성 완료"
else
    log_success "리소스 그룹 '$RESOURCE_GROUP' 확인 완료"
fi

# 3. 기존 SQL 서버 정리 (선택사항)
log_info "3. 기존 chat-session SQL 서버 확인 중..."
EXISTING_SERVERS=$(az sql server list --resource-group $RESOURCE_GROUP --query "[?contains(name, 'kdb-chatsession')].name" --output tsv)
if [ ! -z "$EXISTING_SERVERS" ]; then
    log_warning "기존 chat-session 서버가 발견되었습니다:"
    echo "$EXISTING_SERVERS"
    read -p "기존 서버들을 삭제하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for server in $EXISTING_SERVERS; do
            log_info "서버 '$server' 삭제 중..."
            az sql server delete --name $server --resource-group $RESOURCE_GROUP --yes
            log_success "서버 '$server' 삭제 완료"
        done
    fi
fi

# 4. SQL Server 생성
log_info "4. SQL Server 생성 중..."
log_info "서버명: $SERVER_NAME"
az sql server create \
    --name $SERVER_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user $ADMIN_USER \
    --admin-password "$ADMIN_PASSWORD" \
    --enable-public-network true

log_success "SQL Server 생성 완료"

# 5. 데이터베이스 생성
log_info "5. 데이터베이스 생성 중..."
log_info "데이터베이스명: $DATABASE_NAME"
az sql db create \
    --resource-group $RESOURCE_GROUP \
    --server $SERVER_NAME \
    --name $DATABASE_NAME \
    --service-objective Basic

log_success "데이터베이스 생성 완료"

# 6. 방화벽 규칙 설정
log_info "6. 방화벽 규칙 설정 중..."
az sql server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --server $SERVER_NAME \
    --name $FIREWALL_RULE_NAME \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255

log_success "방화벽 규칙 설정 완료"

# 7. 연결 정보 생성
FULL_SERVER_NAME="${SERVER_NAME}.database.windows.net"
CONNECTION_STRING="DRIVER={ODBC Driver 17 for SQL Server};Server=${FULL_SERVER_NAME};Database=${DATABASE_NAME};UID=${ADMIN_USER};PWD=${ADMIN_PASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

log_info "7. 설정 파일 업데이트 중..."

# azure_sql_config.py 파일 업데이트
cat > azure_sql_config.py << EOF
"""
Azure SQL 연결 설정 파일
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
EOF

log_success "설정 파일 업데이트 완료"

# 8. 환경 변수 설정 스크립트 생성
log_info "8. 환경 변수 설정 스크립트 생성 중..."
cat > set_azure_env.sh << EOF
#!/bin/bash
# Azure SQL 환경 변수 설정 스크립트

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
EOF

chmod +x set_azure_env.sh
log_success "환경 변수 설정 스크립트 생성 완료"

# 9. 연결 테스트
log_info "9. 연결 테스트 중..."
export ODBCINI="/opt/homebrew/etc/odbc.ini"
export ODBCSYSINI="/opt/homebrew/etc"

# 잠시 대기 (Azure SQL 서버 준비 시간)
log_info "Azure SQL 서버 준비를 위해 30초 대기 중..."
sleep 30

# Python 연결 테스트
python3 -c "
import pyodbc
try:
    conn = pyodbc.connect('$CONNECTION_STRING')
    print('✅ Azure SQL 연결 성공!')
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    print('✅ 쿼리 실행 성공!')
    conn.close()
except Exception as e:
    print(f'❌ 연결 실패: {e}')
    print('⚠️  서버가 아직 준비되지 않았을 수 있습니다. 몇 분 후 다시 시도해주세요.')
"

# 10. 세션 관리자 테스트
log_info "10. 세션 관리자 테스트 실행 중..."
if [ -f "test_session_manager.py" ]; then
    python3 test_session_manager.py
else
    log_warning "test_session_manager.py 파일이 없습니다."
fi

# 11. 요약 정보 출력
log_info "11. 설정 요약"
log_info "=============="
echo ""
log_success "Azure SQL 서버 정보:"
echo "  - 서버명: $FULL_SERVER_NAME"
echo "  - 데이터베이스: $DATABASE_NAME"
echo "  - 사용자명: $ADMIN_USER"
echo "  - 비밀번호: $ADMIN_PASSWORD"
echo ""
log_success "환경 변수 설정:"
echo "  source ./set_azure_env.sh"
echo ""
log_success "연결 문자열:"
echo "  $CONNECTION_STRING"
echo ""
log_success "🎉 Azure SQL 자동 설정 완료!"
echo ""
log_info "📝 참고사항:"
echo "  1. 환경 변수를 설정하려면: source ./set_azure_env.sh"
echo "  2. 세션 관리자 테스트: python3 test_session_manager.py"
echo "  3. 설정 파일: azure_sql_config.py"
echo "  4. 리소스 삭제 시 이 스크립트를 다시 실행하세요." 