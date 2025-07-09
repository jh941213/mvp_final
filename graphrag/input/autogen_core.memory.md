# autogen_core.memory 모듈

`autogen_core.memory` 모듈은 에이전트가 정보를 저장하고 검색할 수 있는 메모리 시스템을 제공합니다. 모델 컨텍스트를 풍부하게 하거나 수정하는 데 사용할 수 있는 데이터 저장소 역할을 합니다.

## 핵심 개념

메모리 시스템은 다음과 같은 핵심 기능을 제공합니다:
- **저장**: 다양한 형태의 콘텐츠를 메모리에 추가
- **검색**: 쿼리를 통해 관련 메모리 내용 검색
- **컨텍스트 업데이트**: 모델 컨텍스트에 메모리 내용 반영
- **관리**: 메모리 내용 정리 및 리소스 관리

## 기본 인터페이스

### Memory

```python
class Memory()
```

모든 메모리 구현체가 따라야 하는 추상 기본 클래스입니다.

#### 주요 메서드

**add(content: MemoryContent, cancellation_token: CancellationToken | None = None) -> None**
- 새로운 콘텐츠를 메모리에 추가합니다.

**query(query: str | MemoryContent, cancellation_token: CancellationToken | None = None, **kwargs: Any) -> MemoryQueryResult**
- 메모리 저장소를 쿼리하여 관련 항목을 반환합니다.

**update_context(model_context: ChatCompletionContext) -> UpdateContextResult**
- 관련 메모리 콘텐츠를 사용하여 모델 컨텍스트를 업데이트합니다.

**clear() -> None**
- 메모리의 모든 항목을 삭제합니다.

**close() -> None**
- 메모리 구현체가 사용하는 리소스를 정리합니다.

## 구현체

### ListMemory

```python
class ListMemory(name: str | None = None, memory_contents: List[MemoryContent] | None = None)
```

시간순으로 정렬된 리스트 기반의 간단한 메모리 구현체입니다.

#### 주요 매개변수
- `name: str | None` - 메모리 인스턴스의 식별자 (선택사항)
- `memory_contents: List[MemoryContent] | None` - 초기 메모리 콘텐츠 (선택사항)

#### 특징
- 콘텐츠를 리스트에 저장하고 시간순으로 검색
- `content` 속성을 통해 직접 메모리 콘텐츠 접근 및 수정 가능
- 모든 저장된 메모리를 SystemMessage로 모델 컨텍스트에 추가

#### 주요 속성 및 메서드

**content: List[MemoryContent]**
- 현재 메모리 콘텐츠 목록을 반환합니다.

**name: str**
- 메모리 인스턴스 식별자를 반환합니다.

```python
import asyncio
from autogen_core.memory import ListMemory, MemoryContent
from autogen_core.model_context import BufferedChatCompletionContext

async def list_memory_example():
    # 메모리 초기화
    memory = ListMemory(name="chat_history")
    
    # 메모리 콘텐츠 추가
    content1 = MemoryContent(
        content="사용자는 정중한 언어를 선호합니다", 
        mime_type="text/plain"
    )
    await memory.add(content1)
    
    content2 = MemoryContent(
        content="사용자의 관심사: 인공지능, 프로그래밍", 
        mime_type="text/plain"
    )
    await memory.add(content2)
    
    # 직접 메모리 콘텐츠 수정
    new_content = MemoryContent(
        content="새로운 선호사항: 간결한 답변", 
        mime_type="text/plain"
    )
    memory.content = [new_content]
    
    # 모델 컨텍스트 생성
    model_context = BufferedChatCompletionContext(buffer_size=10)
    
    # 메모리로 모델 컨텍스트 업데이트
    update_result = await memory.update_context(model_context)
    
    # 업데이트된 모델 컨텍스트 확인
    messages = await model_context.get_messages()
    print("업데이트된 컨텍스트:")
    for msg in messages:
        print(f"- {type(msg).__name__}: {getattr(msg, 'content', str(msg))}")
    
    # 메모리 쿼리
    query_result = await memory.query("선호사항")
    print(f"\n쿼리 결과: {len(query_result.results)}개 항목")
    for result in query_result.results:
        print(f"- {result.content}")

asyncio.run(list_memory_example())
```

## 데이터 모델

### MemoryContent

```python
class MemoryContent(BaseModel)
```

메모리 콘텐츠 항목을 나타내는 모델입니다.

