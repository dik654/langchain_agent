import re
from typing import Dict
from models.llm import llm  # LLM 프록시 함수
from utils.stream_formatter import stream_spinner

async def plan_workflow(state: Dict, send_event=None) -> Dict:
    tool_info = state.get("tool_info", "")
    user_input = state.get("user_query", "")

    available_tools = set()
    for line in tool_info.strip().splitlines():
        clean_line = line.strip().lstrip("-•").strip()
        tool_name = clean_line.split(":")[0].strip()
        if tool_name:
            available_tools.add(tool_name)

    # ✅ 키워드 기반 자동 분기 (우선 적용)
    meeting_keywords = ["회의:", "회의록", "회의 내용 정리", "회의 PDF", "회의록 PDF", "회의 결과 PDF"]
    if any(keyword in user_input for keyword in meeting_keywords):
        plan_lines = ["formatting_meeting", "generate_meeting_pdf"]
        return {
            **state,
            "plan": plan_lines,
            "plan_index": 0,
            "__next__": plan_lines[0],
            "status": "🧭 키워드 기반 자동 계획 설정됨: formatting_meeting → generate_meeting_pdf"
        }

    max_retries = 3
    retry_count = 0

    # LLM용 프롬프트 정의
    system_prompt_base = f"""
    chat history를 처리하거나, 어떤 도구도 필요 없는 경우 아무것도 출력하지 마세요(빈 응답).
    사용자가 '회의록' 또는 '회의 내용', '회의 결과', '회의 요약', '회의 내용 정리', '회의 PDF' 등을 요청한 경우 'formatting_meeting' → 'generate_meeting_pdf' 순서를 출력하세요.
    사용자가 '보고서', '리포트', '분석 문서', 'PDF 리포트'를 요청한 경우 'use_rag' → 'formatting_report' → 'generate_report_pdf' 순서를 출력하세요.

    출력 형식 예시:
    formatting_meeting
    generate_meeting_pdf

    [사용 가능한 도구 목록]
    {tool_info}
    """.strip()

    plan_lines = []
    status_msg = ""

    while retry_count < max_retries:
        try:
            result = llm.invoke(user_input, system_prompt_base, temperature=0.63)
            content = result.get("content") if isinstance(result, dict) else getattr(result, "content", None)
        except Exception as e:
            return {
                **state,
                "plan": [],
                "plan_index": 0,
                "status": f"❌ 계획 수립 중 오류: {str(e)}"
            }

        if not content:
            return {
                **state,
                "plan": [],
                "plan_index": 0,
                "status": "❗ 계획 수립 실패: 빈 응답"
            }

        plan_text = content.split("</think>")[-1] if "</think>" in content else content
        plan_lines = [
            line.strip().lstrip("-•").strip()
            for line in plan_text.strip().splitlines() if line.strip()
        ]

        if not plan_lines:
            return {
                **state,
                "plan": ["finalize"],
                "plan_index": 0,
                "__next__": "finalize",
                "status": "ℹ️ 더 이상 실행할 툴이 없으므로 finalize로 이동합니다."
            }

        if plan_lines == ["finalize"]:
            return {
                **state,
                "plan": ["finalize"],
                "plan_index": 0,
                "__next__": "finalize",
                "status": "ℹ️ 툴 실행 없이 바로 finalize 처리됩니다."
            }

        unknown_tools = [tool for tool in plan_lines if tool not in available_tools]
        if unknown_tools:
            retry_msg = f"🔁 재시도 {retry_count+1}/{max_retries}: 사용 불가능한 도구 포함됨 → {', '.join(unknown_tools)}"
            print(f"[RETRY] {retry_msg}", flush=True)
            if send_event:
                async for chunk in stream_spinner(retry_msg):
                    await send_event(chunk)
            retry_count += 1
            continue
        else:
            status_msg = f"🧭 실행 계획 수립됨: {' → '.join(plan_lines)}"
            break

    if retry_count >= max_retries:
        fail_msg = "❌ 계획 수립 실패: 사용 불가능한 도구가 계속 포함됨"
        if send_event:
            async for chunk in stream_spinner(fail_msg):
                await send_event(chunk)
        return {
            **state,
            "plan": [],
            "plan_index": 0,
            "status": fail_msg
        }

    return {
        **state,
        "plan": plan_lines,
        "plan_index": 0,
        "status": status_msg
    }
