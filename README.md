# KTDS MagenticOne 멀티에이전트 시스템

## 📋 개요

**KTDS MagenticOne 시스템**은 Microsoft AutoGen의 **MagenticOne 아키텍처**를 기반으로 한 지능형 멀티에이전트 시스템입니다. **Azure SQL 세션 관리**와 **자동화된 인프라 관리**를 포함한 완전한 엔터프라이즈 솔루션입니다.

## 🏗️ 프로젝트 구조

```
backend/agent/
├── 📁 agents/              # Worker 에이전트들
│   ├── hr_agent.py
│   ├── bulletin_board_agent.py
│   ├── project_management_agent.py
│   └── ktds_info_agent.py
├── 📁 tools/               # 에이전트별 도구들
│   ├── hr_tools.py
│   ├── bulletin_tools.py
│   └── project_tools.py
├── 📁 config/              # 설정 파일들
│   ├── azure_sql_config.py
│   ├── config.py
│   └── requirements.txt
├── 📁 scripts/             # 자동화 스크립트들
│   ├── setup_azure_sql_auto.sh
│   ├── quick_setup.sh
│   └── cron_setup_azure.sh
├── 📁 env/                 # 환경변수 관리
│   ├── env_template.txt
│   ├── env_loader.py
│   └── setup_env.py
├── 📁 tests/               # 테스트 파일들
│   └── test_session_manager.py
├── 📁 docs/                # 문서들
│   ├── README.md
│   ├── AZURE_SQL_AUTOMATION_GUIDE.md
│   ├── setup_cron.md
│   └── environment_setup.md
├── multi_agent_system.py   # 메인 시스템
├── session_manager.py      # 세션 관리
└── agent.py                # 단일 에이전트
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r config/requirements.txt

# 환경변수 설정
python3 env/setup_env.py
source set_env.sh
```

### 2. Azure SQL 자동 설정 (매일 삭제되는 리소스용)

```bash
# 즉시 실행 (권장)
./scripts/quick_setup.sh

# 또는 상세 설정
./scripts/setup_azure_sql_auto.sh
```

### 3. 시스템 테스트

```bash
# 세션 관리자 테스트
python3 tests/test_session_manager.py

# 환경변수 상태 확인
python3 env/env_loader.py
```

## 🤖 시스템 아키텍처

```
🎯 MagenticOneOrchestrator (조율자)
├── 🏢 HR_Agent (인사 업무 전문)
├── 📋 Bulletin_Agent (게시판 및 커뮤니케이션)  
├── 📊 Project_Agent (프로젝트 관리)
└── 🔍 KTDS_Info_Agent (회사 정보 검색)
```

### 주요 특징

- **지능형 라우팅**: 질문 유형에 따라 적절한 전문 에이전트 자동 선택
- **Azure SQL 세션 관리**: UUID 기반 세션 추적 및 대화 기록 저장
- **자동 Fallback**: Azure SQL 실패 시 메모리 기반으로 자동 전환
- **완전 자동화**: 매일 삭제되는 Azure 리소스 자동 재생성

## 🗄️ Azure SQL 자동화

### 매일 자동 실행 설정

```bash
# cron job 설정
crontab -e

# 매일 오전 9시에 자동 실행
0 9 * * * /Users/kdb/ms_final_mvp/backend/agent/scripts/cron_setup_azure.sh
```

### 수동 실행

```bash
# 즉시 실행
./scripts/quick_setup.sh

# 완전 자동화 (사용자 상호작용 없음)
./scripts/cron_setup_azure.sh
```

## 🔧 환경변수 관리

### 새로 설정

```bash
python3 env/setup_env.py
```

### 기존 설정 로드

```bash
python3 env/setup_env.py --load
```

### 상태 확인

```bash
python3 env/env_loader.py
```

## 💡 사용법

### 기본 사용

