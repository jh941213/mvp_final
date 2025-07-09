# autogen_core.tools 모듈

`autogen_core.tools` 모듈은 에이전트가 사용할 수 있는 도구(Tool) 시스템과 도구들을 관리하는 워크벤치(Workbench) 기능을 제공합니다. 함수를 도구로 래핑하고, 스트리밍 도구, 상태 관리 등의 고급 기능을 지원합니다.

## 기본 도구 클래스

### Tool

```python
class Tool(*args, **kwargs)
```

모든 도구가 구현해야 하는 기본 프로토콜입니다.

#### 주요 속성 및 메서드
- `name: str` - 도구의 이름
- `description: str` - 도구의 설명
- `schema: ToolSchema` - 도구의 스키마 정보

**args_type() -> Type[BaseModel]**
- 도구의 인수 타입을 반환합니다.

**return_type() -> Type[Any]**
- 도구의 반환 타입을 반환합니다.

**run_json(args: Mapping[str, Any], cancellation_token: CancellationToken, call_id: str | None = None) -> Any**
- 딕셔너리 형태의 인수로 도구를 실행합니다.

**return_value_as_string(value: Any) -> str**
- 반환값을 문자열로 변환합니다.

**save_state_json() / load_state_json(state: Mapping[str, Any])**
- 도구의 상태를 저장하고 복원합니다.

### BaseTool

```python
class BaseTool(args_type: Type[ArgsT], return_type: Type[ReturnT], name: str, description: str, strict: bool = False)
```

도구 구현을 위한 추상 기본 클래스입니다.

#### 주요 매개변수
- `args_type: Type[ArgsT]` - 인수 타입
- `return_type: Type[ReturnT]` - 반환 타입
- `name: str` - 도구 이름
- `description: str` - 도구 설명
- `strict: bool` - 엄격 모드 (구조화된 출력 모드에서 필요)

#### 구현해야 할 메서드

**run(args: ArgsT, cancellation_token: CancellationToken) -> ReturnT**
- 도구의 핵심 실행 로직을 구현합니다.

```python
from pydantic import BaseModel
from autogen_core.tools import BaseTool
from autogen_core import CancellationToken

class CalculatorArgs(BaseModel):
    operation: str
    a: float
    b: float

class CalculatorResult(BaseModel):
    result: float

class CalculatorTool(BaseTool[CalculatorArgs, CalculatorResult]):
    def __init__(self):
        super().__init__(
            args_type=CalculatorArgs,
            return_type=CalculatorResult,
            name="calculator",
            description="간단한 수학 계산을 수행합니다."
        )
    
    async def run(self, args: CalculatorArgs, cancellation_token: CancellationToken) -> CalculatorResult:
        if args.operation == "add":
            result = args.a + args.b
        elif args.operation == "subtract":
            result = args.a - args.b
        elif args.operation == "multiply":
            result = args.a * args.b
        elif args.operation == "divide":
            if args.b == 0:
                raise ValueError("0으로 나눌 수 없습니다.")
            result = args.a / args.b
        else:
            raise ValueError(f"지원하지 않는 연산: {args.operation}")
        
        return CalculatorResult(result=result)

# 사용 예제
async def use_calculator():
    tool = CalculatorTool()
    cancellation_token = CancellationToken()
    
    result = await tool.run_json({
        "operation": "add",
        "a": 10,
        "b": 20
    }, cancellation_token)
    
    print(f"결과: {result}")  # CalculatorResult(result=30.0)
```

### FunctionTool

```python
class FunctionTool(func: Callable[[...], Any], description: str, name: str | None = None, global_imports: Sequence[str | ImportFromModule | Alias] = [], strict: bool = False)
```

표준 Python 함수를 도구로 래핑하는 클래스입니다.

#### 주요 매개변수
- `func: Callable` - 래핑할 함수
- `description: str` - 도구 설명
- `name: str | None` - 도구 이름 (None이면 함수명 사용)
- `global_imports: Sequence` - 전역 임포트 목록
- `strict: bool` - 엄격 모드

