import httpx
from utils.stream_formatter import stream_spinner

RAG_API_URL = "http://localhost:8002/v1/rag/context"

async def use_rag(state: dict, send_event=None) -> dict:
    """ZetaCube(회사), DePIN, 블록체인과 검색 요약 도구"""
    plan_index = state.get("plan_index", 0)
    query = state.get("user_query", "")

    print(f"[DEBUG] use_rag 실행됨 (plan_index={plan_index})", flush=True)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(RAG_API_URL, json={"query": query + ". 수치나 전문용어 등 쓸모있는 정보가 최대한 많이 포함된 내용을 우선 검색해주세요. 동일 단어가 반복하는 내용은 피해주세요. 페이지 숫자가 content에 들어간 것은 수치로 치지 마세요.", "k": 8,}, )
            resp.raise_for_status()
            data = resp.json()

            # RAGContextResponse의 구조에 맞게 파싱
            documents = data.get("retrieved_documents", [])
            top_k_contents = [doc.get("content", "") for doc in documents[:]]
            summary = "\n---\n".join(top_k_contents).strip()

    except Exception as e:
        summary = f"❌ RAG 호출 실패: {e}"

    print(summary)

    return {
        **state,
        "output": "▫️▫️⚙️ 내부 문서를 검토 중 입니다...",
        "summary_text": summary,
        "status": "🔍 내부 문서 검토:\n\n",
        "plan_index": plan_index + 1
    }
