from models.llm import llm  # LLM 프록시 함수

def generate_direct_answer(state: dict) -> dict:
    # """사용자 질문에 도구 없이 직접 답변합니다."""
    # print(f"[DEBUG] state 타입: {type(state)}, 값: {state}")

    # system_prompt = "다음 사용자의 질문에 도구 없이 직접 답변하세요."
    # user_input = state.get("input", "")

    # result = llm.invoke(user_input, system_prompt)
    # answer = result.get("content") if isinstance(result, dict) else result.content

    return {
        **state,
        "output": f"🧠 직접 응답:\n\n{answer}",
        "status": "📌 직접 응답 완료"
    }