#### 특징
- 함수의 타입 어노테이션을 기반으로 자동 스키마 생성
- 동기/비동기 함수 모두 지원
- 입력 검증 및 직렬화 자동 처리

```python
import random
from autogen_core.tools import FunctionTool
from autogen_core import CancellationToken
from typing_extensions import Annotated
import asyncio

# 비동기 함수 예제
async def get_stock_price(
    ticker: str, 
    date: Annotated[str, "YYYY/MM/DD 형식의 날짜"]
) -> float:
    """주어진 티커의 주식 가격을 가져옵니다."""
    # 실제로는 API 호출 등을 수행
    return random.uniform(10, 200)

# 동기 함수 예제
def get_weather(
    city: str, 
    unit: Annotated[str, "온도 단위 (celsius/fahrenheit)"] = "celsius"
) -> dict:
    """도시의 날씨 정보를 가져옵니다."""
    return {
        "city": city,
        "temperature": 22 if unit == "celsius" else 72,
        "condition": "sunny",
        "unit": unit
    }

async def function_tool_example():
    # 주식 가격 도구 생성
    stock_tool = FunctionTool(
        get_stock_price,
        description="특정 티커의 주식 가격을 조회합니다."
    )
    
    # 날씨 도구 생성
    weather_tool = FunctionTool(
        get_weather,
        description="도시의 현재 날씨를 조회합니다.",
        name="weather_checker"  # 커스텀 이름
    )
    
    cancellation_token = CancellationToken()
    
    # 주식 가격 조회
    stock_result = await stock_tool.run_json({
        "ticker": "AAPL",
        "date": "2024/01/01"
    }, cancellation_token)
    
    print(f"AAPL 주식 가격: ${stock_result:.2f}")
    
    # 날씨 조회
    weather_result = await weather_tool.run_json({
        "city": "서울",
        "unit": "celsius"
    }, cancellation_token)
    
    print(f"서울 날씨: {weather_result}")

asyncio.run(function_tool_example())
```

## 스트리밍 도구

### StreamTool

```python
class StreamTool(*args, **kwargs)
```

스트리밍 결과를 지원하는 도구의 프로토콜입니다.

**run_json_stream(args: Mapping[str, Any], cancellation_token: CancellationToken, call_id: str | None = None) -> AsyncGenerator[Any, None]**
- 스트리밍 방식으로 도구를 실행합니다.

### BaseStreamTool

```python
class BaseStreamTool(args_type: Type[ArgsT], return_type: Type[ReturnT], name: str, description: str, strict: bool = False)
```

스트리밍 도구 구현을 위한 추상 기본 클래스입니다.

#### 구현해야 할 메서드

**run_stream(args: ArgsT, cancellation_token: CancellationToken) -> AsyncGenerator[StreamT | ReturnT, None]**
- 스트리밍 데이터를 생성하고 최종 결과로 끝나는 제너레이터를 반환합니다.

```python
from autogen_core.tools import BaseStreamTool
from pydantic import BaseModel
import asyncio

class TextGenerationArgs(BaseModel):
    prompt: str
    max_tokens: int = 100

class TextChunk(BaseModel):
    text: str
    is_final: bool = False

class TextGenerationResult(BaseModel):
    full_text: str
    token_count: int

class StreamingTextGenerator(BaseStreamTool[TextGenerationArgs, TextChunk, TextGenerationResult]):
    def __init__(self):
        super().__init__(
            args_type=TextGenerationArgs,
            return_type=TextGenerationResult,
            name="text_generator",
            description="텍스트를 스트리밍 방식으로 생성합니다."
        )
    
    async def run_stream(self, args: TextGenerationArgs, cancellation_token: CancellationToken):
        words = ["안녕하세요", "이것은", "스트리밍", "텍스트", "생성", "예제입니다"]
        full_text = ""
        
        # 스트리밍 청크들 생성
        for i, word in enumerate(words):
            if cancellation_token.is_cancelled():
                break
                
            full_text += word + " "
            
            # 중간 청크 전송
            yield TextChunk(text=word + " ", is_final=False)
            await asyncio.sleep(0.1)  # 실제 생성 시뮬레이션
        
        # 최종 결과 전송
        yield TextGenerationResult(
            full_text=full_text.strip(),
            token_count=len(words)
        )

# 사용 예제
async def streaming_example():
    tool = StreamingTextGenerator()
    cancellation_token = CancellationToken()
    
    print("스트리밍 텍스트 생성:")
    async for chunk in tool.run_json_stream({
        "prompt": "안녕하세요",
        "max_tokens": 50
    }, cancellation_token):
        
        if isinstance(chunk, TextChunk):
            print(chunk.text, end="", flush=True)
        else:  # TextGenerationResult
            print(f"\n\n최종 결과: {chunk.full_text}")
            print(f"토큰 수: {chunk.token_count}")

asyncio.run(streaming_example())
```

