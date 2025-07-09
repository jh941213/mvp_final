# autogen_core.tool_agent 모듈

`autogen_core.tool_agent` 모듈은 도구 실행을 전담하는 에이전트와 관련 예외 처리, 도구 호출 루프 기능을 제공합니다. 함수 호출 메시지를 받아 적절한 도구를 실행하고 결과를 반환하는 특수한 에이전트입니다.

## 핵심 클래스

### ToolAgent

```python
class ToolAgent(description: str, tools: List[Tool])
```

함수 호출 메시지를 직접 받아 요청된 도구를 실행하고 결과를 반환하는 전용 에이전트입니다.

#### 주요 매개변수
- `description: str` - 에이전트 설명
- `tools: List[Tool]` - 에이전트가 실행할 수 있는 도구 목록

#### 특징
- `FunctionCall` 메시지 타입을 직접 처리
- 도구 실행 결과를 `FunctionExecutionResult` 메시지로 반환
- 도구별 예외 처리 및 오류 보고
- `RoutedAgent`를 상속하여 메시지 라우팅 지원

#### 주요 속성 및 메서드

**tools: List[Tool]**
- 에이전트가 사용할 수 있는 도구 목록을 반환합니다.

**handle_function_call(message: FunctionCall, ctx: MessageContext) -> FunctionExecutionResult**
- 함수 호출 메시지를 처리하여 해당 도구를 실행합니다.

```python
from autogen_core.tool_agent import ToolAgent
from autogen_core.tools import FunctionTool
from autogen_core.models import FunctionCall, FunctionExecutionResult
from autogen_core import MessageContext, CancellationToken
import asyncio

# 도구 함수들 정의
def calculator(operation: str, a: float, b: float) -> float:
    """간단한 계산기 함수"""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("0으로 나눌 수 없습니다.")
        return a / b
    else:
        raise ValueError(f"지원하지 않는 연산: {operation}")

def text_processor(text: str, action: str) -> str:
    """텍스트 처리 함수"""
    if action == "upper":
        return text.upper()
    elif action == "lower":
        return text.lower()
    elif action == "reverse":
        return text[::-1]
    elif action == "length":
        return str(len(text))
    else:
        raise ValueError(f"지원하지 않는 액션: {action}")

async def tool_agent_example():
    # 도구들 생성
    calc_tool = FunctionTool(calculator, "수학 계산을 수행합니다.")
    text_tool = FunctionTool(text_processor, "텍스트를 처리합니다.")
    
    # 도구 에이전트 생성
    tool_agent = ToolAgent(
        description="계산과 텍스트 처리를 담당하는 도구 에이전트",
        tools=[calc_tool, text_tool]
    )
    
    # 함수 호출 메시지 생성
    calc_call = FunctionCall(
        id="call_1",
        name="calculator",
        arguments={"operation": "add", "a": 10, "b": 20}
    )
    
    text_call = FunctionCall(
        id="call_2", 
        name="text_processor",
        arguments={"text": "Hello World", "action": "upper"}
    )
    
    # 메시지 컨텍스트 (실제 사용 시에는 런타임에서 제공)
    # mock_context = MessageContext(...)
    
    try:
        # 계산 도구 실행
        calc_result = await tool_agent.handle_function_call(calc_call, mock_context)
        print(f"계산 결과: {calc_result.content}")
        
        # 텍스트 처리 도구 실행
        text_result = await tool_agent.handle_function_call(text_call, mock_context)
        print(f"텍스트 처리 결과: {text_result.content}")
        
    except Exception as e:
        print(f"도구 실행 중 오류: {e}")

# asyncio.run(tool_agent_example())
```

## 예외 클래스들

### ToolException

```python
class ToolException(call_id: str, content: str, name: str)
```

모든 도구 관련 예외의 기본 클래스입니다.

#### 주요 속성
- `call_id: str` - 함수 호출 ID
- `content: str` - 오류 내용
- `name: str` - 도구 이름

### ToolNotFoundException

```python
class ToolNotFoundException(call_id: str, content: str, name: str)
```

