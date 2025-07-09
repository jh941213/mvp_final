"""
KT 전문 고객 상담원 믿음 (MI:DM) 에이전트
Friendli AI의 Midm-2.0 모델 사용
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import ModelInfo
from tools.bulletin_tools import get_current_time
import os

def create_midm_agent() -> AssistantAgent:
    """KT 전문 고객 상담원 믿음 에이전트 생성 (Friendli AI Midm-2.0 사용)"""
    
    # Friendli AI Midm-2.0 모델 정보 정의
    midm_model_info = ModelInfo(
        vision=False,
        function_calling=True,
        json_output=True,
        max_tokens=4096,
        max_input_tokens=8192,
        family="midm"
    )
    
    # Friendli AI Midm-2.0 클라이언트 생성
    model_client = OpenAIChatCompletionClient(
        model=os.getenv("FRIENDLY_MODEL_NAME"),
        model_info=midm_model_info,
        api_key=os.getenv("FRIENDLI_API_KEY"),  # 환경변수 사용
        base_url=os.getenv("FRIENDLI_API_URL"),  # 환경변수 사용
    )
    
    # 믿음 에이전트 생성 (일시적으로 tool 제거)
    midm_agent = AssistantAgent(
        name="Midm_Agent",
        model_client=model_client,
        tools=[],  # 일시적으로 tool 제거
        description="KT 고객 상담 전문가 믿음 - 친근하고 전문적인 KT 서비스 안내 (Friendli AI Midm-2.0 기반)",
        system_message="""안녕하세요! KT 고객 상담 전문가 믿음입니다. 🌟

저는 Midm-2.0 모델 기반으로 KT 서비스에 대한 전문적이고 친근한 상담을 제공합니다.

**전문 분야:**
- 📱 모바일 요금제 상담 및 추천
- 🌐 인터넷/IPTV 서비스 안내  
- 📞 고객센터 연결 및 지원
- 💡 KT 신규 서비스 소개
- 🔧 기술 지원 및 문제 해결

**상담 방식:**
- 고객 맞춤형 친근한 톤
- 정확하고 신뢰할 수 있는 정보 제공
- 단계별 안내와 명확한 설명
- 적극적인 문제 해결 지원

언제든지 KT 서비스에 대해 궁금한 점이 있으시면 편하게 말씀해 주세요! 😊"""
    )
    
    return midm_agent