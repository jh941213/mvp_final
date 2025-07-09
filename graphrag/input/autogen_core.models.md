# autogen_core.models 모듈

`autogen_core.models` 모듈은 언어 모델과의 상호작용을 위한 메시지 타입, 클라이언트 인터페이스, 그리고 모델 정보 관리 기능을 제공합니다.

## 메시지 타입

### SystemMessage

```python
class SystemMessage(BaseModel)
```

개발자가 모델에게 제공하는 시스템 지시사항을 포함하는 메시지입니다.

#### 주요 필드
- `content: str` - 메시지 내용
- `type: Literal['SystemMessage']` - 메시지 타입

```python
# 예제
system_msg = SystemMessage(
    content="당신은 도움이 되는 AI 어시스턴트입니다. 항상 정중하고 정확한 답변을 제공하세요."
)
```

> **참고**: OpenAI는 'system' 역할에서 'developer' 역할로 전환하고 있지만, 'system' 역할은 여전히 지원되며 서버 측에서 자동으로 'developer' 역할로 변환됩니다.

### UserMessage

```python
class UserMessage(BaseModel)
```

최종 사용자의 입력 또는 모델에 제공되는 데이터를 포함하는 메시지입니다.

#### 주요 필드
- `content: str | List[str | Image]` - 메시지 내용 (텍스트 또는 텍스트와 이미지의 조합)
- `source: str` - 메시지를 보낸 에이전트의 이름
- `type: Literal['UserMessage']` - 메시지 타입

```python
# 텍스트만 포함하는 예제
user_msg = UserMessage(
    content="파이썬에서 리스트를 정렬하는 방법을 알려주세요.",
    source="user_agent"
)

# 텍스트와 이미지를 포함하는 예제
from autogen_core import Image
user_msg_with_image = UserMessage(
    content=[
        "이 이미지에서 무엇을 볼 수 있나요?",
        Image.from_file("image.jpg")
    ],
    source="user_agent"
)
```

### AssistantMessage

```python
class AssistantMessage(BaseModel)
```

언어 모델에서 생성된 어시스턴트 메시지입니다.

#### 주요 필드
- `content: str | List[FunctionCall]` - 메시지 내용 (텍스트 또는 함수 호출 목록)
- `source: str` - 메시지를 보낸 에이전트의 이름
- `thought: str | None` - 추론 텍스트 (추론 모델에서 사용)
- `type: Literal['AssistantMessage']` - 메시지 타입

```python
# 텍스트 응답 예제
assistant_msg = AssistantMessage(
    content="파이썬에서 리스트를 정렬하려면 sort() 메서드나 sorted() 함수를 사용할 수 있습니다.",
    source="assistant_agent"
)

# 함수 호출 예제
from autogen_core import FunctionCall
assistant_msg_with_calls = AssistantMessage(
    content=[
        FunctionCall(
            id="call_1",
            name="calculate",
            arguments='{"operation": "add", "a": 10, "b": 20}'
        )
    ],
    source="assistant_agent"
)
```

### FunctionExecutionResultMessage

```python
class FunctionExecutionResultMessage(BaseModel)
```

여러 함수 호출의 실행 결과를 포함하는 메시지입니다.

#### 주요 필드
- `content: List[FunctionExecutionResult]` - 함수 실행 결과 목록
- `type: Literal['FunctionExecutionResultMessage']` - 메시지 타입

```python
# 예제
result_msg = FunctionExecutionResultMessage(
    content=[
        FunctionExecutionResult(
            call_id="call_1",
            name="calculate",
            content="30",
            is_error=False
        )
    ]
)
```

## 함수 실행 관련 클래스

### FunctionExecutionResult

```python
class FunctionExecutionResult(BaseModel)
```

함수 호출의 실행 결과를 포함합니다.

#### 주요 필드
- `call_id: str` - 함수 호출 ID
- `name: str` - 호출된 함수의 이름 (v0.4.8에서 추가)
- `content: str` - 함수 호출의 출력
- `is_error: bool | None` - 함수 호출이 오류를 발생시켰는지 여부