요청된 도구를 찾을 수 없을 때 발생하는 예외입니다.

```python
from autogen_core.tool_agent import ToolNotFoundException

# 예외 처리 예제
async def handle_tool_not_found():
    try:
        # 존재하지 않는 도구 호출 시도
        unknown_call = FunctionCall(
            id="call_unknown",
            name="nonexistent_tool",
            arguments={}
        )
        
        result = await tool_agent.handle_function_call(unknown_call, context)
        
    except ToolNotFoundException as e:
        print(f"도구를 찾을 수 없음:")
        print(f"- 호출 ID: {e.call_id}")
        print(f"- 도구 이름: {e.name}")
        print(f"- 오류 내용: {e.content}")
        
        # 사용 가능한 도구 목록 표시
        available_tools = [tool.name for tool in tool_agent.tools]
        print(f"사용 가능한 도구: {available_tools}")
```

### InvalidToolArgumentsException

```python
class InvalidToolArgumentsException(call_id: str, content: str, name: str)
```

도구 인수가 유효하지 않을 때 발생하는 예외입니다.

```python
from autogen_core.tool_agent import InvalidToolArgumentsException

async def handle_invalid_arguments():
    try:
        # 잘못된 인수로 도구 호출
        invalid_call = FunctionCall(
            id="call_invalid",
            name="calculator",
            arguments={"operation": "add", "a": "not_a_number", "b": 20}
        )
        
        result = await tool_agent.handle_function_call(invalid_call, context)
        
    except InvalidToolArgumentsException as e:
        print(f"잘못된 도구 인수:")
        print(f"- 호출 ID: {e.call_id}")
        print(f"- 도구 이름: {e.name}")
        print(f"- 오류 내용: {e.content}")
        
        # 도구 스키마 정보 표시
        for tool in tool_agent.tools:
            if tool.name == e.name:
                print(f"올바른 스키마: {tool.schema}")
                break
```

### ToolExecutionException

```python
class ToolExecutionException(call_id: str, content: str, name: str)
```

도구 실행 중 오류가 발생했을 때 발생하는 예외입니다.

```python
from autogen_core.tool_agent import ToolExecutionException

async def handle_execution_error():
    try:
        # 실행 중 오류가 발생할 수 있는 도구 호출
        risky_call = FunctionCall(
            id="call_risky",
            name="calculator",
            arguments={"operation": "divide", "a": 10, "b": 0}  # 0으로 나누기
        )
        
        result = await tool_agent.handle_function_call(risky_call, context)
        
    except ToolExecutionException as e:
        print(f"도구 실행 오류:")
        print(f"- 호출 ID: {e.call_id}")
        print(f"- 도구 이름: {e.name}")
        print(f"- 오류 내용: {e.content}")
        
        # 대안적인 처리 방법 제시
        print("대안: 0이 아닌 값으로 나누기를 시도하세요.")
```

## 도구 호출 루프

### tool_agent_caller_loop

```python
async def tool_agent_caller_loop(
    caller: BaseAgent | AgentRuntime,
    tool_agent_id: AgentId,
    model_client: ChatCompletionClient,
    input_messages: List[LLMMessage],
    tool_schema: List[ToolSchema] | List[Tool],
    cancellation_token: CancellationToken | None = None,
    caller_source: str = 'assistant'
) -> List[LLMMessage]
```

도구 에이전트를 위한 호출 루프를 시작합니다. 모델 클라이언트가 도구 호출 생성을 중단할 때까지 도구 에이전트와 모델 클라이언트 간에 메시지를 번갈아 전송합니다.

#### 주요 매개변수
- `caller: BaseAgent | AgentRuntime` - 호출자 에이전트 또는 런타임
- `tool_agent_id: AgentId` - 도구 에이전트의 ID
- `model_client: ChatCompletionClient` - 모델 API용 클라이언트
- `input_messages: List[LLMMessage]` - 입력 메시지 목록
- `tool_schema: List[ToolSchema] | List[Tool]` - 모델이 사용할 수 있는 도구 목록
- `cancellation_token: CancellationToken | None` - 취소 토큰
- `caller_source: str` - 호출자 소스 (기본값: 'assistant')