#### 주요 필드
- `content: str | bytes | Dict[str, Any] | Image` - 메모리 항목의 콘텐츠
- `mime_type: MemoryMimeType | str` - 메모리 콘텐츠의 MIME 타입
- `metadata: Dict[str, Any] | None` - 메모리 항목과 연관된 메타데이터

#### 메서드

**serialize_mime_type(mime_type: MemoryMimeType | str) -> str**
- MIME 타입을 문자열로 직렬화합니다.

```python
from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_core import Image

# 텍스트 콘텐츠
text_content = MemoryContent(
    content="중요한 정보: 사용자는 한국어를 선호합니다",
    mime_type=MemoryMimeType.TEXT,
    metadata={"importance": "high", "category": "preference"}
)

# JSON 콘텐츠
json_content = MemoryContent(
    content={"user_id": "12345", "preferences": ["korean", "concise"]},
    mime_type=MemoryMimeType.JSON,
    metadata={"source": "user_profile"}
)

# 마크다운 콘텐츠
markdown_content = MemoryContent(
    content="# 사용자 가이드\n\n사용자는 다음을 선호합니다:\n- 정중한 언어\n- 구체적인 예시",
    mime_type=MemoryMimeType.MARKDOWN
)

# 이미지 콘텐츠 (예시)
# image_content = MemoryContent(
#     content=Image.from_path("user_diagram.png"),
#     mime_type=MemoryMimeType.IMAGE,
#     metadata={"description": "사용자 워크플로우 다이어그램"}
# )

# 바이너리 콘텐츠
binary_content = MemoryContent(
    content=b"binary_data_here",
    mime_type=MemoryMimeType.BINARY,
    metadata={"format": "custom"}
)
```

### MemoryMimeType

```python
class MemoryMimeType(Enum)
```

메모리 콘텐츠에 지원되는 MIME 타입을 정의하는 열거형입니다.

#### 지원되는 타입
- `TEXT = 'text/plain'` - 일반 텍스트
- `MARKDOWN = 'text/markdown'` - 마크다운 텍스트
- `JSON = 'application/json'` - JSON 데이터
- `IMAGE = 'image/*'` - 이미지 파일
- `BINARY = 'application/octet-stream'` - 바이너리 데이터

### MemoryQueryResult

```python
class MemoryQueryResult(BaseModel)
```

메모리 쿼리 작업의 결과를 나타내는 모델입니다.

#### 주요 필드
- `results: List[MemoryContent]` - 쿼리 결과로 반환된 메모리 콘텐츠 목록

### UpdateContextResult

```python
class UpdateContextResult(BaseModel)
```

메모리 컨텍스트 업데이트 작업의 결과를 나타내는 모델입니다.

#### 주요 필드
- `memories: MemoryQueryResult` - 컨텍스트에 추가된 메모리들

## 실용적인 예제

### 대화 기록 메모리 시스템

