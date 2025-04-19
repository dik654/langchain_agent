# tools/search_tool.py

def use_rag(state: dict) -> dict:
    """관련 문서를 검색하고 요약합니다."""
    print(f"[DEBUG] use_rag 실행됨: {state.get('plan_index', 0)}", flush=True)
    return {
        **state,
        "output": f"🔍 RAG 실행 결과 (모킹)",
        "status": "🔍 RAG 실행 중",
        "plan_index": state.get("plan_index", 0) + 1,
    }
