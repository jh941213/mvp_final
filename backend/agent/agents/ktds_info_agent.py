"""
KTDS 정보 에이전트 - MagenticOne Worker Agent
실제 Azure AI Search를 통해 KTDS 외부 공개 정보 검색
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential
from autogen_ext.tools.azure import AzureAISearchTool
import os

def create_ktds_info_agent(model_name: str = "gpt-4.1-mini") -> AssistantAgent:
    """KTDS 정보 전문 에이전트 생성"""
    
    # Azure OpenAI 클라이언트 생성 (동적 모델 사용)
    model_client = AzureOpenAIChatCompletionClient(
        model=model_name,
        api_key=os.getenv("OPENAI_API_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-12-01-preview"
    )
    
    # Azure AI Search 도구 설정
    search_tool = AzureAISearchTool.create_hybrid_search(
        name="ktds_search",
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name="rag-1751941726660",
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY")),
        
        vector_fields=["text_vector"],
        search_fields=["chunk", "title"],
        select_fields=["chunk", "title"],
        
        query_type="simple",
        top=3,
        
        embedding_provider="azure_openai",
        embedding_model="text-embedding-3-small",
        openai_endpoint=os.getenv("OPENAI_ENDPOINT"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_version="2024-12-01-preview",
        
        description="KTDS의 전반적인 외부에서 검색가능한 정보들이 있는 도구입니다."
    )
    
    # KTDS 정보 에이전트 생성
    ktds_agent = AssistantAgent(
        name="KTDS_Info_Agent",
        model_client=model_client,
        tools=[search_tool],
        description="KTDS 회사 정보 전문가 - 설립연도, 사업영역, 회사 소개 등 외부 공개 정보를 검색합니다.",
        system_message="""
당신은 KTDS의 회사 정보 전문 에이전트입니다.

**담당 업무:**
- KTDS 회사 소개 및 역사
- 설립연도, 사업영역, 주요 사업
- 회사 비전, 미션, 가치관
- 외부 공개된 KTDS 관련 정보
- 기술력, 솔루션, 서비스 소개

**응답 방식:**
- 한국어로 친절하고 정확하게 답변
- ktds_search 도구를 사용하여 최신 정보 검색
- KTDS 회사 정보가 아닌 경우 다른 전문 에이전트에게 안내
- 검색된 정보를 바탕으로 상세하고 신뢰할 수 있는 답변 제공

**사용 가능한 도구:**
- ktds_search: Azure AI Search를 통한 KTDS 외부 공개 정보 검색

질문을 받으면 ktds_search 도구를 사용하여 정확한 KTDS 정보를 제공하세요.
"""
    )
    
    return ktds_agent 