## 상태 관리 도구

### BaseToolWithState

```python
class BaseToolWithState(args_type: Type[ArgsT], return_type: Type[ReturnT], state_type: Type[StateT], name: str, description: str)
```

상태를 가지는 도구를 위한 기본 클래스입니다.

#### 구현해야 할 메서드

**save_state() -> StateT**
- 도구의 현재 상태를 저장합니다.

**load_state(state: StateT)**
- 저장된 상태를 복원합니다.

```python
from autogen_core.tools import BaseToolWithState
from pydantic import BaseModel

class CounterArgs(BaseModel):
    increment: int = 1

class CounterResult(BaseModel):
    current_value: int

class CounterState(BaseModel):
    count: int

class StatefulCounter(BaseToolWithState[CounterArgs, CounterResult, CounterState]):
    def __init__(self):
        super().__init__(
            args_type=CounterArgs,
            return_type=CounterResult,
            state_type=CounterState,
            name="counter",
            description="상태를 유지하는 카운터입니다."
        )
        self.count = 0
    
    async def run(self, args: CounterArgs, cancellation_token: CancellationToken) -> CounterResult:
        self.count += args.increment
        return CounterResult(current_value=self.count)
    
    def save_state(self) -> CounterState:
        return CounterState(count=self.count)
    
    def load_state(self, state: CounterState) -> None:
        self.count = state.count

# 사용 예제
async def stateful_tool_example():
    tool = StatefulCounter()
    cancellation_token = CancellationToken()
    
    # 여러 번 실행
    for i in range(3):
        result = await tool.run_json({"increment": i + 1}, cancellation_token)
        print(f"실행 {i+1}: {result}")
    
    # 상태 저장
    state = await tool.save_state_json()
    print(f"저장된 상태: {state}")
    
    # 새로운 도구 인스턴스에 상태 복원
    new_tool = StatefulCounter()
    await new_tool.load_state_json(state)
    
    result = await new_tool.run_json({"increment": 10}, cancellation_token)
    print(f"복원 후 실행: {result}")

asyncio.run(stateful_tool_example())
```

## 워크벤치 시스템

### Workbench

```python
class Workbench()
```

도구들을 관리하고 실행하는 워크벤치의 추상 기본 클래스입니다.

#### 주요 메서드

**start() / stop()**
- 워크벤치를 시작하고 중지합니다.

**call_tool(name: str, arguments: Mapping[str, Any] | None = None, cancellation_token: CancellationToken | None = None, call_id: str | None = None) -> ToolResult**
- 워크벤치의 도구를 호출합니다.

**list_tools() -> List[ToolSchema]**
- 사용 가능한 도구 목록을 반환합니다.

**save_state() / load_state(state: Mapping[str, Any])**
- 워크벤치 상태를 저장하고 복원합니다.

**reset()**
- 워크벤치를 초기 상태로 재설정합니다.

### StaticWorkbench

```python
class StaticWorkbench(tools: List[BaseTool[Any, Any]])
```

정적인 도구 세트를 제공하는 워크벤치입니다.

#### 특징
- 도구 실행 후에도 도구 목록이 변경되지 않음
- 단순하고 예측 가능한 동작

