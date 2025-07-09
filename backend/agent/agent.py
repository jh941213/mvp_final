import asyncio
import os
import sys
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential
from autogen_ext.tools.azure import AzureAISearchTool

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from app.core.config import get_openai_config, get_azure_search_config


class KTDSAgent:
    def __init__(self):
        """KT DS 전문 AI 에이전트 초기화"""
        self.search_tool = None
        self.model_client = None
        self.agent = None
        self._setup_tools()
        self._setup_model()
        self._setup_agent()
    
    def _setup_tools(self):
        """검색 도구 설정"""
        self.search_tool = AzureAISearchTool.create_hybrid_search(
            name="ktds_search",
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_CREDENTIAL")),
            
            vector_fields=["text_vector"],
            search_fields=["chunk", "title"],
            select_fields=["chunk", "title"],
            
            query_type="simple",
            top=3,
            
            embedding_provider="azure_openai",
            embedding_model="text-embedding-3-small",
            openai_endpoint=os.getenv("OPENAI_ENDPOINT"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            
            description="KT ds 의 전반적인 외부에서 검색가능한 정보들이 있는 tools 입니다."
        )
    
    def _setup_model(self):
        """모델 클라이언트 설정"""
        self.model_client = AzureOpenAIChatCompletionClient(
            model="gpt-4.1-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            api_version=os.getenv("OPENAI_API_VERSION")
        )
    
    def _setup_agent(self):
        """KT DS Agent 설정"""
        self.agent = AssistantAgent(
            name="ktds_agent",
            model_client=self.model_client,
            tools=[self.search_tool],
            reflect_on_tool_use=True,
            system_message="KT DS 전문 AI입니다. ktds_search로 정보를 검색한 후 한국어로 상세히 답변하세요."
        )
    
    async def ask(self, question: str) -> str:
        """질문에 대한 답변을 반환합니다"""
        result = await self.agent.run(task=question)
        return result.messages[-1].content
    
    def get_agent_info(self):
        """에이전트 정보 반환"""
        return {
            "name": self.agent.name if self.agent else None,
            "model": self.model_client.model if self.model_client else None,
            "tools": len(self.agent.tools) if self.agent else 0
        }

