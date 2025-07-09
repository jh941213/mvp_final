#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log_info "🛠️  FastAPI 백엔드 초기 설정 시작"

# 프로젝트 루트로 이동
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

log_info "프로젝트 루트: $PROJECT_ROOT"

# Python 버전 확인
PYTHON_VERSION=$(python3 --version 2>&1)
log_info "Python 버전: $PYTHON_VERSION"

# 가상환경 생성
VENV_PATH="$PROJECT_ROOT/venv"
if [ -d "$VENV_PATH" ]; then
    log_warning "기존 가상환경 삭제 중..."
    rm -rf "$VENV_PATH"
fi

log_info "새 가상환경 생성 중..."
python3 -m venv "$VENV_PATH"
if [ $? -eq 0 ]; then
    log_success "가상환경 생성 완료"
else
    log_error "가상환경 생성 실패"
    exit 1
fi

# 가상환경 활성화
source "$VENV_PATH/bin/activate"
log_success "가상환경 활성화 완료"

# pip 업그레이드
log_info "pip 업그레이드 중..."
pip install --upgrade pip

# 기본 패키지 설치
log_info "필수 패키지 설치 중..."
pip install fastapi uvicorn python-multipart python-dotenv

# requirements.txt가 있다면 설치
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
if [ -f "$REQUIREMENTS_FILE" ]; then
    log_info "추가 의존성 설치 중..."
    pip install -r "$REQUIREMENTS_FILE"
    log_success "의존성 설치 완료"
fi

# .env 파일 생성 (없는 경우)
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    log_info ".env 파일 생성 중..."
    cat > "$ENV_FILE" << EOF
# FastAPI 설정
APP_NAME=FastAPI Backend
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 데이터베이스 설정
DATABASE_URL=sqlite:///./test.db

# 보안 설정
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 설정
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# 로깅 설정
LOG_LEVEL=INFO
EOF
    log_success ".env 파일 생성 완료"
else
    log_info ".env 파일이 이미 존재합니다"
fi

log_success "🎉 초기 설정 완료!"
log_info "다음 명령으로 서버를 시작할 수 있습니다:"
log_info "  개발 모드: ./backend/dev.sh"
log_info "  프로덕션 모드: ./backend/prod.sh"
log_info "  테스트 모드: ./backend/test.sh" 