```python
# 성공적인 함수 실행 결과
success_result = FunctionExecutionResult(
    call_id="call_1",
    name="get_weather",
    content='{"temperature": 22, "condition": "sunny"}',
    is_error=False
)

# 오류가 발생한 함수 실행 결과
error_result = FunctionExecutionResult(
    call_id="call_2",
    name="invalid_function",
    content="Function not found",
    is_error=True
)
```

## 모델 클라이언트

### ChatCompletionClient

```python
class ChatCompletionClient(ComponentBase[BaseModel], ABC)
```

채팅 완성을 위한 추상 기본 클래스입니다. 모든 언어 모델 클라이언트가 구현해야 하는 인터페이스를 정의합니다.

#### 주요 속성
- `capabilities: ModelCapabilities` - 모델의 기능
- `model_info: ModelInfo` - 모델 정보

#### 주요 메서드

**create(messages, *, tools=[], tool_choice='auto', json_output=None, extra_create_args={}, cancellation_token=None)**
- 모델에서 단일 응답을 생성합니다.

**매개변수:**
- `messages` - 모델에 보낼 메시지 시퀀스
- `tools` - 모델과 함께 사용할 도구들
- `tool_choice` - 도구 선택 방식 ('auto', 'required', 'none' 또는 특정 Tool 객체)
- `json_output` - JSON 모드 또는 구조화된 출력 사용 여부
- `extra_create_args` - 기본 클라이언트에 전달할 추가 인수
- `cancellation_token` - 취소 토큰

**반환값:** `CreateResult` - 모델 호출 결과

```python
# 기본 사용법
async def example_usage(client: ChatCompletionClient):
    messages = [
        SystemMessage(content="당신은 도움이 되는 어시스턴트입니다."),
        UserMessage(content="안녕하세요!", source="user")
    ]
    
    result = await client.create(messages)
    print(f"응답: {result.content}")
    print(f"토큰 사용량: {result.usage}")
```

**create_stream(messages, *, tools=[], tool_choice='auto', json_output=None, extra_create_args={}, cancellation_token=None)**
- 모델에서 스트리밍 응답을 생성합니다.

**반환값:** `AsyncGenerator[str | CreateResult, None]` - 문자열 청크를 생성하고 CreateResult로 끝나는 제너레이터

```python
# 스트리밍 사용법
async def streaming_example(client: ChatCompletionClient):
    messages = [UserMessage(content="긴 이야기를 들려주세요.", source="user")]
    
    async for chunk in client.create_stream(messages):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)
        else:  # CreateResult
            print(f"\n완료: {chunk.finish_reason}")
```

**count_tokens(messages, *, tools=[]) / remaining_tokens(messages, *, tools=[])**
- 메시지의 토큰 수를 계산하거나 남은 토큰 수를 반환합니다.

**actual_usage() / total_usage()**
- 실제 사용량과 총 사용량을 반환합니다.

## 모델 정보 및 기능

### ModelInfo

```python
class ModelInfo(TypedDict)
```

모델의 속성 정보를 포함하는 딕셔너리입니다.

#### 주요 필드
- `family: ModelFamily | str` - 모델 패밀리
- `function_calling: bool` - 함수 호출 지원 여부
- `json_output: bool` - JSON 출력 지원 여부
- `structured_output: bool` - 구조화된 출력 지원 여부
- `vision: bool` - 비전(이미지 입력) 지원 여부
- `multiple_system_messages: bool | None` - 다중 시스템 메시지 지원 여부

```python
# 예제
model_info: ModelInfo = {
    "family": ModelFamily.GPT_4O,
    "function_calling": True,
    "json_output": True,
    "structured_output": True,
    "vision": True,
    "multiple_system_messages": True
}
```

### ModelFamily

```python
class ModelFamily()
```

모델 패밀리를 나타내는 상수들을 포함하는 네임스페이스 클래스입니다.

#### 주요 상수들

