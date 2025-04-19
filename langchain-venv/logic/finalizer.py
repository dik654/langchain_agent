# from typing import Dict

# def finalize_answer(state: Dict) -> Dict:
#     intent = state.get("intent")
#     output = state.get("output")
#     status = state.get("status", "")

#     if not output and intent == "none":
#         user_input = state.get("input", "")

#         result = llm.invoke(user_input, system_prompt)
#         output = result.get("content") if isinstance(result, dict) else result.content

#     elif not output:
#         output = "⚠️ 도구 실행 결과가 없습니다."

#     elif isinstance(output, dict):
#         output = "\n".join(f"{k}: {v}" for k, v in output.items())

#     elif isinstance(output, list):
#         output = "\n".join(str(v) for v in output)

#     final_output = "\n\n".join([
#         "🎉 모든 작업이 완료되었습니다.",
#         status,
#         output
#     ])

#     print(f"[FINALIZE DEBUG] 최종 출력:\n{final_output}")

#     return {
#         **state,
#         "output": final_output,
#         "status": "✅ 흐름 종료"
#     }

# logic/finalizer.py

def finalize_answer(state: dict) -> dict:
    outputs = state.get("outputs", [])
    final_output = outputs[-1] if outputs else {}

    message = "🎉 모든 작업이 완료되었습니다."

    if isinstance(final_output, dict):
        # PDF 결과
        if "pdf_path" in final_output:
            message = f"✅ PDF 보고서가 생성되었습니다!\n📄 경로: {final_output['pdf_path']}"

        # RAG 결과
        elif "summary" in final_output:
            message = f"🧠 요약 완료:\n{final_output['summary']}"

        # 오류 메시지
        elif "error" in final_output:
            message = f"❌ 오류 발생: {final_output['error']}"

        # 그 외 dict 결과
        else:
            message = f"📋 결과:\n{final_output}"

    elif isinstance(final_output, str):
        message = final_output  # 예: "🔍 RAG 실행 결과 (모킹)"

    return {
        **state,
        "status": "✅ 흐름 종료",
        "output": message
    }

