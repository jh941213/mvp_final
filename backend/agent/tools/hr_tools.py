"""
HR 에이전트 전용 도구들
급여, 휴가, 교육, 복리후생 등 HR 관련 사내 합성 데이터 처리
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any


async def get_salary_info() -> str:
    """급여 정보 조회 - 급여 지급일, 공제 내역 등"""
    data = {
        "pay_date": "매월 마지막 영업일",
        "pay_schedule": {
            "regular_salary": "매월 마지막 영업일 오후 3시",
            "bonus": "6월, 12월 (연 2회)",
            "overtime": "급여와 함께 지급"
        },
        "deductions": [
            "국민연금 4.5%",
            "건강보험 3.545%", 
            "고용보험 0.9%",
            "소득세 (간이세액표 기준)"
        ],
        "contact": "인사팀 (내선: 1234, hr@ktds.com)"
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_vacation_info() -> str:
    """휴가 정보 조회 - 연차, 특별휴가 등"""
    data = {
        "annual_leave": {
            "첫해": "11일",
            "1년 이상": "15일",
            "3년 이상": "16일",
            "5년 이상": "18일",
            "10년 이상": "20일",
            "15년 이상": "22일",
            "20년 이상": "25일"
        },
        "special_leave": [
            "경조사휴가: 결혼 5일, 자녀결혼 1일, 회갑 1일",
            "출산휴가: 90일 (법정)",
            "육아휴직: 1년 (법정)",
            "병가: 연 60일 한도"
        ],
        "application_process": "인사포털 > 휴가신청 > 상급자 승인",
        "contact": "인사팀 (내선: 1234)"
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_education_programs() -> str:
    """교육 프로그램 조회"""
    data = {
        "internal_programs": [
            {
                "name": "신입사원 온보딩",
                "duration": "2주",
                "schedule": "매월 첫째 주",
                "target": "신입사원"
            },
            {
                "name": "리더십 교육",
                "duration": "3일",
                "schedule": "분기별",
                "target": "팀장급 이상"
            },
            {
                "name": "기술 세미나",
                "duration": "반일",
                "schedule": "월 2회",
                "target": "개발자"
            }
        ],
        "external_programs": [
            {
                "name": "AWS 자격증 과정",
                "support": "교육비 100% 지원",
                "condition": "합격 시 포상금 지급"
            },
            {
                "name": "PMP 자격증 과정", 
                "support": "교육비 50% 지원",
                "condition": "1년 근속 후 환급"
            }
        ],
        "application": "인사포털 > 교육신청",
        "contact": "교육팀 (내선: 2345)"
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_employee_directory() -> str:
    """임직원 디렉토리 조회"""
    data = {
        "search_methods": [
            "이름으로 검색",
            "부서별 조회", 
            "직급별 조회",
            "업무 키워드 검색"
        ],
        "sample_contacts": [
            {
                "name": "김대표",
                "position": "대표이사",
                "department": "경영진",
                "extension": "1000",
                "email": "ceo@ktds.com"
            },
            {
                "name": "이인사",
                "position": "팀장",
                "department": "인사팀", 
                "extension": "1234",
                "email": "hr@ktds.com"
            },
            {
                "name": "박개발",
                "position": "선임연구원",
                "department": "기술개발팀",
                "extension": "3456",
                "email": "dev@ktds.com"
            }
        ],
        "access": "인사포털 > 조직도 > 임직원 검색",
        "privacy": "개인정보보호법에 따라 업무 관련 정보만 공개"
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_welfare_benefits() -> str:
    """복리후생 정보 조회"""
    data = {
        "insurance": {
            "4대보험": "법정 가입",
            "단체보험": "생명보험, 상해보험 가입",
            "건강검진": "연 1회 종합검진 (배우자 포함)"
        },
        "allowances": [
            "식대: 월 20만원",
            "교통비: 월 15만원", 
            "통신비: 월 5만원",
            "자기계발비: 연 100만원"
        ],
        "facilities": [
            "구내식당: 조식, 중식, 석식 제공",
            "헬스장: 24시간 이용 가능",
            "카페테리아: 무료 커피/차",
            "주차장: 무료 주차"
        ],
        "vacation": [
            "콘도: 제휴 콘도 할인 이용",
            "리조트: 사내 휴양소 운영",
            "해외연수: 우수사원 대상 연 1회"
        ],
        "family_support": [
            "출산축하금: 200만원",
            "자녀학자금: 고등학교까지 지원",
            "경조사비: 경조사별 차등 지급"
        ],
        "contact": "복지팀 (내선: 4567)"
    }
    return json.dumps(data, ensure_ascii=False, indent=2) 