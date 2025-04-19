import re
from typing import Dict
from models.llm import llm  # LLM 프록시 함수

def plan_workflow(state: Dict) -> Dict:
    tool_info = state.get("tool_info", "")
    user_input = state.get("input", "")

    system_prompt=f"""
위 질문에 답변하기 위해 사용해야 할 툴의 순서를 리스트로 만들어 주세요. 예시는 다음과 같습니다:
- pdf_tool
- rag_tool
- content_tool
- report_formatter_tool
- filesystem_tool

**[사용 가능한 툴 목록]**
{tool_info}

단순한 응답이 필요합니다. 툴 이름만 순서대로 한 줄씩 출력하세요.
    """.strip()

    result = llm.invoke(user_input, system_prompt)
    content = result["content"] if isinstance(result, dict) else result.content

    # 🔍 </think> 이후만 추출
    plan_lines = []
    if "</think>" in content:
        plan_text = content.split("</think>")[-1]
    else:
        plan_text = content

    # - bullet 형식 또는 줄 바꿈 기준 추출
    lines = plan_text.strip().splitlines()
    for line in lines:
        clean = line.strip().lstrip("-•").strip()
        if clean:
            plan_lines.append(clean)

    return {
        **state,
        "plan": plan_lines,
        "plan_index": 0,
        "status": f"🧭 실행 계획 수립됨: {' → '.join(plan_lines)}"
    }
