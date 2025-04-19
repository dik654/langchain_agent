def analyze_intent(state: dict) -> dict:
    plan = state.get("plan", [])
    index = state.get("plan_index", 0)
    print(f"[DEBUG] 🔍 analyze_intent 실행됨: index={index}, plan={plan}")

    if index < len(plan):
        intent = plan[index]
        return {
            **state,
            "intent": intent,
            "status": f"🧠 계획에 따라 intent 설정: {intent}"
        }

    return {
        **state,
        "intent": "none",
        "status": "ℹ️ 더 이상 실행할 계획 없음, finalize로 이동합니다."
    }
