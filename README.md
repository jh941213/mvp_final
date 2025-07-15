# 🌐 KTDS Azure Enterprise Multi-Agent System

## 📋 서비스 개요

**KTDS Azure Enterprise Multi-Agent System**은 Microsoft Azure 클라우드 인프라를 기반으로 구축된 차세대 엔터프라이즈 AI 플랫폼입니다. AutoGen 멀티에이전트 아키텍처와 Azure AI 서비스를 통합하여 지능형 업무 자동화와 의사결정 지원을 제공합니다.

## 🏗️ Azure 클라우드 아키텍처
<img width="4594" height="4627" alt="as" src="https://github.com/user-attachments/assets/65856837-613f-43a7-8f1a-dc004d937185" />


## 💡 Agent 아키텍처

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         🎯 KTDS Multi-Agent Query Router                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📥 User Query Input                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────┐                                                     │
│  │  🔍 QueryClassifier │ ◄──── GPT-4o-mini (고정)                             │
│  │    (GPT-4.1-nano)    │                                                    │
│  └─────────────────────┘                                                     │
│           │                                                                  │
│           ▼                                                                  │
│  ┌───────────────────────────────────────┐                                   │
│  │         Classification Result         │                                   │
│  └───────────────────────────────────────┘                                   │
│           │                                                                  │
│      ┌────┴────┐                                                             │
│      ▼         ▼                                                             │
│                                                                              │
├─[SIMPLE]──────────────────────┬─[COMPLEX]────────────────────────────────────┤
│                               │                                              │
│  💬 SimpleKTDSAgent           │  🤖 MagenticOne Multi-Agent System            │
│  ┌─────────────────────────┐  │  ┌─────────────────────────────────────────  │
│  │     Midm-2.0 Base       │  │  │         Orchestrator Agent              │ │
│  │   (Friendli API)        │  │  │      (Azure OpenAI GPT-4.1)             │ │
│  │                         │  │  └─────────────────────────────────────────┘ │
│  │  • 일반 대화              │  │           │                                  │
│  │  • 인사말                │  │           ▼                                   │
│  │  • 단순 질문응답           │  │  ┌─────────────────────────────────────────┐  │
│  │  • 창의적 대화             │  │  │            Agent Router                │  │
│  └─────────────────────────┘  │  │         (질문 유형 분석)                   │  │
│                               │  └─────────────────────────────────────────┘ │
│                               │           │                                  │
│                               │      ┌────┼────┬────┬────┬────┐              │
│                               │      ▼    ▼    ▼    ▼    ▼    ▼              │
│                               │                                              │
│                               │  ┌─────────────────────────────────────────┐ │
│                               │  │           Specialized Agents            │ │
│                               │  │                                         │ │
│                               │  │  🏢 HR Agent                            │ │
│                               │  │  ├─ 급여, 휴가, 교육, 복리후생               │ │
│                               │  │  └─ Tools (5개):                        │ │
│                               │  │     • get_salary_info                  │ │
│                               │  │     • get_vacation_info                │ │
│                               │  │     • get_education_programs           │ │
│                               │  │     • get_employee_directory           │ │
│                               │  │     • get_welfare_benefits             │ │
│                               │  │                                        │ │
│                               │  │  📋 Bulletin Board Agent               │ │
│                               │  │  ├─ 공지사항, 이벤트, 동호회, 식당           │ │
│                               │  │  └─ Tools (6개):                       │ │
│                               │  │     • get_recent_announcements         │ │
│                               │  │     • get_company_events               │ │
│                               │  │     • get_club_activities              │ │
│                               │  │     • search_bulletin_posts            │ │
│                               │  │     • get_cafeteria_menu               │ │
│                               │  │     • get_shuttle_schedule             │ │
│                               │  │                                        │ │
│                               │  │  📊 Project Management Agent           │ │
│                               │  │  ├─ 프로젝트 관리, 일정, 리소스, 리스크       │ │
│                               │  │  └─ Tools (7개):                       │ │
│                               │  │     • get_active_projects              │ │
│                               │  │     • get_project_details              │ │
│                               │  │     • get_team_workload                │ │
│                               │  │     • get_project_milestones           │ │
│                               │  │     • get_resource_allocation          │ │
│                               │  │     • get_project_risks                │ │
│                               │  │     • create_project_report            │ │
│                               │  │                                        │ │
│                               │  │  🔍 KTDS Info Agent                    │ │
│                               │  │  ├─ 회사 정보, 검색, 지식베이스              │ │
│                               │  │  └─ Tools:                             │ │
│                               │  │     • Azure AI Search Integration      │ │
│                               │  │     • Knowledge Base Query             │ │
│                               │  │     • Company Info Retrieval           │ │
│                               │  │                                        │ │
│                               │  │  💬 Midm Agent                         │ │
│                               │  │  ├─ 일반 대화, 창의적 응답                  │ │
│                               │  │  └─ Tools:                             │ │
│                               │  │     • Friendli AI Integration          │ │
│                               │  │     • Creative Conversation            │ │
│                               │  │     • General Chat Processing          │ │
│                               │  │                                        │ │
│                               │  │  🌐 Web Search Agent                   │ │
│                               │  │  ├─ 실시간 웹 검색, 뉴스, 외부 정보          │ │
│                               │  │  └─ Tools (2개):                       │ │
│                               │  │     • web_search (DuckDuckGo)          │ │
│                               │  │     • news_search (DuckDuckGo News)    │ │
│                               │  └─────────────────────────────────────────┘│
│                               │           │                                 │
│                               │           ▼                                 │
│                               │  ┌─────────────────────────────────────────┐│
│                               │  │         Response Aggregator             ││
│                               │  │        (응답 통합 및 정제)                  ││
│                               │  └─────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│                               📤 Unified Response                           │
│                                                                             │
│  🔄 Session Management        📊 Performance Monitor                         │
│  ├─ Azure SQL Storage         ├─ Response Time Tracking                     │
│  ├─ Conversation History      ├─ Agent Usage Statistics                     │
│  └─ Context Continuity        └─ Error Rate Monitoring                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                        🔧 분류 기준 (Classification Logic)                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  🟢 SIMPLE 처리 (SimpleKTDSAgent)                                                 │
│  ├─ 일반적인 인사말 ("안녕하세요", "감사합니다")                                          │
│  ├─ 단순 대화 ("날씨가 좋네요", "어떻게 지내세요?")                                       │
│  ├─ 간단한 질문/응답 ("이름이 뭐예요?", "오늘 몇 시예요?")                                 │    
│  └─ 창의적 대화 (시, 이야기, 농담 등)                                                  │
│                                                                                 │
│  🔴 COMPLEX 처리 (MagenticOne Multi-Agent)                                        │
│  ├─ 🏢 HR 관련: 급여정보, 휴가신청, 복리후생, 교육프로그램, 임직원정보                        │
│  ├─ 📋 게시판 관련: 공지사항, 이벤트, 동호회, 식당메뉴, 셔틀버스정보                           │
│  ├─ 📊 프로젝트 관리: 진행현황, 일정관리, 리소스할당, 마일스톤, 리스크관리                      │
│  ├─ 🔍 KTDS 정보: 회사소개, 사업영역, 연혁, 솔루션, 지식베이스검색                           │
│  ├─ 🌐 웹 검색: 최신뉴스, 기술동향, 실시간정보, 외부데이터수집                               │
│  └─ 🔗 멀티홉 쿼리: 여러 도메인에 걸친 복합 질문 및 통합 분석                                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 핵심 기능

