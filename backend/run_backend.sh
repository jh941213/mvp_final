#!/bin/bash

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 로고 함수들 로드
source "$SCRIPT_DIR/logo.sh"

# 기존 색상 정의 (Microsoft RGB 색상으로 업데이트)
RED='\033[38;2;209;52;56m'          # Microsoft Red
GREEN='\033[38;2;16;124;16m'        # Microsoft Green
YELLOW='\033[38;2;255;185;0m'       # Microsoft Yellow
BLUE='\033[38;2;0;120;212m'         # Microsoft Blue
NC='\033[0m' # No Color

# 로깅 함수 (Microsoft 색상 적용)
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 프로젝트 루트로 이동
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
log_info "프로젝트 루트 디렉토리: $PROJECT_ROOT"

# 모드 설정 (기본값: development)
MODE=${1:-development}
log_info "실행 모드: $MODE"

# 포트 설정
PORT=${2:-8000}
log_info "포트: $PORT"

# 가상환경 확인 및 생성
VENV_PATH="$PROJECT_ROOT/venv"
if [ ! -d "$VENV_PATH" ]; then
    log_info "가상환경이 없습니다. 생성 중..."
    python3 -m venv "$VENV_PATH"
    if [ $? -eq 0 ]; then
        log_success "가상환경 생성 완료: $VENV_PATH"
    else
        log_error "가상환경 생성 실패"
        exit 1
    fi
else
    log_info "기존 가상환경 사용: $VENV_PATH"
fi

# 가상환경 활성화
log_info "가상환경 활성화 중..."
source "$VENV_PATH/bin/activate"
if [ $? -eq 0 ]; then
    log_success "가상환경 활성화 완료"
else
    log_error "가상환경 활성화 실패"
    exit 1
fi

# pip 업그레이드
log_info "pip 업그레이드 중..."
pip install --upgrade pip > /dev/null 2>&1

# 의존성 설치
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
if [ -f "$REQUIREMENTS_FILE" ]; then
    log_info "의존성 설치 중..."
    pip install -r "$REQUIREMENTS_FILE"
    if [ $? -eq 0 ]; then
        log_success "의존성 설치 완료"
        
        # 🎉 의존성 설치 성공 후 로고 표시
        echo -e "\n${MS_GREEN}${BOLD}🎉 설치 성공! KT ds AutoGen 시스템을 시작합니다...${NC}\n"
        show_startup_banner
        show_system_info
        
    else
        log_error "의존성 설치 실패"
        exit 1
    fi
else
    log_warning "requirements.txt 파일을 찾을 수 없습니다: $REQUIREMENTS_FILE"
    # requirements.txt가 없어도 로고는 표시
    echo -e "\n${MS_YELLOW}${BOLD}⚠️  requirements.txt 없이 시작합니다...${NC}\n"
    show_startup_banner
    show_system_info
fi

# 환경변수 설정
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    log_info "환경변수 파일 로드: $ENV_FILE"
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
    log_success "환경변수 로드 완료"
else
    log_warning ".env 파일을 찾을 수 없습니다. 기본값 사용"
fi

# FastAPI 앱 경로 확인
APP_PATH="$PROJECT_ROOT/app"
if [ ! -d "$APP_PATH" ]; then
    log_error "FastAPI 앱 디렉토리를 찾을 수 없습니다: $APP_PATH"
    exit 1
fi

MAIN_FILE="$APP_PATH/main.py"
if [ ! -f "$MAIN_FILE" ]; then
    log_error "main.py 파일을 찾을 수 없습니다: $MAIN_FILE"
    exit 1
fi

log_success "FastAPI 앱 확인 완료: $MAIN_FILE"

# 서버 실행 준비 완료
echo -e "${MS_BLUE}${BOLD}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MS_GREEN}${BOLD}║  ✅ Environment Setup Complete                                   ║${NC}"
echo -e "${MS_YELLOW}${BOLD}║  📁 App Path: $APP_PATH${NC}"
echo -e "${MS_CYAN}${BOLD}║  🌐 Port: $PORT${NC}"
echo -e "${MS_PURPLE}${BOLD}║  🔧 Mode: $MODE${NC}"
echo -e "${MS_BLUE}${BOLD}╚══════════════════════════════════════════════════════════════════╝${NC}"

# 성공 메시지 표시
show_success_message

# 잠시 대기 후 서버 시작
sleep 2

case $MODE in
    "development" | "dev")
        log_info "🔧 개발 모드로 서버 시작 (hot reload 활성화)"
        echo -e "${MS_CYAN}${BOLD}🚀 Starting KT ds Multi-Agent Development Server...${NC}"
        uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload --app-dir "$PROJECT_ROOT"
        ;;
    "production" | "prod")
        log_info "🚀 프로덕션 모드로 서버 시작 (멀티 워커)"
        echo -e "${MS_GREEN}${BOLD}🏭 Starting KT ds Multi-Agent Production Server...${NC}"
        uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4 --app-dir "$PROJECT_ROOT"
        ;;
    "test")
        log_info "🧪 테스트 모드로 서버 시작"
        echo -e "${MS_YELLOW}${BOLD}🔬 Starting KT ds Multi-Agent Test Server...${NC}"
        uvicorn app.main:app --host 127.0.0.1 --port $PORT --app-dir "$PROJECT_ROOT"
        ;;
    *)
        log_error "❌ 알 수 없는 모드: $MODE"
        log_info "📋 사용 가능한 모드: development, production, test"
        exit 1
        ;;
esac 