```python
import asyncio
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_core.model_context import UnboundedChatCompletionContext
from autogen_core.models import SystemMessage, UserMessage, AssistantMessage
from typing import Dict, List
import json
from datetime import datetime

class ConversationMemoryManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.preferences_memory = ListMemory(name=f"preferences_{user_id}")
        self.context_memory = ListMemory(name=f"context_{user_id}")
        self.facts_memory = ListMemory(name=f"facts_{user_id}")
    
    async def add_user_preference(self, preference: str, category: str = "general"):
        """사용자 선호사항 추가"""
        content = MemoryContent(
            content=preference,
            mime_type=MemoryMimeType.TEXT,
            metadata={
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "type": "preference"
            }
        )
        await self.preferences_memory.add(content)
    
    async def add_conversation_context(self, context: str, importance: str = "medium"):
        """대화 컨텍스트 추가"""
        content = MemoryContent(
            content=context,
            mime_type=MemoryMimeType.TEXT,
            metadata={
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
                "type": "context"
            }
        )
        await self.context_memory.add(content)
    
    async def add_user_fact(self, fact: Dict[str, any]):
        """사용자 관련 사실 추가"""
        content = MemoryContent(
            content=fact,
            mime_type=MemoryMimeType.JSON,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "type": "fact"
            }
        )
        await self.facts_memory.add(content)
    
    async def create_personalized_context(self) -> UnboundedChatCompletionContext:
        """개인화된 모델 컨텍스트 생성"""
        context = UnboundedChatCompletionContext()
        
        # 시스템 메시지 추가
        await context.add_message(SystemMessage(
            content="당신은 사용자의 선호사항과 컨텍스트를 고려하는 개인화된 어시스턴트입니다."
        ))
        
        # 각 메모리에서 컨텍스트 업데이트
        await self.preferences_memory.update_context(context)
        await self.context_memory.update_context(context)
        await self.facts_memory.update_context(context)
        
        return context
    
    async def get_memory_summary(self) -> Dict[str, int]:
        """메모리 요약 정보 반환"""
        return {
            "preferences": len(self.preferences_memory.content),
            "contexts": len(self.context_memory.content),
            "facts": len(self.facts_memory.content)
        }
    
    async def clear_all_memories(self):
        """모든 메모리 정리"""
        await self.preferences_memory.clear()
        await self.context_memory.clear()
        await self.facts_memory.clear()

# 사용 예제
async def conversation_memory_example():
    # 메모리 매니저 생성
    memory_manager = ConversationMemoryManager("user_123")
    
    # 사용자 선호사항 추가
    await memory_manager.add_user_preference("정중하고 예의바른 언어 사용", "communication")
    await memory_manager.add_user_preference("구체적인 예시와 함께 설명", "explanation")
    await memory_manager.add_user_preference("한국어로 대화", "language")
    
    # 대화 컨텍스트 추가
    await memory_manager.add_conversation_context("사용자는 Python 프로그래밍을 배우고 있음", "high")
    await memory_manager.add_conversation_context("최근에 웹 개발에 관심을 보임", "medium")
    
    # 사용자 사실 추가
    await memory_manager.add_user_fact({
        "occupation": "학생",
        "experience_level": "초급",
        "interests": ["AI", "웹개발", "데이터분석"]
    })
    
    # 개인화된 컨텍스트 생성
    personalized_context = await memory_manager.create_personalized_context()
    
    # 컨텍스트 내용 확인
    messages = await personalized_context.get_messages()
    print("=== 개인화된 컨텍스트 ===")
    for i, msg in enumerate(messages):
        print(f"{i+1}. {type(msg).__name__}: {getattr(msg, 'content', str(msg))[:100]}...")
    
    # 메모리 요약
    summary = await memory_manager.get_memory_summary()
    print(f"\n=== 메모리 요약 ===")
    print(f"선호사항: {summary['preferences']}개")
    print(f"컨텍스트: {summary['contexts']}개")
    print(f"사실: {summary['facts']}개")

asyncio.run(conversation_memory_example())
```

### 지식 기반 메모리 시스템

