def read_txt(state: dict) -> dict:
    """text 파일을 읽습니다."""
    print(f"[DEBUG] read_text 실행됨: {state.get('plan_index', 0)}", flush=True)
    return {
        **state,
        "output": f"🧮 txt 결과 (모킹)",
        "status": "🧮 txt 도구 실행 중",
        "plan_index": state.get("plan_index", 0) + 1,
    }