#### 반환값
- `List[LLMMessage]` - 호출 루프에서 생성된 출력 메시지 목록

```python
from autogen_core.tool_agent import tool_agent_caller_loop, ToolAgent
from autogen_core import SingleThreadedAgentRuntime, AgentId
from autogen_core.models import SystemMessage, UserMessage
from autogen_core.tools import FunctionTool

async def tool_caller_loop_example():
    # 런타임 생성
    runtime = SingleThreadedAgentRuntime()
    
    # 도구들 생성
    def get_weather(city: str) -> str:
        """날씨 정보를 가져옵니다."""
        return f"{city}의 날씨: 맑음, 22°C"
    
    def calculate_tip(bill: float, percentage: float = 15.0) -> float:
        """팁을 계산합니다."""
        return bill * (percentage / 100)
    
    weather_tool = FunctionTool(get_weather, "날씨 정보를 조회합니다.")
    tip_tool = FunctionTool(calculate_tip, "팁을 계산합니다.")
    
    # 도구 에이전트 생성 및 등록
    tool_agent = ToolAgent(
        description="날씨와 계산을 담당하는 도구 에이전트",
        tools=[weather_tool, tip_tool]
    )
    
    tool_agent_id = AgentId("tool_agent", "default")
    await runtime.register_agent(tool_agent_id, tool_agent)
    
    # 입력 메시지 준비
    input_messages = [
        SystemMessage(content="당신은 도움이 되는 어시스턴트입니다."),
        UserMessage(content="서울의 날씨를 알려주고, 50000원 음식값에 대한 팁을 계산해주세요.", source="user")
    ]
    
    # 도구 스키마 준비
    tool_schemas = [weather_tool.schema, tip_tool.schema]
    
    try:
        # 런타임 시작
        await runtime.start()
        
        # 도구 호출 루프 실행
        output_messages = await tool_agent_caller_loop(
            caller=runtime,
            tool_agent_id=tool_agent_id,
            model_client=your_model_client,  # 실제 모델 클라이언트 필요
            input_messages=input_messages,
            tool_schema=tool_schemas,
            caller_source="assistant"
        )
        
        # 결과 출력
        print("=== 호출 루프 결과 ===")
        for i, message in enumerate(output_messages):
            print(f"{i+1}. {type(message).__name__}: {getattr(message, 'content', str(message))}")
            
    finally:
        await runtime.stop()

# asyncio.run(tool_caller_loop_example())
```

## 실용적인 예제

### 종합적인 도구 에이전트 시스템