```python
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
import asyncio
from typing import List, Dict
import json

class KnowledgeBaseMemory:
    def __init__(self, domain: str):
        self.domain = domain
        self.memory = ListMemory(name=f"kb_{domain}")
    
    async def add_knowledge(self, title: str, content: str, category: str, 
                          confidence: float = 1.0, sources: List[str] = None):
        """지식 항목 추가"""
        knowledge_item = {
            "title": title,
            "content": content,
            "category": category,
            "confidence": confidence,
            "sources": sources or [],
            "added_at": datetime.now().isoformat()
        }
        
        memory_content = MemoryContent(
            content=knowledge_item,
            mime_type=MemoryMimeType.JSON,
            metadata={
                "category": category,
                "confidence": confidence,
                "type": "knowledge"
            }
        )
        
        await self.memory.add(memory_content)
    
    async def add_example(self, title: str, code: str, description: str, 
                         language: str = "python"):
        """코드 예제 추가"""
        example_item = {
            "title": title,
            "code": code,
            "description": description,
            "language": language,
            "type": "example"
        }
        
        memory_content = MemoryContent(
            content=example_item,
            mime_type=MemoryMimeType.JSON,
            metadata={
                "language": language,
                "type": "example"
            }
        )
        
        await self.memory.add(memory_content)
    
    async def add_best_practice(self, practice: str, rationale: str, 
                              importance: str = "medium"):
        """모범 사례 추가"""
        best_practice = f"**모범 사례**: {practice}\n\n**이유**: {rationale}"
        
        memory_content = MemoryContent(
            content=best_practice,
            mime_type=MemoryMimeType.MARKDOWN,
            metadata={
                "importance": importance,
                "type": "best_practice"
            }
        )
        
        await self.memory.add(memory_content)
    
    async def get_knowledge_by_category(self, category: str) -> List[Dict]:
        """카테고리별 지식 검색"""
        all_memories = await self.memory.query("")
        
        filtered_knowledge = []
        for memory_item in all_memories.results:
            if (memory_item.metadata and 
                memory_item.metadata.get("category") == category):
                if memory_item.mime_type == MemoryMimeType.JSON:
                    filtered_knowledge.append(memory_item.content)
        
        return filtered_knowledge
    
    async def create_specialized_context(self, focus_area: str = None):
        """특화된 컨텍스트 생성"""
        context = UnboundedChatCompletionContext()
        
        # 도메인별 시스템 메시지
        system_msg = f"당신은 {self.domain} 분야의 전문가입니다. "
        if focus_area:
            system_msg += f"특히 {focus_area}에 집중하여 답변해주세요."
        
        await context.add_message(SystemMessage(content=system_msg))
        
        # 메모리 내용을 컨텍스트에 추가
        await self.memory.update_context(context)
        
        return context

# 사용 예제
async def knowledge_base_example():
    # Python 프로그래밍 지식 기반 생성
    python_kb = KnowledgeBaseMemory("Python Programming")
    
    # 기본 지식 추가
    await python_kb.add_knowledge(
        title="리스트 컴프리헨션",
        content="리스트 컴프리헨션은 기존 리스트를 기반으로 새로운 리스트를 간결하게 생성하는 방법입니다.",
        category="syntax",
        confidence=0.95,
        sources=["Python 공식 문서"]
    )
    
    # 코드 예제 추가
    await python_kb.add_example(
        title="리스트 컴프리헨션 기본 예제",
        code="""
# 기본 형태
squares = [x**2 for x in range(10)]

# 조건부 필터링
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# 중첩 리스트 평탄화
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [item for row in matrix for item in row]
        """,
        description="리스트 컴프리헨션의 다양한 사용 패턴을 보여주는 예제입니다.",
        language="python"
    )
    
    # 모범 사례 추가
    await python_kb.add_best_practice(
        practice="복잡한 로직이 포함된 경우 일반 for 루프 사용",
        rationale="리스트 컴프리헨션이 너무 복잡해지면 가독성이 떨어지므로, 명확성을 위해 일반 루프를 사용하는 것이 좋습니다.",
        importance="high"
    )
    
    # 카테고리별 지식 검색
    syntax_knowledge = await python_kb.get_knowledge_by_category("syntax")
    print("=== Syntax 카테고리 지식 ===")
    for knowledge in syntax_knowledge:
        print(f"제목: {knowledge['title']}")
        print(f"내용: {knowledge['content']}")
        print(f"신뢰도: {knowledge['confidence']}")
        print()
    
    # 특화된 컨텍스트 생성
    specialized_context = await python_kb.create_specialized_context("리스트 처리")
    
    # 컨텍스트 내용 확인
    messages = await specialized_context.get_messages()
    print("=== 특화된 컨텍스트 ===")
    for i, msg in enumerate(messages):
        content = getattr(msg, 'content', str(msg))
        print(f"{i+1}. {type(msg).__name__}: {content[:200]}...")

asyncio.run(knowledge_base_example())
```

### 멀티 모달 메모리 시스템

