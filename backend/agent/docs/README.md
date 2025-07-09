# KTDS MagenticOne 멀티에이전트 시스템

## 📋 개요

**KTDS MagenticOne 시스템**은 Microsoft AutoGen의 **MagenticOne 아키텍처**를 기반으로 한 지능형 멀티에이전트 시스템입니다. **Orchestrator**가 전문 **Worker 에이전트들**을 조율하여 다양한 업무를 효율적으로 처리합니다.

## 🏗️ 시스템 아키텍처

```
🎯 MagenticOneOrchestrator (조율자)
├── 🏢 HR_Agent (인사 업무 전문)
├── 📋 Bulletin_Agent (게시판 및 커뮤니케이션)  
├── 📊 Project_Agent (프로젝트 관리)
└── 🔍 KTDS_Info_Agent (회사 정보 검색)
```

### 주요 특징

- **지능형 라우팅**: 질문 유형에 따라 적절한 전문 에이전트 자동 선택
- **멀티홉 처리**: 복합 질문을 여러 단계로 분해하여 처리
- **실시간 도구 활용**: 각 에이전트가 전용 도구를 사용하여 실제 데이터 제공
- **확장 가능한 구조**: 새로운 에이전트와 도구 쉽게 추가 가능

## 🔧 설치 및 설정

### 필수 패키지

```bash
pip install autogen-agentchat autogen-ext[azure]
```

### 환경 설정

Azure OpenAI 및 Azure AI Search 설정이 필요합니다:

- **Azure OpenAI**: GPT-4.1-mini 모델
- **Azure AI Search**: KTDS 정보 검색용 인덱스

## 🗄️ Azure SQL 자동화 설정

### 매일 삭제되는 Azure SQL 리소스 자동 재생성

Azure SQL 리소스가 매일 삭제되는 환경에서는 자동화 스크립트를 사용하여 리소스를 재생성할 수 있습니다.

### 🚀 빠른 설정 (권장)

```bash
# 한 번 실행으로 모든 설정 완료
./quick_setup.sh
```

### 🛠️ 수동 설정

```bash
# 전체 자동화 스크립트 실행
./setup_azure_sql_auto.sh

# 환경 변수 설정
source ./set_azure_env.sh

# 연결 테스트
python3 test_session_manager.py
```

### ⏰ 자동화 스케줄링

#### 1. Cron Job 설정 (매일 자동 실행)

```bash
# cron job 편집
crontab -e

# 매일 오전 9시에 자동 실행
0 9 * * * /Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh
```

#### 2. 수동 실행

```bash
# 즉시 실행
./cron_setup_azure.sh
```

### 📋 생성되는 파일들

- `azure_sql_config.py`: Azure SQL 연결 설정
- `set_azure_env.sh`: 환경 변수 설정 스크립트
- `/tmp/azure_sql_setup_*.log`: 실행 로그

### 🔍 상태 확인

```bash
# 현재 Azure SQL 서버 확인
az sql server list --resource-group kdb

# 연결 테스트
python3 test_session_manager.py

# 로그 확인
tail -f /tmp/azure_sql_setup_$(date +%Y%m%d).log
```

### 💡 주요 기능

- **자동 리소스 생성**: 타임스탬프 기반 고유 서버명
- **기존 리소스 정리**: 선택적으로 기존 서버 삭제
- **완전 자동화**: 서버 생성부터 연결 테스트까지
- **로그 시스템**: 색상 코딩된 상세 로그
- **Fallback 메커니즘**: Azure SQL 실패 시 메모리 기반으로 자동 전환

### 🔐 보안 정보

- **서버명**: `kdb-chatsession-{timestamp}`
- **데이터베이스**: `chatsession-db`
- **관리자 계정**: `kdbadmin`
- **비밀번호**: `ChatSession123!`
- **위치**: `eastus`

자세한 설정 가이드는 `setup_cron.md` 파일을 참고하세요.

## 🚀 사용법

### 기본 사용

```python
from backend.agent.multi_agent_system import get_magentic_system

# 시스템 초기화 (verbose=True로 상세 로그 출력)
system = get_magentic_system(verbose=True)

# 질문 처리
response = await system.process_query("급여는 언제 들어와요?")
print(response)
```