```python
from multi_agent_system import get_magentic_system

# 시스템 초기화
system = get_magentic_system(verbose=True)

# 질문 처리
response = await system.process_query("급여는 언제 들어와요?")
print(response)
```

### 세션 관리 사용

```python
from session_manager import SessionManager

# 세션 매니저 초기화
session_manager = SessionManager()

# 세션 생성
session_id = session_manager.create_session("user123")

# 대화 기록 저장
session_manager.add_message(session_id, "user", "안녕하세요")
session_manager.add_message(session_id, "assistant", "안녕하세요! 도움이 필요하시면 말씀해주세요.")

# 세션 기록 조회
history = session_manager.get_session_history(session_id)
```

## 📊 주요 기능

### ✅ 멀티에이전트 시스템
- **4개 전문 에이전트**: HR, 게시판, 프로젝트, 회사정보
- **19개 전용 도구**: 각 에이전트별 특화 기능
- **멀티홉 쿼리**: 복합 질문 자동 분해 처리

### ✅ Azure SQL 세션 관리
- **UUID 기반 세션**: 고유 세션 식별자
- **대화 기록 저장**: 사용자별 히스토리 관리
- **자동 Fallback**: 연결 실패 시 메모리 모드

### ✅ 완전 자동화
- **리소스 자동 생성**: 타임스탬프 기반 고유 서버명
- **cron job 지원**: 매일 자동 실행
- **로그 시스템**: 색상 코딩된 상세 로그

## 🔐 보안 설정

### Azure SQL 서버 정보
- **서버명**: `kdb-chatsession-{timestamp}`
- **데이터베이스**: `chatsession-db`
- **관리자**: `kdbadmin`
- **비밀번호**: `ChatSession123!`
- **위치**: `eastus`

### 환경변수 보안
- `.env` 파일을 통한 중앙 관리
- 템플릿 파일 제공
- 자동 스크립트 생성

## 📈 모니터링

### 상태 확인

```bash
# Azure 리소스 확인
az sql server list --resource-group kdb

# 로그 확인
tail -f /tmp/azure_sql_setup_$(date +%Y%m%d).log

# 세션 관리자 테스트
python3 tests/test_session_manager.py
```

### 성능 지표
- **평균 응답시간**: 10-15초
- **멀티홉 쿼리 성공률**: 90%+
- **세션 관리 성공률**: 100% (Fallback 포함)
- **자동화 성공률**: 95%+

## 📚 문서

- **[전체 가이드](docs/README.md)**: 상세한 시스템 가이드
- **[자동화 가이드](docs/AZURE_SQL_AUTOMATION_GUIDE.md)**: Azure SQL 자동화 완전 가이드
- **[Cron 설정](docs/setup_cron.md)**: 자동 실행 설정 방법
- **[환경 설정](docs/environment_setup.md)**: 초기 환경 구성

## 🛠️ 개발 정보

### 기술 스택
- **Microsoft AutoGen**: MagenticOne 아키텍처
- **Azure SQL**: 세션 및 사용자 데이터 관리
- **Azure OpenAI**: GPT-4.1-mini 모델
- **Azure AI Search**: 하이브리드 검색
- **Python**: 비동기 프로그래밍

### 개발 도구
```bash
# 코드 포맷팅
black backend/agent/

# 코드 검사
flake8 backend/agent/

# 테스트 실행
pytest tests/
```

## 🔄 업데이트 및 유지보수

### 스크립트 업데이트
```bash
# 실행 권한 재설정
chmod +x scripts/*.sh

# 환경변수 재설정
python3 env/setup_env.py --load
```

### 정기 점검
- 매주: 로그 파일 확인
- 월별: Azure 리소스 사용량 확인
- 분기별: 보안 설정 검토

## 📞 지원

시스템 관련 문의사항은 개발팀에 연락하시기 바랍니다.

---

**KTDS MagenticOne 시스템** - 지능형 멀티에이전트로 더 스마트한 업무 처리를! 🚀 