```python
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_core import Image
import asyncio

class MultiModalMemorySystem:
    def __init__(self, name: str):
        self.name = name
        self.memory = ListMemory(name=f"multimodal_{name}")
    
    async def add_text_memory(self, text: str, category: str = "general"):
        """텍스트 메모리 추가"""
        content = MemoryContent(
            content=text,
            mime_type=MemoryMimeType.TEXT,
            metadata={"category": category, "modality": "text"}
        )
        await self.memory.add(content)
    
    async def add_structured_data(self, data: Dict, schema_name: str):
        """구조화된 데이터 추가"""
        content = MemoryContent(
            content=data,
            mime_type=MemoryMimeType.JSON,
            metadata={"schema": schema_name, "modality": "structured"}
        )
        await self.memory.add(content)
    
    async def add_documentation(self, markdown_content: str, topic: str):
        """마크다운 문서 추가"""
        content = MemoryContent(
            content=markdown_content,
            mime_type=MemoryMimeType.MARKDOWN,
            metadata={"topic": topic, "modality": "documentation"}
        )
        await self.memory.add(content)
    
    # 이미지 메모리 추가 (실제 이미지 파일이 있을 때)
    # async def add_image_memory(self, image_path: str, description: str):
    #     """이미지 메모리 추가"""
    #     image = Image.from_path(image_path)
    #     content = MemoryContent(
    #         content=image,
    #         mime_type=MemoryMimeType.IMAGE,
    #         metadata={"description": description, "modality": "image"}
    #     )
    #     await self.memory.add(content)
    
    async def get_memories_by_modality(self, modality: str) -> List[MemoryContent]:
        """모달리티별 메모리 검색"""
        all_memories = await self.memory.query("")
        
        return [
            memory for memory in all_memories.results
            if memory.metadata and memory.metadata.get("modality") == modality
        ]
    
    async def create_rich_context(self):
        """다양한 모달리티를 포함한 풍부한 컨텍스트 생성"""
        context = UnboundedChatCompletionContext()
        
        # 시스템 메시지
        await context.add_message(SystemMessage(
            content="당신은 텍스트, 구조화된 데이터, 문서 등 다양한 형태의 정보를 활용할 수 있는 멀티모달 어시스턴트입니다."
        ))
        
        # 메모리 내용을 컨텍스트에 추가
        await self.memory.update_context(context)
        
        return context

# 사용 예제
async def multimodal_memory_example():
    # 멀티모달 메모리 시스템 생성
    mm_memory = MultiModalMemorySystem("project_assistant")
    
    # 텍스트 메모리 추가
    await mm_memory.add_text_memory(
        "프로젝트 데드라인은 2024년 3월 15일입니다.",
        category="schedule"
    )
    
    # 구조화된 데이터 추가
    await mm_memory.add_structured_data(
        {
            "project_name": "AI 챗봇 개발",
            "team_members": ["김개발", "이디자인", "박기획"],
            "status": "진행중",
            "completion": 65
        },
        schema_name="project_info"
    )
    
    # 문서 추가
    await mm_memory.add_documentation(
        """
# 프로젝트 가이드라인

## 코딩 스타일
- PEP 8 준수
- 타입 힌트 사용
- 명확한 변수명 사용

## 테스트
- 단위 테스트 작성 필수
- 커버리지 80% 이상 유지

## 문서화
- README.md 업데이트
- API 문서 자동 생성
        """,
        topic="development_guidelines"
    )
    
    # 모달리티별 메모리 검색
    text_memories = await mm_memory.get_memories_by_modality("text")
    structured_memories = await mm_memory.get_memories_by_modality("structured")
    doc_memories = await mm_memory.get_memories_by_modality("documentation")
    
    print("=== 모달리티별 메모리 현황 ===")
    print(f"텍스트 메모리: {len(text_memories)}개")
    print(f"구조화된 데이터: {len(structured_memories)}개")
    print(f"문서: {len(doc_memories)}개")
    
    # 풍부한 컨텍스트 생성
    rich_context = await mm_memory.create_rich_context()
    
    # 컨텍스트 내용 확인
    messages = await rich_context.get_messages()
    print(f"\n=== 생성된 컨텍스트 ===")
    print(f"총 메시지 수: {len(messages)}")
    for i, msg in enumerate(messages):
        content = getattr(msg, 'content', str(msg))
        print(f"{i+1}. {type(msg).__name__}: {content[:150]}...")

asyncio.run(multimodal_memory_example())
```

## 주요 고려사항

### 메모리 설계 원칙
- **관련성**: 현재 컨텍스트와 관련된 메모리만 선택적으로 활용
- **효율성**: 메모리 크기와 검색 성능 간의 균형 고려
- **일관성**: 메모리 콘텐츠의 형식과 구조 일관성 유지
- **메타데이터 활용**: 효과적인 검색과 분류를 위한 메타데이터 설계

### 성능 최적화
- **인덱싱**: 대용량 메모리의 경우 적절한 인덱싱 전략 필요
- **캐싱**: 자주 접근되는 메모리 내용 캐싱
- **압축**: 큰 메모리 콘텐츠의 압축 저장 고려
- **정리**: 오래되거나 불필요한 메모리의 주기적 정리

### 확장성 고려사항
- **커스텀 메모리**: 특수한 요구사항을 위한 Memory 인터페이스 구현
- **분산 저장**: 여러 저장소에 걸친 메모리 관리
- **버전 관리**: 메모리 콘텐츠의 버전 추적 및 관리
- **동기화**: 여러 에이전트 간의 메모리 동기화

### 보안 및 프라이버시
- **민감 정보**: 개인정보나 민감한 데이터의 안전한 저장
- **접근 제어**: 메모리 접근에 대한 권한 관리
- **암호화**: 중요한 메모리 콘텐츠의 암호화 저장
- **감사 로그**: 메모리 접근 및 수정 이력 추적

이 문서는 `autogen_core.memory` 모듈의 모든 구성 요소를 다루며, 효과적인 메모리 시스템 구축을 위한 실용적인 가이드를 제공합니다. 