### 서비스용 사용 (로그 최소화)

```python
from backend.agent.multi_agent_system import get_magentic_system

# 조용한 모드로 시스템 초기화
system = get_magentic_system(verbose=False)

# 질문 처리
response = await system.process_query("KTDS 설립연도는 언제인가요?")
print(response)
```

### 스트림 방식 사용

```python
async for event in system.run_stream("최근 공지사항을 알려주세요"):
    print(event)
```

## 🤖 에이전트별 기능

### 🏢 HR_Agent
- **담당 업무**: 급여, 휴가, 교육, 복리후생, 인사 정보
- **사용 도구**: 5개 HR 전용 함수
- **예시 질문**: "급여는 언제 들어와요?", "휴가 신청 방법은?"

### 📋 Bulletin_Agent  
- **담당 업무**: 공지사항, 이벤트, 동호회, 식당, 교통 정보
- **사용 도구**: 6개 게시판 전용 함수
- **예시 질문**: "최근 공지사항은?", "구내식당 메뉴는?"

### 📊 Project_Agent
- **담당 업무**: 프로젝트 현황, 일정, 리소스, 리스크 관리
- **사용 도구**: 7개 프로젝트 관리 함수
- **예시 질문**: "진행 중인 프로젝트는?", "팀 워크로드는?"

### 🔍 KTDS_Info_Agent
- **담당 업무**: KTDS 회사 정보, 설립연혁, 사업영역
- **사용 도구**: Azure AI Search (실제 외부 데이터)
- **예시 질문**: "KTDS 설립연도는?", "주요 사업영역은?"

## 🔗 멀티홉 쿼리 지원

복합적인 질문도 자동으로 분해하여 처리합니다:

```python
# 여러 영역을 아우르는 질문
query = "급여 정보를 확인하고, 그 다음에 관련 교육 프로그램도 알려주세요"
response = await system.process_query(query)

# 다중 에이전트 협력이 필요한 질문  
query = "KTDS 설립연도를 찾고, 그 이후 현재 진행 중인 프로젝트 현황도 알려주세요"
response = await system.process_query(query)
```

## 📊 시스템 상태 확인

```python
status = system.get_system_status()
print(f"총 도구 수: {status['total_tools']}개")
print(f"사용 모델: {status['model']}")
```

## ⚙️ 설정 옵션

### KTDSMagenticOneSystem 매개변수

- `verbose` (bool): 상세 로그 출력 여부 (기본값: False)

### 시스템 제한

- **최대 턴**: 10턴
- **최대 메시지**: 10개
- **타임아웃**: 자동 설정

## 🛠️ 개발 정보

### 기술 스택

- **Microsoft AutoGen**: MagenticOne 아키텍처
- **Azure OpenAI**: GPT-4.1-mini 모델
- **Azure AI Search**: 하이브리드 검색
- **Python**: 비동기 프로그래밍

### 파일 구조

```
backend/agent/
├── multi_agent_system.py    # 메인 시스템
├── agent.py                 # 단일 KTDS 에이전트 (옵션)
├── agents/                  # Worker 에이전트들
│   ├── hr_agent.py
│   ├── bulletin_board_agent.py
│   ├── project_management_agent.py
│   └── ktds_info_agent.py
├── tools/                   # 에이전트별 도구들
│   ├── hr_tools.py
│   ├── bulletin_tools.py
│   └── project_tools.py
└── README.md               # 이 문서
```

## 🎯 성능 지표

- **평균 응답시간**: 10-15초
- **멀티홉 쿼리 성공률**: 90%+
- **총 도구 수**: 19개
- **지원 에이전트**: 4개

## 🔐 보안 주의사항

- API 키와 엔드포인트는 환경변수로 관리 권장
- 프로덕션 환경에서는 적절한 인증 및 권한 관리 필요
- 로그 레벨 조정으로 민감 정보 노출 방지

## 📞 지원

시스템 관련 문의사항은 개발팀에 연락하시기 바랍니다.

---

**KTDS MagenticOne 시스템** - 지능형 멀티에이전트로 더 스마트한 업무 처리를! 