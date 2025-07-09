"""
HR 에이전트 - MagenticOne Worker Agent
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.hr_tools import (
    get_salary_info, 
    get_vacation_info, 
    get_education_programs,
    get_employee_directory,
    get_welfare_benefits
)


def create_hr_agent(model_name: str = "gpt-4.1-mini") -> AssistantAgent:
    """HR 전문 에이전트 생성"""
    
    # Azure OpenAI 클라이언트 생성 (동적 모델 사용)
    model_client = AzureOpenAIChatCompletionClient(
        model=model_name,
        api_key=os.getenv("OPENAI_API_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-12-01-preview"
    )
    # HR 전용 도구들
    hr_tools = [
        get_salary_info,
        get_vacation_info, 
        get_education_programs,
        get_employee_directory,
        get_welfare_benefits
    ]
    
    # HR 에이전트 생성
    hr_agent = AssistantAgent(
        name="HR_Agent",
        model_client=model_client,
        tools=hr_tools,
        description="HR 관련 업무 전문가 - 급여, 휴가, 교육, 복리후생, 인사 정보를 담당합니다.",
        system_message="""
당신은 KTDS의 HR 전문 에이전트입니다.

**담당 업무:**
- 급여 및 수당 정보
- 휴가 및 근태 관리  
- 교육 프로그램 안내
- 임직원 디렉토리
- 복리후생 정보

**응답 방식:**
- 한국어로 친절하고 정확하게 답변
- 관련 도구를 사용하여 최신 정보 제공
- HR 관련 질문이 아닌 경우 다른 전문 에이전트에게 안내

**사용 가능한 도구:**
- get_salary_info(): 급여 정보 조회
- get_vacation_info(): 휴가 정보 조회  
- get_education_programs(): 교육 프로그램 조회
- get_employee_directory(): 임직원 디렉토리 조회
- get_welfare_benefits(): 복리후생 정보 조회

질문을 받으면 적절한 도구를 사용하여 정확한 정보를 제공하세요.
"""
    )
    
    return hr_agent 