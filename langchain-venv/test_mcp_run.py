import asyncio
from tools.tool_registry import registry
from graph.flow import build_graph

# --- register the dummy MCP ---
def dummy_mcp_tool(state):
    return {"output": f"✅ dummy_mcp processed: {state['input']}"}

registry.register(
    "dummy_mcp",                                       # 툴 이름
    "A dummy MCP tool for testing end‑to‑end",         # description
    {"input": {"type": "string"}},                     # params 정의
    dummy_mcp_tool                                     # func
)

async def main():
    graph = build_graph()

    # --- 계획 강제 주입: dummy_mcp 만 실행 ---
    state = {
        "input": "hello world",
        "plan": ["dummy_mcp"],
        "plan_index": 0,
        "__next__": "dummy_mcp",
        "status": ""
    }

    print("🚀 그래프 실행 시작...\n")

    async for step in graph.astream(state):
        print("🧩 단계 상태:")
        for k, v in step.items():
            if k == "output":
                print(f"🔹 output: {v}\n")
            elif k == "status":
                print(f"🔸 status: {v}")
            elif k == "plan":
                print(f"📋 plan: {v}")
            elif k == "__next__":
                print(f"➡️ 다음: {v}")
            else:
                print(f"{k}: {v}")
        print("-" * 40)

    # ✅ 마지막 상태값 받아서 output 출력
    final_state = step
    final_output = final_state.get("output", "❌ output 없음")
    print("\n🎉 최종 결과:")
    print(f"📝 {final_output}")
    print("\n✅ 실행 완료")

if __name__ == "__main__":
    asyncio.run(main())
