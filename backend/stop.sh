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

log_info "🛑 FastAPI 서버 중지 중..."

# uvicorn 프로세스 찾기 및 종료
UVICORN_PIDS=$(pgrep -f "uvicorn.*app.main:app")

if [ -z "$UVICORN_PIDS" ]; then
    log_warning "실행 중인 FastAPI 서버를 찾을 수 없습니다"
else
    log_info "실행 중인 서버 프로세스: $UVICORN_PIDS"
    
    for PID in $UVICORN_PIDS; do
        log_info "프로세스 $PID 종료 중..."
        kill $PID
        sleep 1
        
        # 강제 종료가 필요한 경우
        if kill -0 $PID 2>/dev/null; then
            log_warning "프로세스 $PID 강제 종료 중..."
            kill -9 $PID
        fi
    done
    
    log_success "FastAPI 서버가 중지되었습니다"
fi

# 포트 확인 (8000, 8080)
for PORT in 8000 8080; do
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        log_warning "포트 $PORT을 사용하는 프로세스 $PID 발견. 종료 중..."
        kill $PID
        sleep 1
        if kill -0 $PID 2>/dev/null; then
            kill -9 $PID
        fi
        log_success "포트 $PORT 해제 완료"
    fi
done 