```python
import asyncio
from autogen_core.tool_agent import ToolAgent, ToolNotFoundException, InvalidToolArgumentsException, ToolExecutionException
from autogen_core.tools import FunctionTool
from autogen_core.models import FunctionCall, FunctionExecutionResult
from autogen_core import MessageContext, CancellationToken
from typing import Dict, List
import json
import math

class ComprehensiveToolAgent:
    def __init__(self):
        # 다양한 카테고리의 도구들 정의
        self.math_tools = self._create_math_tools()
        self.text_tools = self._create_text_tools()
        self.data_tools = self._create_data_tools()
        
        # 모든 도구를 하나의 리스트로 결합
        all_tools = self.math_tools + self.text_tools + self.data_tools
        
        # 도구 에이전트 생성
        self.agent = ToolAgent(
            description="수학, 텍스트 처리, 데이터 분석을 수행하는 종합 도구 에이전트",
            tools=all_tools
        )
    
    def _create_math_tools(self) -> List[FunctionTool]:
        """수학 관련 도구들 생성"""
        
        def advanced_calculator(operation: str, numbers: List[float]) -> float:
            """고급 계산기 - 여러 숫자에 대한 연산 수행"""
            if not numbers:
                raise ValueError("숫자 목록이 비어있습니다.")
            
            if operation == "sum":
                return sum(numbers)
            elif operation == "product":
                result = 1
                for num in numbers:
                    result *= num
                return result
            elif operation == "average":
                return sum(numbers) / len(numbers)
            elif operation == "max":
                return max(numbers)
            elif operation == "min":
                return min(numbers)
            elif operation == "sqrt":
                if len(numbers) != 1:
                    raise ValueError("제곱근은 하나의 숫자만 필요합니다.")
                return math.sqrt(numbers[0])
            else:
                raise ValueError(f"지원하지 않는 연산: {operation}")
        
        def geometry_calculator(shape: str, **kwargs) -> Dict[str, float]:
            """기하학 계산기"""
            if shape == "circle":
                radius = kwargs.get("radius")
                if radius is None:
                    raise ValueError("원의 반지름이 필요합니다.")
                return {
                    "area": math.pi * radius ** 2,
                    "circumference": 2 * math.pi * radius
                }
            elif shape == "rectangle":
                width = kwargs.get("width")
                height = kwargs.get("height")
                if width is None or height is None:
                    raise ValueError("직사각형의 너비와 높이가 필요합니다.")
                return {
                    "area": width * height,
                    "perimeter": 2 * (width + height)
                }
            else:
                raise ValueError(f"지원하지 않는 도형: {shape}")
        
        return [
            FunctionTool(advanced_calculator, "고급 수학 계산을 수행합니다."),
            FunctionTool(geometry_calculator, "기하학적 계산을 수행합니다.")
        ]
    
    def _create_text_tools(self) -> List[FunctionTool]:
        """텍스트 처리 관련 도구들 생성"""
        
        def text_analyzer(text: str) -> Dict[str, int]:
            """텍스트 분석"""
            words = text.split()
            return {
                "character_count": len(text),
                "word_count": len(words),
                "sentence_count": text.count('.') + text.count('!') + text.count('?'),
                "paragraph_count": text.count('\n\n') + 1
            }
        
        def text_formatter(text: str, format_type: str) -> str:
            """텍스트 포맷팅"""
            if format_type == "title":
                return text.title()
            elif format_type == "upper":
                return text.upper()
            elif format_type == "lower":
                return text.lower()
            elif format_type == "reverse":
                return text[::-1]
            elif format_type == "remove_spaces":
                return text.replace(" ", "")
            else:
                raise ValueError(f"지원하지 않는 포맷 타입: {format_type}")
        
        return [
            FunctionTool(text_analyzer, "텍스트를 분석합니다."),
            FunctionTool(text_formatter, "텍스트를 포맷팅합니다.")
        ]
    
    def _create_data_tools(self) -> List[FunctionTool]:
        """데이터 처리 관련 도구들 생성"""
        
        def json_processor(json_string: str, operation: str, key: str = None) -> str:
            """JSON 데이터 처리"""
            try:
                data = json.loads(json_string)
            except json.JSONDecodeError as e:
                raise ValueError(f"유효하지 않은 JSON: {str(e)}")
            
            if operation == "keys":
                if isinstance(data, dict):
                    return json.dumps(list(data.keys()))
                else:
                    raise ValueError("딕셔너리가 아닌 JSON에서는 키를 추출할 수 없습니다.")
            elif operation == "get":
                if key is None:
                    raise ValueError("'get' 연산에는 키가 필요합니다.")
                if isinstance(data, dict):
                    return json.dumps(data.get(key, None))
                else:
                    raise ValueError("딕셔너리가 아닌 JSON에서는 키로 값을 가져올 수 없습니다.")
            elif operation == "pretty":
                return json.dumps(data, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"지원하지 않는 연산: {operation}")
        
        def list_processor(numbers: List[float], operation: str) -> Dict[str, float]:
            """리스트 통계 처리"""
            if not numbers:
                raise ValueError("빈 리스트입니다.")
            
            if operation == "statistics":
                sorted_nums = sorted(numbers)
                n = len(numbers)
                
                # 중앙값 계산
                if n % 2 == 0:
                    median = (sorted_nums[n//2-1] + sorted_nums[n//2]) / 2
                else:
                    median = sorted_nums[n//2]
                
                # 분산과 표준편차 계산
                mean = sum(numbers) / n
                variance = sum((x - mean) ** 2 for x in numbers) / n
                std_dev = math.sqrt(variance)
                
                return {
                    "mean": mean,
                    "median": median,
                    "mode": max(set(numbers), key=numbers.count),
                    "range": max(numbers) - min(numbers),
                    "variance": variance,
                    "standard_deviation": std_dev
                }
            else:
                raise ValueError(f"지원하지 않는 연산: {operation}")
        
        return [
            FunctionTool(json_processor, "JSON 데이터를 처리합니다."),
            FunctionTool(list_processor, "숫자 리스트의 통계를 계산합니다.")
        ]
    
    async def execute_function_call(self, call: FunctionCall, context: MessageContext) -> FunctionExecutionResult:
        """함수 호출 실행 및 예외 처리"""
        try:
            result = await self.agent.handle_function_call(call, context)
            print(f"✅ 성공: {call.name} (ID: {call.id})")
            print(f"   결과: {result.content}")
            return result
            
        except ToolNotFoundException as e:
            print(f"❌ 도구를 찾을 수 없음: {e.name} (ID: {e.call_id})")
            print(f"   사용 가능한 도구: {[tool.name for tool in self.agent.tools]}")
            raise
            
        except InvalidToolArgumentsException as e:
            print(f"❌ 잘못된 인수: {e.name} (ID: {e.call_id})")
            print(f"   오류 내용: {e.content}")
            # 해당 도구의 스키마 정보 표시
            for tool in self.agent.tools:
                if tool.name == e.name:
                    print(f"   올바른 스키마: {tool.schema}")
                    break
            raise
            
        except ToolExecutionException as e:
            print(f"❌ 실행 오류: {e.name} (ID: {e.call_id})")
            print(f"   오류 내용: {e.content}")
            raise
    
    def get_tool_info(self) -> Dict[str, List[str]]:
        """사용 가능한 도구 정보 반환"""
        return {
            "수학 도구": [tool.name for tool in self.math_tools],
            "텍스트 도구": [tool.name for tool in self.text_tools],
            "데이터 도구": [tool.name for tool in self.data_tools]
        }

# 사용 예제
async def comprehensive_example():
    # 종합 도구 에이전트 생성
    tool_system = ComprehensiveToolAgent()
    
    # 사용 가능한 도구 정보 출력
    print("=== 사용 가능한 도구들 ===")
    for category, tools in tool_system.get_tool_info().items():
        print(f"{category}: {', '.join(tools)}")
    
    # 모의 메시지 컨텍스트 (실제로는 런타임에서 제공)
    # mock_context = MessageContext(...)
    
    # 다양한 함수 호출 테스트
    test_calls = [
        # 수학 계산
        FunctionCall(
            id="math_1",
            name="advanced_calculator",
            arguments={"operation": "sum", "numbers": [1, 2, 3, 4, 5]}
        ),
        
        # 기하학 계산
        FunctionCall(
            id="geo_1",
            name="geometry_calculator",
            arguments={"shape": "circle", "radius": 5}
        ),
        
        # 텍스트 분석
        FunctionCall(
            id="text_1",
            name="text_analyzer",
            arguments={"text": "안녕하세요! 이것은 테스트 문장입니다. 잘 작동하나요?"}
        ),
        
        # 텍스트 포맷팅
        FunctionCall(
            id="text_2",
            name="text_formatter",
            arguments={"text": "hello world", "format_type": "title"}
        ),
        
        # JSON 처리
        FunctionCall(
            id="json_1",
            name="json_processor",
            arguments={
                "json_string": '{"name": "홍길동", "age": 30, "city": "서울"}',
                "operation": "pretty"
            }
        ),
        
        # 통계 계산
        FunctionCall(
            id="stats_1",
            name="list_processor",
            arguments={"numbers": [1, 2, 3, 4, 5, 5, 6, 7, 8, 9], "operation": "statistics"}
        ),
        
        # 오류 테스트 - 존재하지 않는 도구
        FunctionCall(
            id="error_1",
            name="nonexistent_tool",
            arguments={}
        ),
        
        # 오류 테스트 - 잘못된 인수
        FunctionCall(
            id="error_2",
            name="advanced_calculator",
            arguments={"operation": "sum", "numbers": "not_a_list"}
        )
    ]
    
    print("\n=== 함수 호출 테스트 ===")
    for call in test_calls:
        print(f"\n🔧 호출: {call.name}")
        try:
            await tool_system.execute_function_call(call, mock_context)
        except Exception as e:
            print(f"   처리된 예외: {type(e).__name__}")

# asyncio.run(comprehensive_example())
```