```python
from autogen_core.tools import StaticWorkbench, FunctionTool
import asyncio

def add_numbers(a: float, b: float) -> float:
    """두 숫자를 더합니다."""
    return a + b

def multiply_numbers(a: float, b: float) -> float:
    """두 숫자를 곱합니다."""
    return a * b

async def workbench_example():
    # 도구들 생성
    add_tool = FunctionTool(add_numbers, "두 숫자를 더하는 도구")
    multiply_tool = FunctionTool(multiply_numbers, "두 숫자를 곱하는 도구")
    
    # 워크벤치 생성
    workbench = StaticWorkbench([add_tool, multiply_tool])
    
    # 워크벤치 시작
    await workbench.start()
    
    try:
        # 사용 가능한 도구 목록 확인
        tools = await workbench.list_tools()
        print("사용 가능한 도구들:")
        for tool in tools:
            print(f"- {tool['name']}: {tool.get('description', '')}")
        
        # 도구 실행
        result1 = await workbench.call_tool("add_numbers", {"a": 10, "b": 20})
        print(f"덧셈 결과: {result1.to_text()}")
        
        result2 = await workbench.call_tool("multiply_numbers", {"a": 5, "b": 6})
        print(f"곱셈 결과: {result2.to_text()}")
        
    finally:
        # 워크벤치 중지
        await workbench.stop()

asyncio.run(workbench_example())
```

### StaticStreamWorkbench

```python
class StaticStreamWorkbench(tools: List[BaseTool[Any, Any]])
```

스트리밍 결과를 지원하는 정적 워크벤치입니다.

**call_tool_stream(name: str, arguments: Mapping[str, Any] | None = None, cancellation_token: CancellationToken | None = None, call_id: str | None = None) -> AsyncGenerator[Any | ToolResult, None]**
- 도구를 스트리밍 방식으로 호출합니다.

```python
from autogen_core.tools import StaticStreamWorkbench

async def streaming_workbench_example():
    # 스트리밍 도구가 포함된 워크벤치
    streaming_tool = StreamingTextGenerator()  # 앞에서 정의한 도구
    workbench = StaticStreamWorkbench([streaming_tool])
    
    await workbench.start()
    
    try:
        print("스트리밍 도구 실행:")
        async for chunk in workbench.call_tool_stream("text_generator", {
            "prompt": "안녕하세요",
            "max_tokens": 50
        }):
            if isinstance(chunk, ToolResult):
                print(f"\n최종 결과: {chunk.to_text()}")
            else:
                print(chunk, end="", flush=True)
                
    finally:
        await workbench.stop()

asyncio.run(streaming_workbench_example())
```

## 결과 타입

### ToolResult

```python
class ToolResult(BaseModel)
```

워크벤치에서 도구 실행 결과를 나타내는 클래스입니다.

#### 주요 필드
- `name: str` - 실행된 도구의 이름
- `result: List[TextResultContent | ImageResultContent]` - 실행 결과
- `is_error: bool` - 오류 발생 여부
- `type: Literal['ToolResult']` - 결과 타입

**to_text(replace_image: str | None = None) -> str**
- 결과를 텍스트 문자열로 변환합니다.

### TextResultContent / ImageResultContent

```python
class TextResultContent(BaseModel)
class ImageResultContent(BaseModel)
```

도구 실행 결과의 내용을 나타내는 클래스들입니다.

- `TextResultContent`: 텍스트 결과
- `ImageResultContent`: 이미지 결과

```python
# 결과 처리 예제
async def result_handling_example():
    workbench = StaticWorkbench([add_tool])  # 앞에서 정의한 도구
    await workbench.start()
    
    try:
        result = await workbench.call_tool("add_numbers", {"a": 15, "b": 25})
        
        print(f"도구 이름: {result.name}")
        print(f"오류 여부: {result.is_error}")
        print(f"결과 내용: {result.to_text()}")
        
        # 개별 결과 내용 접근
        for content in result.result:
            if content.type == "TextResultContent":
                print(f"텍스트 결과: {content.content}")
            elif content.type == "ImageResultContent":
                print(f"이미지 결과: [이미지 데이터]")
                
    finally:
        await workbench.stop()
```

