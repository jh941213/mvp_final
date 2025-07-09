"""
게시판 에이전트 - MagenticOne Worker Agent  
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.bulletin_tools import (
    get_recent_announcements,
    get_company_events,
    get_club_activities,
    search_bulletin_posts,
    get_cafeteria_menu,
    get_shuttle_schedule
)


def create_bulletin_agent(model_name: str = "gpt-4.1-mini") -> AssistantAgent:
    """게시판 전문 에이전트 생성"""
    
    # Azure OpenAI 클라이언트 생성 (동적 모델 사용)
    model_client = AzureOpenAIChatCompletionClient(
        model=model_name,
        api_key=os.getenv("OPENAI_API_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-12-01-preview"
    )
    
    # 게시판 전용 도구들
    bulletin_tools = [
        get_recent_announcements,
        get_company_events,
        get_club_activities,
        search_bulletin_posts,
        get_cafeteria_menu,
        get_shuttle_schedule
    ]
    
    # 게시판 에이전트 생성
    bulletin_agent = AssistantAgent(
        name="Bulletin_Agent",
        model_client=model_client,
        tools=bulletin_tools,
        description="사내 게시판 및 커뮤니케이션 전문가 - 공지사항, 이벤트, 동호회, 식당, 교통 정보를 담당합니다.",
        system_message="""
당신은 KTDS의 사내 게시판 전문 에이전트입니다.

**담당 업무:**
- 공지사항 및 알림
- 회사 이벤트 정보
- 동호회 활동 안내
- 게시판 글 검색
- 구내식당 메뉴
- 셔틀버스 운행 정보

**응답 방식:**
- 한국어로 친절하고 정확하게 답변
- 관련 도구를 사용하여 최신 정보 제공
- 게시판 관련 질문이 아닌 경우 다른 전문 에이전트에게 안내

**사용 가능한 도구:**
- get_recent_announcements(): 최근 공지사항 조회
- get_company_events(): 회사 이벤트 정보 조회
- get_club_activities(): 동호회 활동 정보 조회
- search_bulletin_posts(): 게시판 글 검색
- get_cafeteria_menu(): 구내식당 메뉴 조회
- get_shuttle_schedule(): 셔틀버스 운행 정보 조회

질문을 받으면 적절한 도구를 사용하여 정확한 정보를 제공하세요.
"""
    )
    
    return bulletin_agent 