**OpenAI 모델들**
- `GPT_35 = 'gpt-35'`
- `GPT_4 = 'gpt-4'`
- `GPT_41 = 'gpt-41'`
- `GPT_45 = 'gpt-45'`
- `GPT_4O = 'gpt-4o'`
- `O1 = 'o1'`
- `O3 = 'o3'`
- `O4 = 'o4'`
- `R1 = 'r1'`

**Google 모델들**
- `GEMINI_1_5_FLASH = 'gemini-1.5-flash'`
- `GEMINI_1_5_PRO = 'gemini-1.5-pro'`
- `GEMINI_2_0_FLASH = 'gemini-2.0-flash'`
- `GEMINI_2_5_PRO = 'gemini-2.5-pro'`
- `GEMINI_2_5_FLASH = 'gemini-2.5-flash'`

**Anthropic 모델들**
- `CLAUDE_3_HAIKU = 'claude-3-haiku'`
- `CLAUDE_3_SONNET = 'claude-3-sonnet'`
- `CLAUDE_3_OPUS = 'claude-3-opus'`
- `CLAUDE_3_5_HAIKU = 'claude-3-5-haiku'`
- `CLAUDE_3_5_SONNET = 'claude-3-5-sonnet'`
- `CLAUDE_3_7_SONNET = 'claude-3-7-sonnet'`
- `CLAUDE_4_OPUS = 'claude-4-opus'`
- `CLAUDE_4_SONNET = 'claude-4-sonnet'`

**Meta 모델들**
- `LLAMA_3_3_8B = 'llama-3.3-8b'`
- `LLAMA_3_3_70B = 'llama-3.3-70b'`
- `LLAMA_4_SCOUT = 'llama-4-scout'`
- `LLAMA_4_MAVERICK = 'llama-4-maverick'`

**Mistral 모델들**
- `MISTRAL = 'mistral'`
- `MINISTRAL = 'ministral'`
- `CODESRAL = 'codestral'`
- `OPEN_CODESRAL_MAMBA = 'open-codestral-mamba'`
- `PIXTRAL = 'pixtral'`

#### 유틸리티 메서드들

```python
# 모델 패밀리 확인 메서드들
ModelFamily.is_openai(family)    # OpenAI 모델인지 확인
ModelFamily.is_claude(family)    # Claude 모델인지 확인
ModelFamily.is_gemini(family)    # Gemini 모델인지 확인
ModelFamily.is_llama(family)     # Llama 모델인지 확인
ModelFamily.is_mistral(family)   # Mistral 모델인지 확인

# 예제
if ModelFamily.is_openai(model_info["family"]):
    print("OpenAI 모델을 사용 중입니다.")
```

### ModelCapabilities

```python
class ModelCapabilities(TypedDict)
```

모델의 기능을 나타내는 타입 정의입니다.

#### 필드
- `function_calling: bool` - 함수 호출 지원
- `json_output: bool` - JSON 출력 지원
- `vision: bool` - 비전 지원

## 결과 및 사용량 클래스

### CreateResult

```python
class CreateResult(BaseModel)
```

모델 완성의 출력을 포함하는 결과 클래스입니다.

#### 주요 필드
- `content: str | List[FunctionCall]` - 모델 완성 출력
- `finish_reason: Literal['stop', 'length', 'function_calls', 'content_filter', 'unknown']` - 완성 종료 이유
- `usage: RequestUsage` - 프롬프트와 완성에서 사용된 토큰 사용량
- `cached: bool` - 캐시된 응답에서 생성되었는지 여부
- `thought: str | None` - 추론 텍스트 (추론 모델용)
- `logprobs: List[ChatCompletionTokenLogprob] | None` - 완성에서 토큰의 로그 확률

```python
# 결과 처리 예제
async def process_result(client: ChatCompletionClient):
    messages = [UserMessage(content="2+2는 얼마인가요?", source="user")]
    result = await client.create(messages)
    
    print(f"응답: {result.content}")
    print(f"종료 이유: {result.finish_reason}")
    print(f"사용된 토큰: {result.usage.prompt_tokens + result.usage.completion_tokens}")
    print(f"캐시됨: {result.cached}")
    
    if result.thought:
        print(f"추론 과정: {result.thought}")
```

