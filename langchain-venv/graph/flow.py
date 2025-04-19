# graph/flow.py

from typing import Callable, Dict, Any
from langgraph.graph import StateGraph
from logic.suggest_tools import suggest_available_tools
from logic.plan import plan_workflow
from logic.analyzer import analyze_intent
from logic.router import route_by_intent
from logic.finalizer import finalize_answer
from tools.tool_registry import registry

# ─────────────────────────────────────────────────────────────────────────────
# 1) 툴 실행 후 plan_index, __next__, status 자동 갱신 래퍼
# ─────────────────────────────────────────────────────────────────────────────
def wrap_tool(func: Callable[[Dict[str, Any]], Dict[str, Any]], name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        result = func(state)
        outputs = state.get("outputs", [])
        if "output" in result:
            outputs = outputs + [result["output"]]

        plan = state.get("plan", [])
        idx = state.get("plan_index", 0) + 1
        next_tool = plan[idx] if idx < len(plan) else "finalize"

        return {
            **state,
            **result,
            "outputs": outputs,
            "plan_index": idx,
            "__next__": next_tool,
            "status": f"✅ '{name}' 완료 → 다음툴: {next_tool}",
        }
    return node_fn

# ─────────────────────────────────────────────────────────────────────────────
# 2) 그래프 빌드
# ─────────────────────────────────────────────────────────────────────────────
def build_graph():
    print("[DEBUG] ✅ 그래프 생성 시작")
    graph = StateGraph(state_schema=dict)

    # — 기본 노드 등록 —
    core_nodes = {
        "suggest_tools": suggest_available_tools,
        "plan": plan_workflow,
        "analyze": analyze_intent,
        "route": route_by_intent,
        "finalize": finalize_answer,
    }
    for name, fn in core_nodes.items():
        graph.add_node(name, fn)
    print("[DEBUG] ✅ 기본 노드 등록 완료")

    # — 내장 툴 & MCP 툴 등록 헬퍼 함수 —
    def register_tool(name: str, fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        node = wrap_tool(fn, name)
        graph.add_node(name, node)
        graph.add_edge(name, "analyze")
        print(f"[DEBUG] ➕ 툴 노드 추가: {name}")

    # ① 내장 툴
    from tools.pdf_tool              import generate_pdf
    from tools.rag_tool              import use_rag
    from tools.txt_tool              import read_txt
    from tools.report_formatter_tool import report_formatting

    builtin_tools: Dict[str, Callable] = {
        "generate_pdf": generate_pdf,
        "use_rag": use_rag,
        "read_txt": read_txt,
        "report_formatting": report_formatting,
    }
    for name, fn in builtin_tools.items():
        register_tool(name, fn)

    # ② MCP 툴
    for tool_name in registry.list().keys():
        if tool_name in builtin_tools:
            continue

        # 클로저가 tool_name 을 바인딩하도록 기본 인자 사용
        def make_mcp(name: str):
            def mcp_tool(state: Dict[str, Any]) -> Dict[str, Any]:
                out = registry.run(name, {"input": state["input"]})
                return {"output": out, "status": f"🔧 MCP '{name}' 완료"}
            return mcp_tool

        register_tool(tool_name, make_mcp(tool_name))

    # — 흐름 연결 —
    graph.set_entry_point("suggest_tools")
    graph.add_edge("suggest_tools", "plan")
    graph.add_edge("plan",          "analyze")
    graph.add_edge("analyze",       "route")
    graph.add_conditional_edges("route", lambda state: state.get("__next__"))
    graph.set_finish_point("finalize")

    print("[DEBUG] ✅ 그래프 구성 완료")
    return graph.compile()
