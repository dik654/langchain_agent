import asyncio
from graph.flow import build_graph

async def test_workflow():
    graph_executor = build_graph()

    print("🚀 그래프 실행 시작...\n")

    async for step in graph_executor.astream({
        "input": "회사의 내부 감사 보고서를 자동으로 생성해줘."
    }):
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

        # ✅ 마지막 finalize 단계일 때 최종 메시지 출력
        if step.get("__next__") == "finalize":
            print("\n🎉 최종 결과:")
            final_output = step.get("output")
            if isinstance(final_output, str):
                print(f"📝 {final_output}")
            elif isinstance(final_output, dict):
                message = final_output.get("message") or final_output.get("pdf_path") or "✅ 모든 작업이 완료되었습니다."
                print(f"📝 {message}")
            else:
                print("📝 ✅ 모든 작업이 완료되었습니다.")

    print("\n✅ 실행 완료")

if __name__ == "__main__":
    asyncio.run(test_workflow())