## 스키마 및 타입

### ToolSchema

```python
class ToolSchema(TypedDict)
```

도구의 스키마 정보를 정의하는 타입입니다.

#### 필드
- `name: str` - 도구 이름
- `description: str` - 도구 설명 (선택사항)
- `parameters: ParametersSchema` - 매개변수 스키마 (선택사항)
- `strict: bool` - 엄격 모드 (선택사항)

### ParametersSchema

```python
class ParametersSchema(TypedDict)
```

도구 매개변수의 스키마를 정의하는 타입입니다.

#### 필드
- `type: str` - 매개변수 타입
- `properties: Dict[str, Any]` - 속성 정의
- `required: Sequence[str]` - 필수 필드 목록 (선택사항)
- `additionalProperties: bool` - 추가 속성 허용 여부 (선택사항)

## 실용적인 예제

### 종합적인 도구 시스템

```python
import asyncio
from autogen_core.tools import FunctionTool, StaticWorkbench
from autogen_core import CancellationToken
from typing import Dict, List
import json

# 다양한 도구 함수들
def file_read(file_path: str) -> str:
    """파일의 내용을 읽습니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"파일 읽기 오류: {str(e)}"

def file_write(file_path: str, content: str) -> str:
    """파일에 내용을 씁니다."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"파일 '{file_path}'에 성공적으로 저장했습니다."
    except Exception as e:
        return f"파일 쓰기 오류: {str(e)}"

def json_parse(json_string: str) -> Dict:
    """JSON 문자열을 파싱합니다."""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        return {"error": f"JSON 파싱 오류: {str(e)}"}

def list_operations(numbers: List[float], operation: str) -> float:
    """숫자 리스트에 연산을 적용합니다."""
    if operation == "sum":
        return sum(numbers)
    elif operation == "average":
        return sum(numbers) / len(numbers) if numbers else 0
    elif operation == "max":
        return max(numbers) if numbers else 0
    elif operation == "min":
        return min(numbers) if numbers else 0
    else:
        raise ValueError(f"지원하지 않는 연산: {operation}")

class ComprehensiveToolSystem:
    def __init__(self):
        # 도구들 생성
        self.tools = [
            FunctionTool(file_read, "파일 내용을 읽는 도구"),
            FunctionTool(file_write, "파일에 내용을 쓰는 도구"),
            FunctionTool(json_parse, "JSON 문자열을 파싱하는 도구"),
            FunctionTool(list_operations, "숫자 리스트 연산 도구"),
        ]
        
        self.workbench = StaticWorkbench(self.tools)
    
    async def start(self):
        await self.workbench.start()
    
    async def stop(self):
        await self.workbench.stop()
    
    async def execute_workflow(self):
        """복합적인 워크플로우 실행"""
        try:
            # 1. JSON 데이터 생성 및 파일 저장
            json_data = '{"numbers": [1, 2, 3, 4, 5], "operation": "average"}'
            
            write_result = await self.workbench.call_tool("file_write", {
                "file_path": "data.json",
                "content": json_data
            })
            print(f"1. 파일 저장: {write_result.to_text()}")
            
            # 2. 파일 읽기
            read_result = await self.workbench.call_tool("file_read", {
                "file_path": "data.json"
            })
            print(f"2. 파일 읽기: {read_result.to_text()}")
            
            # 3. JSON 파싱
            parse_result = await self.workbench.call_tool("json_parse", {
                "json_string": read_result.to_text()
            })
            print(f"3. JSON 파싱: {parse_result.to_text()}")
            
            # 4. 파싱된 데이터로 계산 수행
            # 실제로는 parse_result에서 데이터를 추출해야 하지만, 
            # 여기서는 예시를 위해 직접 값을 사용
            calc_result = await self.workbench.call_tool("list_operations", {
                "numbers": [1, 2, 3, 4, 5],
                "operation": "average"
            })
            print(f"4. 평균 계산: {calc_result.to_text()}")
            
        except Exception as e:
            print(f"워크플로우 실행 중 오류: {e}")

# 실행
async def main():
    system = ComprehensiveToolSystem()
    await system.start()
    
    try:
        # 사용 가능한 도구 목록 출력
        tools = await system.workbench.list_tools()
        print("=== 사용 가능한 도구들 ===")
        for tool in tools:
            print(f"- {tool['name']}: {tool.get('description', '')}")
        
        print("\n=== 워크플로우 실행 ===")
        await system.execute_workflow()
        
    finally:
        await system.stop()

asyncio.run(main())
```

