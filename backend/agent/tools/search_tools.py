"""
웹 검색 도구들
DuckDuckGo를 통한 실시간 웹 검색 기능 제공
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from ddgs import DDGS
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
import logging
import os

logger = logging.getLogger(__name__)

# 환경변수 설정
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')

async def web_search(query: str, max_results: int = 5, region: str = "kr-ko", timelimit: Optional[str] = None) -> str:
    """
    DuckDuckGo를 통한 웹 검색
    
    Args:
        query: 검색할 키워드나 질문
        max_results: 검색 결과 개수 (기본값: 5, 최대: 10)
        region: 검색 지역 (kr-ko: 한국, us-en: 미국, 기본값: kr-ko)
        timelimit: 시간 제한 (d: 하루, w: 일주일, m: 한달, y: 일년)
    
    Returns:
        검색 결과 문자열
    """
    try:
        # 검색 결과 개수 제한
        max_results = min(max_results, 10)
        
        # 동기 검색을 비동기로 래핑
        results = await asyncio.to_thread(_search_sync, query, max_results, region, timelimit)
        
        if not results:
            return f"'{query}'에 대한 검색 결과를 찾을 수 없습니다."
        
        # 결과를 포맷팅
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_result = f"""
**{i}. {result.get('title', 'No Title')}**
- URL: {result.get('href', 'No URL')}
- 내용: {result.get('body', 'No Description')}
"""
            formatted_results.append(formatted_result)
        
        return f"🔍 '{query}' 검색 결과:\n" + "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"DuckDuckGo 검색 오류: {str(e)}")
        return f"검색 중 오류가 발생했습니다: {str(e)}"


def _search_sync(query: str, max_results: int, region: str, timelimit: Optional[str]) -> List[Dict[str, Any]]:
    """동기 검색 실행"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                keywords=query,
                region=region,
                timelimit=timelimit,
                max_results=max_results
            ))
            return results
    except Exception as e:
        logger.error(f"동기 검색 오류: {str(e)}")
        return []


async def news_search(query: str, max_results: int = 5, region: str = "kr-ko", timelimit: str = "w") -> str:
    """
    DuckDuckGo를 통한 뉴스 검색
    
    Args:
        query: 검색할 뉴스 키워드
        max_results: 뉴스 결과 개수 (기본값: 5, 최대: 10)
        region: 검색 지역 (kr-ko: 한국, us-en: 미국, 기본값: kr-ko)
        timelimit: 시간 제한 (d: 하루, w: 일주일, m: 한달)
    
    Returns:
        뉴스 검색 결과 문자열
    """
    try:
        max_results = min(max_results, 10)
        
        results = await asyncio.to_thread(_news_search_sync, query, max_results, region, timelimit)
        
        if not results:
            return f"'{query}'에 대한 뉴스를 찾을 수 없습니다."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            date = result.get('date', 'No Date')
            formatted_result = f"""
**{i}. {result.get('title', 'No Title')}**
- 날짜: {date}
- 출처: {result.get('source', 'Unknown')}
- URL: {result.get('url', 'No URL')}
- 내용: {result.get('body', 'No Description')}
"""
            formatted_results.append(formatted_result)
        
        return f"📰 '{query}' 뉴스 검색 결과:\n" + "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"DuckDuckGo 뉴스 검색 오류: {str(e)}")
        return f"뉴스 검색 중 오류가 발생했습니다: {str(e)}"


def _news_search_sync(query: str, max_results: int, region: str, timelimit: str) -> List[Dict[str, Any]]:
    """동기 뉴스 검색 실행"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(
                keywords=query,
                region=region,
                timelimit=timelimit,
                max_results=max_results
            ))
            return results
    except Exception as e:
        logger.error(f"동기 뉴스 검색 오류: {str(e)}")
        return []


def create_search_agent(orchestrator_client, model_name: str = "gpt-4.1-mini") -> AssistantAgent:
    """검색 전문 에이전트 생성"""
    
    # 동적 모델 클라이언트 생성
    from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
    
    model_client = AzureOpenAIChatCompletionClient(
        model=model_name,
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION
    )
    
    search_agent = AssistantAgent(
        name="Search_Agent",
        model_client=model_client,
        tools=[web_search, news_search],  # tools 매개변수로 직접 전달
        description="웹 검색 전문가 - 실시간 정보 검색 및 최신 뉴스 제공",
        system_message="""
당신은 웹 검색 전문 에이전트입니다.

**담당 업무:**
- 실시간 웹 정보 검색
- 최신 뉴스 및 동향 검색
- 기술 정보, 시장 동향, 일반 정보 검색
- 검색 결과 분석 및 요약

**응답 방식:**
- 한국어로 친절하고 정확하게 답변
- web_search 함수로 일반 웹 검색
- news_search 함수로 최신 뉴스 검색
- 검색 결과를 바탕으로 종합적인 정보 제공
- 출처와 날짜를 명시하여 신뢰성 확보

**사용 가능한 함수:**
- web_search: DuckDuckGo 웹 검색
- news_search: DuckDuckGo 뉴스 검색

질문을 받으면 적절한 검색 함수를 사용하여 최신 정보를 제공하세요.
"""
    )
    
    return search_agent


# 호환성을 위한 래퍼 함수들
def create_web_search_tool():
    """웹 검색 도구 생성 (호환성용)"""
    return web_search


def create_news_search_tool():
    """뉴스 검색 도구 생성 (호환성용)"""
    return news_search 