### RequestUsage

```python
class RequestUsage()
```

토큰 사용량을 나타내는 클래스입니다.

#### 필드
- `prompt_tokens: int` - 프롬프트에 사용된 토큰 수
- `completion_tokens: int` - 완성에 사용된 토큰 수

```python
# 사용량 계산 예제
def calculate_cost(usage: RequestUsage, prompt_price_per_1k: float, completion_price_per_1k: float):
    prompt_cost = (usage.prompt_tokens / 1000) * prompt_price_per_1k
    completion_cost = (usage.completion_tokens / 1000) * completion_price_per_1k
    return prompt_cost + completion_cost
```

## 로그 확률 클래스

### ChatCompletionTokenLogprob

```python
class ChatCompletionTokenLogprob(BaseModel)
```

완성에서 토큰의 로그 확률 정보를 포함합니다.

#### 주요 필드
- `token: str` - 토큰
- `logprob: float` - 로그 확률
- `bytes: List[int] | None` - 토큰의 바이트 표현
- `top_logprobs: List[TopLogprob] | None` - 상위 로그 확률들

### TopLogprob

```python
class TopLogprob()
```

상위 로그 확률 정보를 포함합니다.

#### 필드
- `logprob: float` - 로그 확률
- `bytes: List[int] | None` - 바이트 표현

## 실용적인 예제

### 기본 대화 시스템

```python
import asyncio
from autogen_core.models import (
    SystemMessage, UserMessage, AssistantMessage,
    ChatCompletionClient, CreateResult
)

async def chat_example(client: ChatCompletionClient):
    # 대화 기록
    conversation = [
        SystemMessage(content="당신은 친근한 AI 어시스턴트입니다."),
        UserMessage(content="안녕하세요! 오늘 날씨가 어떤가요?", source="user")
    ]
    
    # 응답 생성
    result = await client.create(conversation)
    
    # 어시스턴트 응답을 대화에 추가
    conversation.append(AssistantMessage(
        content=result.content,
        source="assistant"
    ))
    
    print(f"어시스턴트: {result.content}")
    return conversation
```

### 함수 호출 시스템

```python
from autogen_core import Tool, ToolSchema

async def function_calling_example(client: ChatCompletionClient):
    # 도구 정의
    weather_tool = ToolSchema(
        name="get_weather",
        description="특정 위치의 현재 날씨를 가져옵니다",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "도시 이름"
                }
            },
            "required": ["location"]
        }
    )
    
    messages = [
        SystemMessage(content="날씨 정보를 제공하는 어시스턴트입니다."),
        UserMessage(content="서울의 날씨를 알려주세요.", source="user")
    ]
    
    # 함수 호출이 필요한 응답 생성
    result = await client.create(
        messages, 
        tools=[weather_tool],
        tool_choice="auto"
    )
    
    if isinstance(result.content, list):  # 함수 호출
        for call in result.content:
            print(f"함수 호출: {call.name}({call.arguments})")
            
            # 실제 함수 실행 (여기서는 예시)
            weather_data = '{"temperature": 15, "condition": "흐림"}'
            
            # 함수 실행 결과를 대화에 추가
            messages.append(AssistantMessage(
                content=result.content,
                source="assistant"
            ))
            
            messages.append(FunctionExecutionResultMessage(
                content=[FunctionExecutionResult(
                    call_id=call.id,
                    name=call.name,
                    content=weather_data,
                    is_error=False
                )]
            ))
            
            # 최종 응답 생성
            final_result = await client.create(messages)
            print(f"최종 응답: {final_result.content}")
```

### 스트리밍 응답 처리