### 에이전트와 도구 통합

```python
from autogen_core import RoutedAgent, MessageContext, message_handler
from autogen_core.models import UserMessage, AssistantMessage
from autogen_core.tools import StaticWorkbench, FunctionTool

class ToolUsingAgent(RoutedAgent):
    def __init__(self, workbench: StaticWorkbench):
        super().__init__("도구를 사용하는 에이전트")
        self.workbench = workbench
    
    @message_handler
    async def handle_user_message(self, message: UserMessage, ctx: MessageContext) -> None:
        user_input = message.content
        
        # 간단한 명령 파싱 (실제로는 LLM이 도구 선택을 결정)
        if "계산" in user_input and "더하기" in user_input:
            # 숫자 추출 (간단한 예시)
            numbers = [float(x) for x in user_input.split() if x.replace('.', '').isdigit()]
            if len(numbers) >= 2:
                result = await self.workbench.call_tool("add_numbers", {
                    "a": numbers[0],
                    "b": numbers[1]
                })
                response = f"계산 결과: {result.to_text()}"
            else:
                response = "계산할 숫자를 두 개 이상 제공해주세요."
        else:
            response = f"'{user_input}'에 대한 응답입니다. 사용 가능한 명령: '숫자 더하기'"
        
        # 응답 전송
        await self.publish_message(
            AssistantMessage(content=response, source=self.id.type),
            ctx.topic_id
        )

# 에이전트와 도구 통합 예제
async def agent_tool_integration():
    # 도구 생성
    add_tool = FunctionTool(
        lambda a, b: a + b,
        "두 숫자를 더하는 도구"
    )
    
    # 워크벤치 생성 및 시작
    workbench = StaticWorkbench([add_tool])
    await workbench.start()
    
    try:
        # 에이전트 생성
        agent = ToolUsingAgent(workbench)
        
        # 메시지 처리 시뮬레이션
        user_msg = UserMessage(
            content="10과 20을 더하기 계산해주세요",
            source="user"
        )
        
        # 실제로는 런타임에서 처리되지만, 여기서는 직접 호출
        # await agent.handle_user_message(user_msg, mock_context)
        
    finally:
        await workbench.stop()
```

## 주요 고려사항

### 도구 설계 원칙
- **단일 책임**: 각 도구는 하나의 명확한 기능만 수행
- **타입 안전성**: 모든 매개변수와 반환값에 타입 어노테이션 사용
- **오류 처리**: 예외 상황을 적절히 처리하고 의미 있는 오류 메시지 제공
- **문서화**: 도구의 목적과 사용법을 명확히 설명

### 성능 최적화
- **스트리밍**: 큰 결과나 실시간 피드백이 필요한 경우 스트리밍 도구 사용
- **상태 관리**: 필요한 경우에만 상태를 유지하고, 적절한 상태 저장/복원 구현
- **리소스 관리**: 워크벤치의 start/stop을 통한 적절한 리소스 관리

### 보안 고려사항
- **입력 검증**: 모든 도구 입력에 대한 철저한 검증
- **권한 제어**: 민감한 작업에 대한 적절한 권한 확인
- **샌드박싱**: 위험한 작업의 경우 격리된 환경에서 실행

### 확장성
- **모듈화**: 관련 도구들을 그룹화하여 관리
- **플러그인 시스템**: 동적으로 도구를 추가/제거할 수 있는 구조
- **버전 관리**: 도구 스키마 변경 시 하위 호환성 고려

이 문서는 `autogen_core.tools` 모듈의 모든 구성 요소를 다루며, 효과적인 도구 시스템 구축을 위한 실용적인 가이드를 제공합니다. 