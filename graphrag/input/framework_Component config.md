# Component config

AutoGen components are able to be declaratively configured in a generic fashion. This is to support configuration based experiences, such as AutoGen studio, but it is also useful for many other scenarios.

The system that provides this is called "component configuration". In AutoGen, a component is simply something that can be created from a config object and itself can be dumped to a config object. In this way, you can define a component in code and then get the config object from it.

This system is generic and allows for components defined outside of AutoGen itself (such as extensions) to be configured in the same way.

## How does this differ from state?

This is a very important point to clarify. When we talk about serializing an object, we must include all data that makes that object itself. Including things like message history etc. When deserializing from serialized state, you must get back the exact same object. This is not the case with component configuration.

Component configuration should be thought of as the blueprint for an object, and can be stamped out many times to create many instances of the same configured object.

## Usage

If you have a component in Python and want to get the config for it, simply call dump_component() on it. The resulting object can be passed back into load_component() to get the component back.

### Loading a component from a config

To load a component from a config object, you can use the load_component() method. This method will take a config object and return a component object. It is best to call this method on the interface you want. For example to load a model client:

```python
from autogen_core.models import ChatCompletionClient

config = {
    "provider": "openai_chat_completion_client",
    "config": {"model": "gpt-4o"},
}

client = ChatCompletionClient.load_component(config)
```

### Creating a component class

To add component functionality to a given class:

1. Add a call to Component() in the class inheritance list.
2. Implment the _to_config() and _from_config() methods

For example:

```python
from autogen_core import Component, ComponentBase
from pydantic import BaseModel


class Config(BaseModel):
    value: str


class MyComponent(ComponentBase[Config], Component[Config]):
    component_type = "custom"
    component_config_schema = Config

    def __init__(self, value: str):
        self.value = value

    def _to_config(self) -> Config:
        return Config(value=self.value)

    @classmethod
    def _from_config(cls, config: Config) -> "MyComponent":
        return cls(value=config.value)
```

## Secrets

If a field of a config object is a secret value, it should be marked using SecretStr, this will ensure that the value will not be dumped to the config object.

For example:

```python
from pydantic import BaseModel, SecretStr


class ClientConfig(BaseModel):
    endpoint: str
    api_key: SecretStr
```