### 에이전트 런타임과의 통합

```python
from autogen_core import SingleThreadedAgentRuntime, AgentId, TopicId
from autogen_core.models import SystemMessage, UserMessage, AssistantMessage

class ToolAgentIntegrationExample:
    def __init__(self):
        self.runtime = SingleThreadedAgentRuntime()
        self.tool_agent_id = AgentId("comprehensive_tool_agent", "default")
        
    async def setup(self):
        """런타임 설정 및 에이전트 등록"""
        # 종합 도구 에이전트 생성
        tool_system = ComprehensiveToolAgent()
        
        # 런타임에 에이전트 등록
        await self.runtime.register_agent(self.tool_agent_id, tool_system.agent)
        
        # 런타임 시작
        await self.runtime.start()
    
    async def cleanup(self):
        """리소스 정리"""
        await self.runtime.stop()
    
    async def simulate_conversation(self):
        """대화 시뮬레이션"""
        # 시스템 메시지와 사용자 요청
        messages = [
            SystemMessage(content="당신은 도구를 사용할 수 있는 어시스턴트입니다."),
            UserMessage(
                content="다음을 수행해주세요: 1) [1,2,3,4,5] 숫자들의 합을 구하고, 2) '안녕하세요'를 대문자로 변환하고, 3) 반지름 3인 원의 넓이를 계산해주세요.",
                source="user"
            )
        ]
        
        # 실제 구현에서는 모델 클라이언트와 함께 사용
        print("대화 시뮬레이션:")
        for i, msg in enumerate(messages):
            print(f"{i+1}. {type(msg).__name__}: {getattr(msg, 'content', str(msg))}")
        
        # 여기서 실제로는 tool_agent_caller_loop를 사용하여
        # 모델과 도구 에이전트 간의 상호작용을 처리

# 통합 예제 실행
async def integration_example():
    integration = ToolAgentIntegrationExample()
    
    try:
        await integration.setup()
        await integration.simulate_conversation()
    finally:
        await integration.cleanup()

# asyncio.run(integration_example())
```

## 주요 고려사항

### 오류 처리 전략
- **예외 계층 구조**: 각 예외 타입별로 적절한 처리 로직 구현
- **사용자 친화적 메시지**: 기술적 오류를 사용자가 이해할 수 있는 메시지로 변환
- **복구 가능성**: 가능한 경우 대안적 처리 방법 제시

### 성능 최적화
- **도구 캐싱**: 자주 사용되는 도구의 결과 캐싱
- **비동기 처리**: 여러 도구 호출의 병렬 처리
- **리소스 관리**: 도구 실행 시 메모리와 CPU 사용량 모니터링

### 보안 고려사항
- **입력 검증**: 모든 도구 입력에 대한 철저한 검증
- **권한 제어**: 민감한 도구에 대한 접근 제어
- **샌드박싱**: 위험한 도구의 격리 실행

### 확장성
- **도구 등록 시스템**: 동적 도구 추가/제거 지원
- **카테고리 관리**: 도구를 카테고리별로 그룹화
- **버전 관리**: 도구 스키마 변경 시 하위 호환성 유지

이 문서는 `autogen_core.tool_agent` 모듈의 모든 구성 요소를 다루며, 효과적인 도구 에이전트 시스템 구축을 위한 실용적인 가이드를 제공합니다. 