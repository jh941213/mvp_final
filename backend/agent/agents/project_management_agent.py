"""
프로젝트 관리 에이전트 - MagenticOne Worker Agent
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.project_tools import (
    get_active_projects,
    get_project_details,
    get_team_workload,
    get_project_milestones,
    get_resource_allocation,
    get_project_risks,
    create_project_report
)


def create_project_agent(model_name: str = "gpt-4.1-mini") -> AssistantAgent:
    """프로젝트 관리 전문 에이전트 생성"""
    
    # Azure OpenAI 클라이언트 생성 (동적 모델 사용)
    model_client = AzureOpenAIChatCompletionClient(
        model=model_name,
        api_key=os.getenv("OPENAI_API_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-12-01-preview"
    )
    
    # 프로젝트 관리 전용 도구들
    project_tools = [
        get_active_projects,
        get_project_details,
        get_team_workload,
        get_project_milestones,
        get_resource_allocation,
        get_project_risks,
        create_project_report
    ]
    
    # 프로젝트 관리 에이전트 생성
    project_agent = AssistantAgent(
        name="Project_Agent",
        model_client=model_client,
        tools=project_tools,
        description="프로젝트 관리 전문가 - 프로젝트 현황, 일정, 리소스, 리스크 관리를 담당합니다.",
        system_message="""
당신은 KTDS의 프로젝트 관리 전문 에이전트입니다.

**담당 업무:**
- 프로젝트 현황 및 진행 상태
- 프로젝트 상세 정보 제공
- 팀 워크로드 관리
- 프로젝트 마일스톤 추적
- 리소스 할당 현황
- 리스크 모니터링
- 프로젝트 보고서 생성

**응답 방식:**
- 한국어로 친절하고 정확하게 답변
- 관련 도구를 사용하여 최신 정보 제공
- 프로젝트 관리 질문이 아닌 경우 다른 전문 에이전트에게 안내

**사용 가능한 도구:**
- get_active_projects(): 진행 중인 프로젝트 조회
- get_project_details(): 프로젝트 상세 정보 조회
- get_team_workload(): 팀 워크로드 현황 조회
- get_project_milestones(): 프로젝트 마일스톤 현황 조회
- get_resource_allocation(): 리소스 할당 현황 조회
- get_project_risks(): 프로젝트 리스크 현황 조회
- create_project_report(): 프로젝트 보고서 생성

질문을 받으면 적절한 도구를 사용하여 정확한 정보를 제공하세요.
"""
    )
    
    return project_agent 