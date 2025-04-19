def route_by_intent(state: dict) -> dict:
    plan = state.get("plan", [])
    plan_index = state.get("plan_index", 0)

    if plan_index >= len(plan):
        print("[ROUTER] 계획 종료 도달 → finalize 이동")
        return {**state, "__next__": "finalize"}

    intent = plan[plan_index]
    print(f"[ROUTER] 분기 예정 intent: {intent} (index: {plan_index})")

    return {
        **state,
        "intent": intent,
        "__next__": intent
    }
