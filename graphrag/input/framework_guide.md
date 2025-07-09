# Agent and Agent Runtime

이 섹션과 다음 섹션에서는 AutoGen의 핵심 개념인 agents, agent runtime, messages, 그리고 communication에 대해 집중적으로 다룹니다. 이들은 멀티 에이전트 애플리케이션의 기본 구성 요소입니다.

> **Note**
> 
> Core API는 의견을 강요하지 않고 유연하도록 설계되었습니다. 때때로 어려움을 느낄 수 있습니다. 상호작용적이고 확장 가능하며 분산된 멀티 에이전트 시스템을 구축하고 모든 워크플로우를 완전히 제어하고 싶다면 계속하십시오. 빠르게 무언가를 실행하고 싶다면 AgentChat API를 살펴보는 것이 좋습니다.

AutoGen에서 에이전트는 기본 인터페이스 `Agent`로 정의된 엔티티입니다. 이는 `AgentId` 타입의 고유 식별자와 `AgentMetadata` 타입의 메타데이터 딕셔너리를 가집니다.

대부분의 경우, `RoutedAgent`라는 상위 레벨 클래스에서 에이전트를 서브클래싱할 수 있습니다. 이는 `message_handler()` 데코레이터로 지정된 해당 메시지 핸들러로 메시지를 라우팅하고 메시지 변수에 대한 적절한 타입 힌트를 제공합니다.

에이전트 런타임은 AutoGen에서 에이전트를 위한 실행 환경입니다.

프로그래밍 언어의 런타임 환경과 유사하게, 에이전트 런타임은 에이전트 간의 통신을 촉진하고, 에이전트 생명주기를 관리하며, 보안 경계를 강화하고, 모니터링 및 디버깅을 지원하는 데 필요한 인프라를 제공합니다.

로컬 개발을 위해 개발자는 Python 애플리케이션에 임베드될 수 있는 `SingleThreadedAgentRuntime`을 사용할 수 있습니다.

> **Note**
> 
> 에이전트는 애플리케이션 코드에 의해 직접 인스턴스화되고 관리되지 않습니다. 대신, 필요할 때 런타임에 의해 생성되고 런타임에 의해 관리됩니다.

AgentChat에 이미 익숙하다면, `AssistantAgent`와 같은 AgentChat의 에이전트들은 애플리케이션에 의해 생성되므로 런타임에 의해 직접 관리되지 않는다는 점을 주목하는 것이 중요합니다. Core에서 AgentChat 에이전트를 사용하려면, AgentChat 에이전트에게 메시지를 위임하는 래퍼 Core 에이전트를 생성하고 런타임이 래퍼 에이전트를 관리하도록 해야 합니다.

## 에이전트 구현하기

에이전트를 구현하려면, 개발자는 `RoutedAgent` 클래스를 서브클래싱하고 `message_handler()` 데코레이터를 사용하여 에이전트가 처리할 것으로 예상되는 각 메시지 타입에 대한 메시지 핸들러 메서드를 구현해야 합니다. 예를 들어, 다음 에이전트는 간단한 메시지 타입 `MyMessageType`을 처리하고 받은 메시지를 출력합니다:

```python
from dataclasses import dataclass

from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler


@dataclass
class MyMessageType:
    content: str


class MyAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("MyAgent")

    @message_handler
    async def handle_my_message_type(self, message: MyMessageType, ctx: MessageContext) -> None:
        print(f"{self.id.type} received message: {message.content}")
```

이 에이전트는 `MyMessageType`만 처리하며 메시지는 `handle_my_message_type` 메서드로 전달됩니다. 개발자는 `message_handler()` 데코레이터를 사용하고 핸들러 함수의 메시지 변수에 타입 힌트를 설정하여 다양한 메시지 타입에 대한 여러 메시지 핸들러를 가질 수 있습니다. 에이전트의 로직에 더 적합하다면 하나의 메시지 핸들러 함수에서 메시지 변수에 대해 Python 타이핑 유니언을 활용할 수도 있습니다. 메시지와 통신에 대한 다음 섹션을 참조하십시오.

## AgentChat 에이전트 사용하기

AgentChat 에이전트가 있고 이를 Core API에서 사용하고 싶다면, AgentChat 에이전트에게 메시지를 위임하는 래퍼 `RoutedAgent`를 생성할 수 있습니다. 다음 예제는 AgentChat의 `AssistantAgent`에 대한 래퍼 에이전트를 생성하는 방법을 보여줍니다.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient


class MyAssistant(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o")
        self._delegate = AssistantAgent(name, model_client=model_client)

    @message_handler
    async def handle_my_message_type(self, message: MyMessageType, ctx: MessageContext) -> None:
        print(f"{self.id.type} received message: {message.content}")
        response = await self._delegate.on_messages(
            [TextMessage(content=message.content, source="user")], ctx.cancellation_token
        )
        print(f"{self.id.type} responded: {response.chat_message}")
```

모델 클라이언트 사용 방법은 Model Client 섹션을 참조하십시오.

Core API는 의견을 강요하지 않으므로, Core API를 사용하기 위해 AgentChat API를 사용할 필요가 없습니다. 자신만의 에이전트를 구현하거나 다른 에이전트 프레임워크를 사용할 수 있습니다.

## 에이전트 타입 등록하기

에이전트를 런타임에서 사용할 수 있도록 하려면, 개발자는 `BaseAgent` 클래스의 `register()` 클래스 메서드를 사용할 수 있습니다. 등록 과정은 문자열로 고유하게 식별되는 에이전트 타입과 주어진 클래스의 에이전트 타입 인스턴스를 생성하는 팩토리 함수를 연결합니다. 팩토리 함수는 필요할 때 에이전트 인스턴스의 자동 생성을 허용하는 데 사용됩니다.

에이전트 타입(`AgentType`)은 에이전트 클래스와 같지 않습니다. 이 예제에서 에이전트 타입은 `AgentType("my_agent")` 또는 `AgentType("my_assistant")`이고 에이전트 클래스는 Python 클래스 `MyAgent` 또는 `MyAssistantAgent`입니다. 팩토리 함수는 `register()` 클래스 메서드가 호출된 에이전트 클래스의 인스턴스를 반환할 것으로 예상됩니다. 에이전트 타입과 정체성에 대해 더 자세히 알아보려면 Agent Identity and Lifecycles를 읽어보십시오.

> **Note**
> 
> 다른 에이전트 타입들은 같은 에이전트 클래스를 반환하는 팩토리 함수로 등록될 수 있습니다. 예를 들어, 팩토리 함수에서 생성자 매개변수의 변형을 사용하여 같은 에이전트 클래스의 다른 인스턴스를 생성할 수 있습니다.

`SingleThreadedAgentRuntime`에 에이전트 타입을 등록하려면 다음 코드를 사용할 수 있습니다:

```python
from autogen_core import SingleThreadedAgentRuntime

runtime = SingleThreadedAgentRuntime()
await MyAgent.register(runtime, "my_agent", lambda: MyAgent())
await MyAssistant.register(runtime, "my_assistant", lambda: MyAssistant("my_assistant"))
# AgentType(type='my_assistant')
```

에이전트 타입이 등록되면, `AgentId`를 사용하여 에이전트 인스턴스에 직접 메시지를 보낼 수 있습니다. 런타임은 이 인스턴스에 메시지를 처음 전달할 때 인스턴스를 생성합니다.

```python
runtime.start()  # 백그라운드에서 메시지 처리를 시작합니다.
await runtime.send_message(MyMessageType("Hello, World!"), AgentId("my_agent", "default"))
await runtime.send_message(MyMessageType("Hello, World!"), AgentId("my_assistant", "default"))
await runtime.stop()  # 백그라운드에서 메시지 처리를 중지합니다.
```

출력:
```
my_agent received message: Hello, World!
my_assistant received message: Hello, World!
my_assistant responded: Hello! How can I assist you today?
```

> **Note**
> 
> 런타임이 에이전트의 생명주기를 관리하기 때문에, `AgentId`는 에이전트와 통신하거나 메타데이터(예: 설명)를 검색하는 데만 사용됩니다.

## Single-Threaded Agent Runtime 실행하기

위의 코드 스니펫은 `start()`를 사용하여 수신자의 메시지 핸들러에 메시지를 처리하고 전달하는 백그라운드 작업을 시작합니다. 이는 로컬 임베디드 런타임 `SingleThreadedAgentRuntime`의 기능입니다.

백그라운드 작업을 즉시 중지하려면 `stop()` 메서드를 사용하십시오:

```python
runtime.start()
# ... 메시지 보내기, 메시지 게시 등.
await runtime.stop()  # 즉시 반환되지만 진행 중인 메시지 처리는 취소하지 않습니다.
```

`start()`를 다시 호출하여 백그라운드 작업을 재개할 수 있습니다.

에이전트를 평가하기 위한 벤치마크 실행과 같은 배치 시나리오의 경우, 처리되지 않은 메시지가 없고 에이전트가 메시지를 처리하지 않을 때 백그라운드 작업이 자동으로 중지되기를 기다릴 수 있습니다 – 배치가 완료된 것으로 간주될 수 있습니다. `stop_when_idle()` 메서드를 사용하여 이를 달성할 수 있습니다:

```python
runtime.start()
# ... 메시지 보내기, 메시지 게시 등.
await runtime.stop_when_idle()  # 런타임이 유휴 상태가 될 때까지 블록됩니다.
```

런타임을 닫고 리소스를 해제하려면 `close()` 메서드를 사용하십시오:

```python
await runtime.close()
```

다른 런타임 구현들은 런타임을 실행하는 고유한 방법을 가질 것입니다.