```python
async def streaming_example(client: ChatCompletionClient):
    messages = [
        SystemMessage(content="창의적인 스토리텔러입니다."),
        UserMessage(content="짧은 모험 이야기를 들려주세요.", source="user")
    ]
    
    print("스토리 생성 중...")
    full_response = ""
    
    async for chunk in client.create_stream(messages):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)
            full_response += chunk
        else:  # CreateResult
            print(f"\n\n[완료: {chunk.finish_reason}]")
            print(f"총 토큰: {chunk.usage.prompt_tokens + chunk.usage.completion_tokens}")
    
    return full_response
```

### JSON 및 구조화된 출력

```python
from pydantic import BaseModel

class WeatherResponse(BaseModel):
    location: str
    temperature: int
    condition: str
    humidity: int

async def structured_output_example(client: ChatCompletionClient):
    messages = [
        SystemMessage(content="날씨 데이터를 JSON 형식으로 제공합니다."),
        UserMessage(content="부산의 현재 날씨 정보를 알려주세요.", source="user")
    ]
    
    # 구조화된 출력 사용
    result = await client.create(
        messages,
        json_output=WeatherResponse  # Pydantic 모델 사용
    )
    
    # 응답을 구조화된 데이터로 파싱
    weather_data = WeatherResponse.model_validate_json(result.content)
    print(f"위치: {weather_data.location}")
    print(f"온도: {weather_data.temperature}°C")
    print(f"상태: {weather_data.condition}")
    print(f"습도: {weather_data.humidity}%")
```

### 토큰 사용량 모니터링

```python
async def token_monitoring_example(client: ChatCompletionClient):
    messages = [
        SystemMessage(content="도움이 되는 어시스턴트입니다."),
        UserMessage(content="인공지능의 역사에 대해 설명해주세요.", source="user")
    ]
    
    # 사용 전 토큰 수 확인
    token_count = await client.count_tokens(messages)
    remaining = await client.remaining_tokens(messages)
    
    print(f"입력 토큰 수: {token_count}")
    print(f"남은 토큰 수: {remaining}")
    
    # 응답 생성
    result = await client.create(messages)
    
    # 사용량 확인
    print(f"프롬프트 토큰: {result.usage.prompt_tokens}")
    print(f"완성 토큰: {result.usage.completion_tokens}")
    print(f"총 토큰: {result.usage.prompt_tokens + result.usage.completion_tokens}")
    
    # 누적 사용량 확인
    total_usage = await client.total_usage()
    print(f"총 누적 사용량: {total_usage.prompt_tokens + total_usage.completion_tokens}")
```

## 유틸리티 함수

### validate_model_info

```python
def validate_model_info(model_info: ModelInfo) -> None
```

모델 정보 딕셔너리의 유효성을 검사합니다.

```python
# 예제
try:
    model_info = {
        "family": ModelFamily.GPT_4O,
        "function_calling": True,
        "json_output": True,
        "structured_output": True,
        "vision": True
    }
    validate_model_info(model_info)
    print("모델 정보가 유효합니다.")
except ValueError as e:
    print(f"모델 정보 오류: {e}")
```

## 주요 고려사항

### 메시지 타입 선택
- **SystemMessage**: 모델의 동작을 지시할 때
- **UserMessage**: 사용자 입력이나 데이터를 전달할 때
- **AssistantMessage**: 모델의 응답을 나타낼 때
- **FunctionExecutionResultMessage**: 함수 호출 결과를 전달할 때

### 모델 기능 활용
- `model_info`와 `capabilities`를 확인하여 모델이 지원하는 기능 사용
- 함수 호출, JSON 출력, 비전 등의 기능을 적절히 활용
- 토큰 제한을 고려한 메시지 관리

### 성능 최적화
- 스트리밍을 사용하여 사용자 경험 향상
- 토큰 사용량 모니터링으로 비용 관리
- 캐싱 활용으로 응답 속도 개선

### 오류 처리
- 함수 호출 시 `is_error` 플래그 확인
- 취소 토큰을 사용한 요청 취소
- 모델별 제한사항과 오류 상황 고려

이 문서는 `autogen_core.models` 모듈의 모든 구성 요소를 다루며, 언어 모델과의 효과적인 상호작용을 위한 실용적인 가이드를 제공합니다. 