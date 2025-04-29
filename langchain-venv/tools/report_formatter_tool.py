from models.llm import llm
import json
import re

class ReportFormatTool():
    name = "format_report"
    
    def _run(self, summary_text: str):
        system_prompt = f"""
        당신은 구조화된 리포트를 생성하기 위한 포매팅 어시스턴트입니다.

        당신의 작업:
        - 제공된 리포트 원문을 읽고,
        - 아래 지침에 따라 필요한 내용을 적절히 특정한 JSON 구조로 포맷팅하세요.

        지침:
        - "title", "author", "date"는 리포트 내용을 기반으로 적절히 추출하거나 생성하세요.
        - 본문 섹션("sections")은 동적으로 생성된 제목과 간단한 도입 문장을 포함해야 합니다.
        - 본문에는 정확히 5개의 소주제를 포함해야 하며, 각 항목에는 다음이 포함되어야 합니다:
            - 의미 있는 "title"
            - 간결하고 명확한 "content" (2~3문장 내외)
        - 전체 리포트는 300~400단어 이내로 구성되어야 하며,
        - 지나치게 긴 문단이나 불필요한 설명은 피해야 합니다.

        요구되는 최종 JSON 출력 예시는 다음과 같습니다:
        ```json
        {{
        "title": "<적절한 리포트 제목>",
        "author": "<작성자 이름>",
        "date": "<작성 날짜>",
        "sections": [
            {{
            "title": "Summary",
            "content": "<리포트 요약>"
            }},
            {{
            "title": "<본문 제목>",
            "content": "<본문 도입 내용>",
            "subsections": [
                {{ "title": "<소주제 1 제목>", "content": "<내용 1>" }},
                {{ "title": "<소주제 2 제목>", "content": "<내용 2>" }},
                {{ "title": "<소주제 3 제목>", "content": "<내용 3>" }},
                {{ "title": "<소주제 4 제목>", "content": "<내용 4>" }},
                {{ "title": "<소주제 5 제목>", "content": "<내용 5>" }}
            ]
            }},
            {{
            "title": "Conclusion",
            "content": "<결론 또는 핵심 인사이트>"
            }}
        ]
        }}

        리포트 원문:
        {summary_text}
        """.strip()


        # formatted_json = llm.invoke(summary_text, system_prompt, 0.2)
        response = llm.invoke(summary_text, system_prompt, 0.63)
        
        if isinstance(response, dict):
            content = response.get("content") or response.get("reasoning_content") or ""
        else:
            content = str(response)
        
        return content

def safe_parse_json_from_output(output: str) -> dict:
    """LLM 응답에서 유효한 JSON만 추출"""

    # 문자열이 아닐 경우 str로 변환 (또는 실패 처리)
    if not isinstance(output, str):
        output = str(output)

    # 1. ```json ... ``` 코드 블록
    match = re.search(r"```(?:\s*json)?\s*([\s\S]+?)\s*```", output)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # 2. json\n{...}
    match = re.search(r"json\s*\n\s*({[\s\S]+})", output)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # 3. 전체가 JSON 문자열일 수 있음
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        pass

    # 4. 실패
    raise ValueError("❌ 유효한 JSON 블록을 찾을 수 없습니다.")

        
async def formatting_report(state: dict, send_event=None) -> dict:
    """이 도구는 리포트를 지정된 JSON 형식으로 포맷팅할 필요가 있을 때만 사용하세요."""

    plan_index = state.get('plan_index', 0)
    format_tool = ReportFormatTool()
    summary_text = state.get("summary_text")
    formatted_report = None

    # 1. summary_text 확보
    if not summary_text:
        output = state.get("output", {})
        if isinstance(output, dict):
            summary_text = output.get("summary")

        if not summary_text:
            for o in reversed(state.get("outputs", [])):
                if isinstance(o, dict) and o.get("source") == "use_rag":
                    summary_text = o.get("summary")
                    break

    if not summary_text:
        return {
            **state,
            "output": "❌ summary_text가 비어 있습니다.",
            "status": "❌ report_formatting 실패",
            "plan_index": plan_index + 1,
        }

    # 2. LLM 호출 및 파싱
    try:
        llm_output = format_tool._run(summary_text)
        raw_content = llm_output.get("content") if isinstance(llm_output, dict) else str(llm_output)
        formatted_report = safe_parse_json_from_output(raw_content)

    except Exception as e:
        return {
            **state,
            "output": {"error": f"❌ JSON 파싱 실패: {str(e)}"},
            "status": "❌ report_formatting 실패",
            "plan_index": plan_index + 1,
        }

    # 3. 유효성 검사
    if not isinstance(formatted_report, dict) or "sections" not in formatted_report:
        return {
            **state,
            "output": {"error": "❌ JSON 구조 오류: 'sections'가 없음"},
            "status": "❌ report_formatting 실패",
            "plan_index": plan_index + 1,
        }

    # 4. 정상 리턴
    return {
        **state,
        "output": "▫️▫️⚙️ report_formatting 도구 실행 중",
        "json_data": formatted_report,
        "status": "🧮 PDF에 맞춰 변환:\n\n",
        "plan_index": plan_index + 1,
        "__next__": "generate_report_pdf",
    }