"""
프로젝트 관리 에이전트 전용 도구들
프로젝트 계획, 진행, 리소스 관리 등 PM 관련 사내 합성 데이터 처리
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any


async def get_active_projects() -> str:
    """진행 중인 프로젝트 조회"""
    data = [
        {
            "project_id": "PRJ001",
            "name": "스마트시티 플랫폼 구축",
            "client": "서울시청",
            "status": "진행중",
            "progress": 65,
            "start_date": "2023-09-01",
            "end_date": "2024-03-31",
            "budget": 850000000,
            "spent_budget": 550000000,
            "team_size": 12,
            "pm": "김프로젝트",
            "next_milestone": "2024-02-15 중간 검수"
        },
        {
            "project_id": "PRJ002", 
            "name": "은행 디지털 전환 컨설팅",
            "client": "KB국민은행",
            "status": "진행중",
            "progress": 40,
            "start_date": "2023-11-01",
            "end_date": "2024-05-31",
            "budget": 1200000000,
            "spent_budget": 480000000,
            "team_size": 8,
            "pm": "이디지털",
            "next_milestone": "2024-02-28 요구사항 확정"
        },
        {
            "project_id": "PRJ003",
            "name": "AI 챗봇 개발",
            "client": "삼성전자",
            "status": "진행중", 
            "progress": 80,
            "start_date": "2023-08-01",
            "end_date": "2024-01-31",
            "budget": 300000000,
            "spent_budget": 240000000,
            "team_size": 6,
            "pm": "박인공지능",
            "next_milestone": "2024-01-20 최종 테스트"
        }
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_project_details(project_id: str = "PRJ001") -> str:
    """프로젝트 상세 정보 조회"""
    projects = {
        "PRJ001": {
            "project_id": "PRJ001",
            "name": "스마트시티 플랫폼 구축",
            "client": "서울시청",
            "status": "진행중",
            "progress": 65,
            "phases": [
                {"name": "요구사항 분석", "status": "완료", "progress": 100},
                {"name": "시스템 설계", "status": "완료", "progress": 100},
                {"name": "개발", "status": "진행중", "progress": 70},
                {"name": "테스트", "status": "대기", "progress": 0},
                {"name": "배포", "status": "대기", "progress": 0}
            ],
            "team_members": [
                {"name": "김프로젝트", "role": "PM", "allocation": 100},
                {"name": "이아키텍트", "role": "시스템 아키텍트", "allocation": 80},
                {"name": "박프론트", "role": "프론트엔드", "allocation": 100},
                {"name": "최백엔드", "role": "백엔드", "allocation": 100}
            ],
            "risks": [
                {"level": "중", "description": "외부 API 연동 지연"},
                {"level": "낮음", "description": "테스트 데이터 확보 이슈"}
            ]
        },
        "PRJ002": {
            "project_id": "PRJ002",
            "name": "은행 디지털 전환 컨설팅",
            "client": "KB국민은행",
            "status": "진행중",
            "progress": 40,
            "phases": [
                {"name": "현황 분석", "status": "완료", "progress": 100},
                {"name": "전략 수립", "status": "진행중", "progress": 60},
                {"name": "시스템 설계", "status": "대기", "progress": 0},
                {"name": "구현", "status": "대기", "progress": 0}
            ],
            "team_members": [
                {"name": "이디지털", "role": "PM", "allocation": 100},
                {"name": "김컨설턴트", "role": "비즈니스 컨설턴트", "allocation": 80},
                {"name": "정분석가", "role": "데이터 분석가", "allocation": 60}
            ],
            "risks": [
                {"level": "높음", "description": "고객사 내부 조직 변경"},
                {"level": "중", "description": "규제 변경 대응"}
            ]
        }
    }
    
    project = projects.get(project_id, projects["PRJ001"])
    return json.dumps(project, ensure_ascii=False, indent=2)


async def get_team_workload() -> str:
    """팀 워크로드 현황 조회"""
    data = [
        {
            "name": "김프로젝트",
            "role": "PM",
            "total_allocation": 100,
            "projects": [
                {"project": "PRJ001", "allocation": 100}
            ],
            "availability": "포화"
        },
        {
            "name": "이아키텍트", 
            "role": "시스템 아키텍트",
            "total_allocation": 120,
            "projects": [
                {"project": "PRJ001", "allocation": 80},
                {"project": "PRJ004", "allocation": 40}
            ],
            "availability": "과부하"
        },
        {
            "name": "박프론트",
            "role": "프론트엔드 개발자",
            "total_allocation": 80,
            "projects": [
                {"project": "PRJ001", "allocation": 80}
            ],
            "availability": "여유"
        },
        {
            "name": "최백엔드",
            "role": "백엔드 개발자", 
            "total_allocation": 100,
            "projects": [
                {"project": "PRJ001", "allocation": 60},
                {"project": "PRJ003", "allocation": 40}
            ],
            "availability": "포화"
        }
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_project_milestones() -> str:
    """프로젝트 마일스톤 현황 조회"""
    data = [
        {
            "project": "PRJ001 - 스마트시티 플랫폼",
            "milestones": [
                {
                    "name": "요구사항 분석 완료",
                    "date": "2023-10-31",
                    "status": "완료",
                    "completion_date": "2023-10-28"
                },
                {
                    "name": "시스템 설계 완료",
                    "date": "2023-12-15", 
                    "status": "완료",
                    "completion_date": "2023-12-10"
                },
                {
                    "name": "중간 검수",
                    "date": "2024-02-15",
                    "status": "예정",
                    "completion_date": null
                },
                {
                    "name": "최종 납품",
                    "date": "2024-03-31",
                    "status": "예정", 
                    "completion_date": null
                }
            ]
        },
        {
            "project": "PRJ002 - 은행 디지털 전환",
            "milestones": [
                {
                    "name": "현황 분석 완료",
                    "date": "2023-12-31",
                    "status": "완료",
                    "completion_date": "2023-12-20"
                },
                {
                    "name": "요구사항 확정",
                    "date": "2024-02-28",
                    "status": "진행중",
                    "completion_date": null
                },
                {
                    "name": "시스템 구축 완료",
                    "date": "2024-05-31",
                    "status": "예정",
                    "completion_date": null
                }
            ]
        }
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_resource_allocation() -> str:
    """리소스 할당 현황 조회"""
    data = {
        "summary": {
            "total_members": 25,
            "allocated_members": 20,
            "available_members": 5,
            "utilization_rate": "80%"
        },
        "by_role": [
            {
                "role": "PM",
                "total": 3,
                "allocated": 3,
                "available": 0,
                "utilization": "100%"
            },
            {
                "role": "시스템 아키텍트",
                "total": 2,
                "allocated": 2,
                "available": 0,
                "utilization": "100%"
            },
            {
                "role": "프론트엔드 개발자",
                "total": 8,
                "allocated": 6,
                "available": 2,
                "utilization": "75%"
            },
            {
                "role": "백엔드 개발자",
                "total": 10,
                "allocated": 8,
                "available": 2,
                "utilization": "80%"
            },
            {
                "role": "QA 엔지니어",
                "total": 2,
                "allocated": 1,
                "available": 1,
                "utilization": "50%"
            }
        ],
        "high_demand_skills": [
            "React",
            "Node.js", 
            "AWS",
            "AI/ML",
            "시스템 설계"
        ]
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_project_risks() -> str:
    """프로젝트 리스크 현황 조회"""
    data = [
        {
            "project": "PRJ001",
            "risks": [
                {
                    "id": "RSK001",
                    "description": "외부 API 연동 지연",
                    "probability": "중간",
                    "impact": "높음",
                    "level": "높음",
                    "mitigation": "대안 API 준비, 일정 버퍼 확보",
                    "owner": "이아키텍트"
                },
                {
                    "id": "RSK002",
                    "description": "테스트 데이터 확보 지연",
                    "probability": "낮음",
                    "impact": "중간",
                    "level": "낮음", 
                    "mitigation": "모의 데이터 생성 도구 준비",
                    "owner": "박프론트"
                }
            ]
        },
        {
            "project": "PRJ002",
            "risks": [
                {
                    "id": "RSK003",
                    "description": "고객사 조직 변경",
                    "probability": "높음",
                    "impact": "매우높음",
                    "level": "높음",
                    "mitigation": "다층 커뮤니케이션 채널 구축",
                    "owner": "이디지털"
                }
            ]
        }
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


async def create_project_report(project_id: str = "PRJ001") -> str:
    """프로젝트 보고서 생성"""
    reports = {
        "PRJ001": {
            "report_id": "RPT001",
            "project_id": "PRJ001", 
            "project_name": "스마트시티 플랫폼 구축",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "period": "2024년 1월",
            "summary": {
                "overall_progress": "65%",
                "schedule_status": "정상",
                "budget_status": "정상",
                "quality_status": "양호"
            },
            "achievements": [
                "백엔드 API 개발 80% 완료",
                "프론트엔드 화면 70% 완료",
                "데이터베이스 설계 완료"
            ],
            "challenges": [
                "외부 API 연동 일부 지연",
                "UI/UX 검토 과정 추가 필요"
            ],
            "next_actions": [
                "외부 API 연동 완료 (2월 1주)",
                "통합 테스트 준비 (2월 2주)",
                "중간 검수 준비 (2월 3주)"
            ],
            "kpi": {
                "진행률": "65%",
                "예산 집행률": "64.7%",
                "품질 지표": "95%",
                "고객 만족도": "4.2/5.0"
            }
        }
    }
    
    report = reports.get(project_id, {
        "error": f"프로젝트 {project_id}의 보고서를 찾을 수 없습니다.",
        "available_projects": list(reports.keys())
    })
    
    return json.dumps(report, ensure_ascii=False, indent=2) 