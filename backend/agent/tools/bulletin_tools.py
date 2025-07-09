"""
게시판 에이전트 전용 도구들
공지사항, 이벤트, 동호회 등 사내 커뮤니케이션 사내 합성 데이터 처리
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any


async def get_recent_announcements() -> str:
    """최근 공지사항 조회"""
    data = [
        {
            "id": "ANN001",
            "title": "2024년 상반기 워크숍 개최 안내",
            "content": "전 직원 대상 워크숍이 3월 15일(금) 오후 2시 본사 대강당에서 개최됩니다.",
            "date": "2024-01-10",
            "author": "인사팀",
            "priority": "high",
            "views": 324
        },
        {
            "id": "ANN002", 
            "title": "주차장 이용 규칙 변경 안내",
            "content": "2월 1일부터 주차장 이용 시간이 07:00~21:00으로 변경됩니다.",
            "date": "2024-01-08",
            "author": "총무팀",
            "priority": "medium",
            "views": 189
        },
        {
            "id": "ANN003",
            "title": "신년 하례식 개최 안내",
            "content": "1월 15일(월) 오전 10시 대강당에서 신년 하례식이 열립니다.",
            "date": "2024-01-05",
            "author": "경영진",
            "priority": "high",
            "views": 567
        }
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_company_events() -> str:
    """회사 이벤트 정보 조회"""
    data = [
        {
            "id": "EVT001",
            "title": "2024 체육대회",
            "date": "2024-04-20",
            "location": "올림픽공원 체조경기장",
            "description": "전 직원 참여 체육대회 및 가족 행사",
            "registration_deadline": "2024-04-01",
            "contact": "복지팀 (내선: 4567)"
        },
        {
            "id": "EVT002", 
            "title": "창립기념일 기념행사",
            "date": "2024-05-15",
            "location": "본사 대강당",
            "description": "창립 20주년 기념식 및 우수사원 시상",
            "registration_deadline": "참석 필수",
            "contact": "총무팀 (내선: 9876)"
        },
        {
            "id": "EVT003",
            "title": "하계 워크샵",
            "date": "2024-07-26~27",
            "location": "부산 해운대",
            "description": "2024년 하반기 전략 워크샵 및 팀빌딩",
            "registration_deadline": "2024-07-01",
            "contact": "기획팀 (내선: 5555)"
        }
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_club_activities() -> str:
    """동호회 활동 정보 조회"""
    data = [
        {
            "name": "축구동호회",
            "description": "매주 토요일 축구 경기",
            "schedule": "매주 토요일 오후 3시",
            "location": "근처 풋살장",
            "members": 24,
            "contact": "김축구 (내선: 1111)",
            "recent_activity": "1월 13일 신년 친선 경기"
        },
        {
            "name": "등산동호회",
            "description": "월 2회 등산 및 트레킹",
            "schedule": "격주 일요일",
            "location": "수도권 명산",
            "members": 18,
            "contact": "이산행 (내선: 2222)",
            "recent_activity": "1월 7일 북한산 등반"
        },
        {
            "name": "독서모임",
            "description": "월 1회 도서 토론",
            "schedule": "매월 셋째 주 금요일",
            "location": "카페테리아",
            "members": 12,
            "contact": "박독서 (내선: 3333)",
            "recent_activity": "12월 도서: '사피엔스' 토론"
        },
        {
            "name": "볼링동호회",
            "description": "매주 볼링 게임",
            "schedule": "매주 목요일 오후 7시",
            "location": "강남 볼링장",
            "members": 15,
            "contact": "최볼링 (내선: 4444)",
            "recent_activity": "1월 월례 토너먼트"
        }
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


async def search_bulletin_posts(keyword: str = "") -> str:
    """게시판 글 검색"""
    posts = [
        {
            "id": "POST001",
            "title": "점심 메뉴 추천해주세요",
            "content": "오늘 점심 뭐 먹을지 고민이에요. 맛있는 식당 추천 부탁드립니다.",
            "author": "미식가123",
            "date": "2024-01-12",
            "category": "자유게시판",
            "replies": 8
        },
        {
            "id": "POST002",
            "title": "프로젝트 관리 도구 추천",
            "content": "효율적인 프로젝트 관리를 위한 도구들을 공유해주세요.",
            "author": "PM김",
            "date": "2024-01-11", 
            "category": "업무토론",
            "replies": 15
        },
        {
            "id": "POST003",
            "title": "신입사원 환영회",
            "content": "이번 달 신입사원들을 위한 환영회를 준비하고 있습니다.",
            "author": "인사팀",
            "date": "2024-01-10",
            "category": "공지사항",
            "replies": 3
        }
    ]
    
    if keyword:
        filtered_posts = [post for post in posts if keyword in post["title"] or keyword in post["content"]]
        return json.dumps(filtered_posts, ensure_ascii=False, indent=2)
    
    return json.dumps(posts, ensure_ascii=False, indent=2)


async def get_cafeteria_menu() -> str:
    """구내식당 메뉴 조회"""
    today = datetime.now().strftime("%Y-%m-%d")
    data = {
        "date": today,
        "breakfast": {
            "time": "08:00~09:30",
            "menu": [
                "계란말이",
                "토스트",
                "시리얼",
                "우유/커피"
            ]
        },
        "lunch": {
            "time": "12:00~14:00",
            "korean": [
                "bulgogi",
                "kimchi stew",
                "rice",
                "side dishes"
            ],
            "western": [
                "pasta",
                "salad",
                "bread"
            ]
        },
        "dinner": {
            "time": "18:00~19:30",
            "menu": [
                "grilled fish",
                "vegetables",
                "soup",
                "rice"
            ]
        },
        "special": "오늘의 특선: 갈비탕",
        "price": "직원 무료, 외부인 5,000원"
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


async def get_shuttle_schedule() -> str:
    """셔틀버스 운행 정보 조회"""
    data = {
        "routes": [
            {
                "name": "강남역 ↔ 본사",
                "morning": ["07:30", "08:00", "08:30", "09:00"],
                "evening": ["18:00", "18:30", "19:00", "19:30"],
                "duration": "약 25분"
            },
            {
                "name": "잠실역 ↔ 본사",
                "morning": ["07:45", "08:15", "08:45"],
                "evening": ["18:15", "18:45", "19:15"],
                "duration": "약 20분"
            },
            {
                "name": "판교역 ↔ 본사",
                "morning": ["08:00", "08:30"],
                "evening": ["18:30", "19:00"],
                "duration": "약 15분"
            }
        ],
        "notice": [
            "탑승 5분 전까지 승차장 대기",
            "만석 시 다음 차량 이용",
            "사내 ID카드 지참 필수"
        ],
        "contact": "교통팀 (내선: 7777)"
    }
    return json.dumps(data, ensure_ascii=False, indent=2) 


async def get_current_time() -> str:
    """현재 시간 조회"""
    current = datetime.now()
    return f"현재 시간: {current.strftime('%Y년 %m월 %d일 %H시 %M분')}" 