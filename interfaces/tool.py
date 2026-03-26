from __future__ import annotations

from abc import ABC, abstractmethod


class ToolInterface(ABC):
    @abstractmethod
    def execute(self, input_data: dict | str) -> object:
        raise NotImplementedError
