# tools/tool_registry.py 수정 및 registry에 기본 툴 포함

import importlib
import inspect
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
        sig = inspect.signature(func)

        # ✅ state 기반 함수라면 state 그대로
        if "state" in sig.parameters:
            return func(args)

        # ✅ 아닌 경우에는 input만 꺼내서
        if "input" not in args:
            raise KeyError("Missing 'input' key in args for input-based tool.")
        return func(args["input"])

    def auto_register_builtin_tools(self, module_paths):
        for module_path in module_paths:
            try:
                mod = importlib.import_module(module_path)
                print(f"[REGISTRY] 모듈 로드됨: {module_path}")

                for name, func in inspect.getmembers(mod):
                    if not (inspect.isfunction(func) or inspect.iscoroutinefunction(func)):
                        continue

                    if name.startswith(("generate_", "use_", "formatting_")):
                        print(f"[REGISTRY] ✅ 함수 발견 및 등록 시도: {name}")
                        doc = inspect.getdoc(func)
                        description = doc if doc else name.replace("_", " ")

                        self.register(
                            name=name,
                            description=f"{description}",
                            params={"input": {"type": "state"}},
                            func=func
                        )
            except ModuleNotFoundError as e:
                print(f"[REGISTRY] ❌ 모듈 로딩 실패: {module_path} → {e}")
                continue


# 전역 인스턴스
registry = ToolRegistry()

# 자동 등록할 모듈 목록 지정
builtin_modules = [
    "tools.pdf_tool",
    "tools.rag_tool",
    "tools.report_formatter_tool",
]

registry.auto_register_builtin_tools(builtin_modules)
