# tools/tool_registry.py 수정 및 registry에 기본 툴 포함

import importlib
import inspect
import os
from typing import Callable, Dict

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict] = {}

    def register(self, name: str, description: str, params: dict, func: Callable):
        self._tools[name] = {
            "description": description,
            "params": params,
            "function": func
        }

    def list(self) -> Dict[str, Dict]:
        return self._tools

    def run(self, name: str, args: dict):
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found.")

        func = tool["function"]
        
        # ✅ 함수가 state를 받는 형태일 경우: args는 그대로 넘김
        if "state" in func.__code__.co_varnames:
            return func(args)

        # ✅ 함수가 input을 받는 형태일 경우: input만 꺼내서 넘김
        return func(args["input"])

    def auto_register_builtin_tools(self, module_paths):
        for module_path in module_paths:
            try:
                mod = importlib.import_module(module_path)

                for name, func in inspect.getmembers(mod, inspect.isfunction):
                    if name.startswith(("use_", "generate_", "read_", "report_", "mock_", "direct_")):
                        # docstring에서 첫 줄을 설명으로 사용
                        doc = inspect.getdoc(func)
                        description = doc.split("\n")[0] if doc else name.replace("_", " ")

                        self.register(
                            name=name,
                            description=f"{description}",
                            params={"input": {"type": "string"}},
                            func=func
                        )
            except ModuleNotFoundError:
                continue

# 전역 인스턴스
registry = ToolRegistry()

# 자동 등록할 모듈 목록 지정
builtin_modules = [
    "tools.pdf_tool",
    "tools.rag_tool",
    "tools.txt_tool",
    "tools.report_formatter_tool",
]

registry.auto_register_builtin_tools(builtin_modules)