### 🎯 지능형 멀티에이전트 시스템
- **Orchestrator Agent**: 작업 분배 및 조율
- **HR Agent**: 인사관리, 급여, 복리후생 전문
- **Works AI Agent**: 업무 자동화 및 프로세스 최적화  
- **Project Management Agent**: 프로젝트 관리 및 리소스 계획
- **KTDS Info Agent**: 회사 정보 및 지식 검색

### 🌊 실시간 스트리밍 & STORM 연구
- **WebSocket 기반 실시간 통신**
- **STORM Research Engine**: 심층 연구 및 위키 문서 생성
- **Progress Tracking**: 실시간 진행상황 모니터링
- **Markdown Export**: 연구 결과 자동 다운로드

### 🔐 엔터프라이즈 보안 & 세션 관리
- **Azure Active Directory 통합**
- **UUID 기반 세션 관리**
- **대화 기록 영구 저장**
- **역할 기반 접근 제어**

## 🏢 Azure 인프라 구성

### 🌐 웹 서비스 계층
```typescript
// Azure Web App + Next.js React Frontend
- Azure App Service (웹 호스팅)
- Next.js 13+ (App Router)
- TypeScript + Tailwind CSS
- Real-time WebSocket 클라이언트
```

### ⚡ API 서비스 계층
```python
// FastAPI Backend Service
- Azure Container Instances
- Python 3.12 + FastAPI
- WebSocket 스트리밍 지원
- Pydantic 데이터 검증
- CORS & 미들웨어 보안
```

### 🤖 AI 서비스 계층
```yaml
Azure AI Services:
  - Azure OpenAI Service: 
    - GPT-4o, GPT-4o-mini
    - 토큰 관리 및 비용 최적화
  - Azure AI Foundry:
    - 모델 배포 및 관리
    - A/B 테스트 지원
  - Azure Cognitive Services:
    - 텍스트 분석 및 번역
```

### 💾 데이터 서비스 계층
```yaml
Azure Data Services:
  - Azure SQL Database:
    - 세션 및 사용자 데이터
    - 자동 백업 및 복제
  - Azure Blob Storage:
    - 파일 및 이미지 저장
    - CDN 통합
  - Azure Cosmos DB:
    - 문서 및 NoSQL 데이터
    - 글로벌 분산
  - Azure Cache for Redis:
    - 세션 캐시
    - 실시간 데이터 캐싱
```

## 🛠️ 개발 환경 설정

### 1️⃣ Prerequisites
```bash
# Azure CLI 설치
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Node.js & Python 환경
node --version  # v18+
python --version  # 3.12+
```

