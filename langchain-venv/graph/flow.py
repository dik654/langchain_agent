# from typing import Callable, Dict, Any
# from langgraph.graph import StateGraph
# from logic.suggest_tools import suggest_available_tools
# from logic.plan import plan_workflow
# from logic.analyzer import analyze_intent
# from logic.router import route_by_intent
# from logic.finalizer import finalize_answer
# from tools.tool_registry import registry
# import asyncio
# import inspect

# def wrap_tool(func: Callable[[Dict[str, Any]], Any], name: str) -> Callable[[Dict[str, Any]], Any]:
#     async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
#         print(f"[DEBUG] 🟢 '{name}' 실행됨")
#         result = await func(state)
#         print(f"[DEBUG] result type: {type(result)}")
#         outputs = state.get("outputs", [])
#         if "output" in result:
#             outputs.append(result["output"])
#         plan = state.get("plan", [])
#         idx = state.get("plan_index", 0) + 1
#         next_tool = plan[idx] if idx < len(plan) else "finalize"
#         return {
#             **state,
#             **result,
#             "outputs": outputs,
#             "plan_index": idx,
#             "__next__": next_tool,
#             "status": f"✅ '{name}' 완료 → 다음툴: {next_tool}"
#         }
#     return node_fn


# def build_graph():
#     print("[DEBUG] ✅ 그래프 생성 시작")
#     graph = StateGraph(state_schema=dict)

#     # ─ 기본 노드 등록 ─
#     core_nodes = {
#         "suggest_tools": suggest_available_tools,
#         "plan": plan_workflow,
#         "analyze": analyze_intent,
#         "route": route_by_intent,
#         "finalize": finalize_answer,
#     }
#     for name, fn in core_nodes.items():
#         graph.add_node(name, fn)
#     print("[DEBUG] ✅ 기본 노드 등록 완료")

#     # ─ 툴 등록 함수 ─
#     def register_tool(name: str, fn: Callable[[Dict[str, Any]], Any]):
#         graph.add_node(name, wrap_tool(fn, name))
#         graph.add_edge(name, "analyze")
#         print(f"[DEBUG] ➕ 툴 노드 추가: {name}")

#     # ─ ① 내장 툴 ─
#     from tools.pdf_tool import generate_report_pdf, generate_meeting_pdf
#     from tools.rag_tool import use_rag
#     from tools.meeting_formatter_tool import formatting_meeting
#     from tools.report_formatter_tool import formatting_report

#     builtin_tools: Dict[str, Callable] = {
#         "generate_report_pdf": generate_report_pdf,
#         "generate_meeting_pdf": generate_meeting_pdf,
#         "use_rag": use_rag,
#         "formatting_meeting": formatting_meeting,  # 🔁 이름 일치시킴
#         "formatting_report": formatting_report,
#     }

#     for name, fn in builtin_tools.items():
#         register_tool(name, fn)

#     # ─ ② MCP 툴 ─
#     for tool_name in registry.list().keys():
#         if tool_name in builtin_tools:
#             continue  # ✅ 중복 방지

#         def make_mcp(name: str):
#             async def mcp_tool(state: Dict[str, Any]) -> Dict[str, Any]:
#                 tool_sig = inspect.signature(registry.list()[name]["function"])
#                 if "state" in tool_sig.parameters:
#                     return await asyncio.to_thread(registry.run, name, state)
#                 else:
#                     return await asyncio.to_thread(registry.run, name, {"input": state.get("input", "")})
#             return mcp_tool

#         register_tool(tool_name, make_mcp(tool_name))

#     # ─ 흐름 구성 ─
#     graph.set_entry_point("suggest_tools")
#     graph.add_edge("suggest_tools", "plan")
#     graph.add_edge("plan", "analyze")
#     graph.add_edge("analyze", "route")
#     graph.add_conditional_edges("route", lambda state: state.get("__next__"))
#     graph.set_finish_point("finalize")

#     print("[DEBUG] ✅ 그래프 구성 완료")
#     return graph.compile()


from typing import Callable, Dict, Any
from langgraph.graph import StateGraph

from logic.finalizer import finalize_answer
from tools.pdf_tool import generate_report_pdf
from tools.rag_tool import use_rag
from tools.report_formatter_tool import formatting_report

def wrap_tool(func: Callable[[Dict[str, Any]], Any], name: str) -> Callable[[Dict[str, Any]], Any]:
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[DEBUG] 🟢 '{name}' 실행됨")
        result = await func(state)
        print(f"[DEBUG] result type: {type(result)}")

        outputs = state.get("outputs", [])
        outputs.append(result)  # ✅ 여기를 result["output"] → result로 바꿔야 함

        return {
            **state,
            **result,
            "outputs": outputs,
            "plan_index": state.get("plan_index", 0) + 1,
            "status": f"✅ 도구: '{name}' 실행 중... ",
        }
    return node_fn

def build_graph():
    print("[DEBUG] ✅ 그래프 생성 시작")
    graph = StateGraph(state_schema=dict)

    # 순차 실행: use_rag → formatting_report → generate_report_pdf → finalize
    graph.add_node("use_rag", wrap_tool(use_rag, "use_rag"))
    graph.add_node("formatting_report", wrap_tool(formatting_report, "formatting_report"))
    graph.add_node("generate_report_pdf", wrap_tool(generate_report_pdf, "generate_report_pdf"))
    graph.add_node("finalize", finalize_answer)

    # 순차적 흐름 연결
    graph.set_entry_point("use_rag")
    graph.add_edge("use_rag", "formatting_report")
    graph.add_edge("formatting_report", "generate_report_pdf")
    graph.add_edge("generate_report_pdf", "finalize")

    graph.set_finish_point("finalize")

    print("[DEBUG] ✅ 그래프 구성 완료 (순차 실행)")
    return graph.compile()
