from abc import ABC, abstractmethod
from typing import Any

class BaseLLM(ABC):
    
    @abstractmethod
    def invoke(self, messages: list[Any]) -> Any:
        pass