### 2️⃣ 백엔드 설정
```bash
# 백엔드 디렉토리 이동
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.template .env
# .env 파일을 편집하여 Azure 리소스 정보 입력

# 백엔드 서버 실행
./run_backend.sh development
```

### 3️⃣ 프론트엔드 설정
```bash
# 프론트엔드 디렉토리 이동
cd frontend/my-app

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 4️⃣ Azure 리소스 자동 설정
```bash
# Azure 로그인
az login

# 리소스 자동 생성 스크립트 실행
./backend/scripts/setup_azure_sql_auto.sh
```

## 🔧 주요 API 엔드포인트

### 💬 채팅 API
```bash
# 일반 채팅
POST /api/v1/chat
{
  "message": "급여는 언제 들어오나요?",
  "session_id": "uuid",
  "user_id": "kim.db@kt.com",
  "agent_mode": "normal"
}

# 실시간 스트리밍
POST /api/v1/stream
{
  "message": "프로젝트 현황을 분석해주세요",
  "session_id": "uuid", 
  "agent_mode": "storm"
}
```

### 📋 세션 관리 API
```bash
# 세션 목록 조회
GET /api/v1/sessions?user_id=kim.db@kt.com

# 새 세션 생성
POST /api/v1/sessions
{
  "user_id": "kim.db@kt.com",
  "session_name": "새로운 대화"
}

# 세션 히스토리
GET /api/v1/sessions/{session_id}
```

### 🤖 시스템 관리 API
```bash
# 헬스체크
GET /api/v1/health

# 에이전트 상태
GET /api/v1/system/agents

# 사용 가능한 모델
GET /api/v1/chat/models
```

## 📊 모니터링 & 성능

### 🔍 Azure Monitor 통합
- **Application Insights**: 성능 및 오류 추적
- **Log Analytics**: 중앙화된 로그 관리
- **Azure Metrics**: 실시간 메트릭 모니터링
- **Alert Rules**: 자동화된 알림 시스템

### 📈 성능 지표
```yaml
SLA 목표:
  - API 응답시간: < 3초 (95%ile)
  - 가용성: 99.9%
  - 동시 사용자: 100명+
  - 스트리밍 지연: < 500ms

모니터링 메트릭:
  - 에이전트 응답 시간
  - 토큰 사용량 및 비용
  - 세션 활성도
  - 오류율 및 재시도 횟수
```

## 🔐 보안 & 컴플라이언스

### 🛡️ 보안 기능
- **Azure AD 통합**: Single Sign-On (SSO)
- **RBAC**: 역할 기반 접근 제어
- **API Keys**: 서비스 간 인증
- **TLS 1.3**: 전송 계층 암호화
- **WAF**: 웹 애플리케이션 방화벽

### 📋 컴플라이언스
- **GDPR**: 개인정보 보호 준수
- **ISO 27001**: 정보보안 관리
- **SOC 2**: 보안 및 가용성 인증

## 🚀 배포 & 운영

### 🔄 CI/CD 파이프라인
```yaml
GitHub Actions:
  - 코드 품질 검사
  - 자동화된 테스트
  - Azure 배포 자동화
  - 롤백 지원

Azure DevOps:
  - 인프라 as Code (Terraform)
  - 환경별 배포 관리
  - 승인 워크플로우
```

### 🌍 다중 환경 관리
```bash
# 개발 환경
az webapp deployment slot create --name dev --resource-group ktds-rg

# 스테이징 환경  
az webapp deployment slot create --name staging --resource-group ktds-rg

# 프로덕션 환경
az webapp deployment slot swap --slot staging --resource-group ktds-rg
```

## 🎯 로드맵

### 🔮 2024 Q4
- [x] 멀티에이전트 시스템 구축
- [x] Azure 인프라 구성
- [x] 실시간 스트리밍 구현
- [ ] 모바일 앱 지원

### 🚀 2025 Q1
- [ ] Graph RAG 고도화
- [ ] Voice AI 통합
- [ ] 다국어 지원 확장
- [ ] Azure OpenAI GPT-4 Turbo 업그레이드

### 🌟 2025 Q2
- [ ] Microsoft Copilot 통합
- [ ] Power Platform 연동
- [ ] 고급 분석 대시보드
- [ ] 엔터프라이즈 API 제공

## 📞 지원 & 연락처

### 🆘 기술 지원
- **개발팀**: dev-team@ktds.com
- **시스템 관리**: sysadmin@ktds.com
- **보안 문의**: security@ktds.com

### 📚 문서 및 리소스
- **API 문서**: [Swagger UI](/docs)
- **개발자 가이드**: [Developer Portal](/dev)
- **사용자 매뉴얼**: [User Guide](/guide)

---

## 🏆 라이선스 & 크레딧

**KTDS Azure Enterprise Multi-Agent System** © 2024 KT ds

Built with 💙 using Microsoft Azure, AutoGen, and cutting-edge AI technologies.

---

*🌐 더 스마트한 미래, 더 효율적인 업무 - KTDS Azure AI가 함께합니다!* 
