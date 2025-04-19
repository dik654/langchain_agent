from models.llm import llm
import json
import re

class FormatTool():
    name = "format_report"
    description = "보고서 내용을 JSON 형태로 포매팅 (본문 제목과 소제목은 내용을 기반으로 동적으로 생성)"
    
    def _run(self, summary_text: str):
        system_prompt = """
        다음 보고서 내용을 바탕으로 아래 JSON 형식으로 포매팅하세요.

        지침:
        - 보고서의 "title", "author", "date"는 보고서 내용을 참고하여 가장 적절한 값을 선택하거나 생성하세요.
        - "본문" 섹션의 제목과 소제목들은 보고서 내용을 바탕으로 가장 적절한 제목을 동적으로 생성하세요.
        - 표나 그래프가 들어갈 위치는 "<table>" 또는 "<graph>"로 표시합니다.

        JSON 형식:
        {{
            "title": "<적절한 제목>",
            "author": "<적절한 저자>",
            "date": "<적절한 날짜>",
            "sections": [
                {{
                    "title": "요약",
                    "content": "<보고서의 핵심 요약>"
                }},
                {{
                    "title": "<본문의 적절한 제목>",
                    "content": "<본문 소개>",
                    "subsections": [
                        {{"title": "<소제목 1>", "content": "<내용 1>"}},
                        {{"title": "<소제목 2>", "content": "<내용 2>"}},
                        {{"title": "<소제목 3>", "content": "<table>"}},
                        {{"title": "<소제목 4>", "content": "<graph>"}},
                        {{"title": "<소제목 5>", "content": "<내용 5>"}}
                    ]
                }},
                {{
                    "title": "결론",
                    "content": "<결론 내용>"
                }}
            ]
        }}

        보고서 내용:
        {summary_text}
        """.strip()

        # formatted_json = llm.invoke(summary_text, system_prompt, 0.2)
        formatted_json = llm.invoke("제타큐브는 탈중앙화 인프라 회사입니다", system_prompt, 0.2)
        print(formatted_json)
        
        return formatted_json

def safe_parse_json_from_output(output: str) -> dict:
    """LLM 응답에서 유효한 JSON만 추출 (백틱 없는 경우 포함)"""

    # 1. 코드블록 ```json { ... } ``` 형식
    match = re.search(r"```json\s*([\s\S]+?)\s*```", output)
    if match:
        json_str = match.group(1)
        return json.loads(json_str)

    # 2. 'json\n{...}' 형식 (백틱 없이 LLM이 내보낸 경우)
    match = re.search(r"json\s*\n\s*({[\s\S]+})", output)
    if match:
        json_str = match.group(1)
        return json.loads(json_str)

    # 3. 그냥 전체 문자열 자체가 JSON일 가능성
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        pass

    # 4. 실패 시
    raise ValueError("유효한 JSON 블록을 찾을 수 없습니다.")
        
def report_formatting(state: dict) -> dict:
    """리포트 형식에 맞게 출력을 변환합니다."""
    plan_index = state.get('plan_index', 0)
    summary_text = state.get("summary_text", "")
    format_tool = FormatTool()

    max_retries = 3
    retry_count = 0
    formatted_report = None
    last_error = None

    while retry_count < max_retries:
        llm_output = format_tool._run(summary_text)
        content = ""
        if isinstance(llm_output, dict):
            content = llm_output.get("content") or llm_output.get("reasoning_content") or ""
        elif isinstance(llm_output, str):
            content = llm_output
        else:
            content = str(llm_output)

        try:
            if not content or not isinstance(content, str):
                raise ValueError("LLM 응답에 content가 없거나 문자열이 아님")
            formatted_report = safe_parse_json_from_output(content)
            break  # 성공했으니 루프 탈출
        except Exception as e:
            last_error = str(e)
            retry_count += 1
            print(f"[RETRY] JSON 파싱 실패 ({retry_count}/{max_retries}) → {last_error}")

    if formatted_report is None:
        formatted_report = {"error": f"최대 재시도 도달: {last_error}"}

    formatted_state = {
        **state,
        "output": formatted_report,
        "status": "🧮 report_formatting 도구 실행 완료",
        "plan_index": plan_index + 1,
    }

    print(f"[DEBUG] report_formatting 실행됨: {plan_index}", flush=True)

    return formatted_state
