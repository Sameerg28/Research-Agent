from __future__ import annotations

from interfaces.llm import LLMInterface
from interfaces.tool import ToolInterface


class LLMTool(ToolInterface):
    def __init__(self, llm: LLMInterface) -> None:
        self._llm = llm

    def execute(self, input_data: dict | str) -> dict:
        if not isinstance(input_data, dict):
            return self._llm.generate("", str(input_data), allow_chunking=False)

        return self._llm.generate(
            system_prompt=str(input_data.get("system_prompt", "")),
            user_prompt=str(input_data.get("user_prompt", "")),
            allow_chunking=bool(input_data.get("allow_chunking", False)),
        )
