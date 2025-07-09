# FastAPI 백엔드 실행 가이드

## 📋 개요
이 디렉토리에는 FastAPI 백엔드 서버를 실행하기 위한 자동화 스크립트들이 포함되어 있습니다.

## 🚀 빠른 시작

### 1. 초기 설정 (최초 1회)
```bash
./backend/setup.sh
```

### 2. 서버 실행
```bash
# 개발 모드 (권장)
./backend/dev.sh

# 또는 프로덕션 모드
./backend/prod.sh

# 또는 테스트 모드  
./backend/test.sh
```

### 3. 서버 중지
```bash
./backend/stop.sh
```

## 📁 스크립트 파일 설명

### `setup.sh` - 초기 환경 설정
- 가상환경 생성 및 활성화
- 필수 패키지 설치
- `.env` 파일 자동 생성
- **최초 1회만 실행**

### `run_backend.sh` - 메인 실행 스크립트
- 다양한 모드 지원 (development, production, test)
- 자동 환경 설정 및 의존성 설치
- 컬러 로깅 지원

**사용법:**
```bash
./run_backend.sh [모드] [포트]

# 예시
./run_backend.sh development 8000
./run_backend.sh production 8080
```

### 편의 스크립트들

#### `dev.sh` - 개발 모드
- 포트: 8000
- Hot reload 활성화
- 개발 중 코드 변경 시 자동 재시작

#### `prod.sh` - 프로덕션 모드  
- 포트: 8000
- 멀티 워커 (4개)
- 최적화된 성능

#### `test.sh` - 테스트 모드
- 포트: 8080
- 로컬호스트만 접근 가능
- 테스트 목적

#### `stop.sh` - 서버 중지
- 실행 중인 uvicorn 프로세스 종료
- 포트 8000, 8080 해제
- 안전한 서버 종료

## 🔧 환경 설정

### `.env` 파일 구조
```bash
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
```

## 📍 서버 접속 주소

| 모드 | URL | 용도 |
|------|-----|------|
| 개발/프로덕션 | http://localhost:8000 | 메인 서버 |
| 테스트 | http://localhost:8080 | 테스트 서버 |
| API 문서 | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | ReDoc UI |

## 🛠️ 문제 해결

### 포트 충돌 오류
```bash
# 실행 중인 프로세스 확인
lsof -i :8000

# 서버 중지 후 재시작
./backend/stop.sh
./backend/dev.sh
```

### 가상환경 문제
```bash
# 환경 재설정
./backend/setup.sh
```

### 의존성 설치 오류
```bash
# 수동 설치
source venv/bin/activate
pip install -r requirements.txt
```

## 📊 로그 확인

스크립트 실행 시 컬러 로그로 상태를 확인할 수 있습니다:
- 🔵 **INFO**: 일반 정보
- 🟢 **SUCCESS**: 성공
- 🟡 **WARNING**: 경고
- 🔴 **ERROR**: 오류

## 🎯 다음 단계

1. **개발 시작**: `./backend/dev.sh` 실행
2. **API 테스트**: http://localhost:8000/docs 접속
3. **코드 수정**: 자동 재시작으로 실시간 확인
4. **배포 준비**: `./backend/prod.sh`로 프로덕션 테스트 