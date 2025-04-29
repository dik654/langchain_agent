# tools/meeting_formatter_tool.py

import re
import json
from models.llm import llm


class MeetingFormatTool:
    name = "format_meeting_note"

    def _run(self, raw_meeting_note: str):
        system_prompt = f"""
당신은 자유 형식 회의 요약을 **엄격하게 구조화된 JSON**으로 변환하는 회의록 포매팅 도우미입니다.

🧠 작업 목표:
- 입력된 회의 내용을 분석하고,
- 아래 형식에 **정확히 일치하는 JSON**만 출력하세요.

⚠️ 반드시 지킬 규칙:
- 절대로 마크다운(```json), 설명, 기타 텍스트를 포함하지 마세요.
- **순수 JSON만** 출력하세요 (코드 블록 없이).
- 모든 키와 값은 쌍따옴표(")로 감싸야 합니다.
- 누락된 필드는 절대 생략하지 말고, 입력에서 추론해서 채우세요.

JSON format:{{
  "title": "필소굿 서비스 안정성 회의",
  "datetime": "2025년 2월 20일 오후 2시",
  "location": "서울 본사 회의실",
  "attendees": ["김민수", "이서연", "박지훈", "정유나"],
  "agenda": ["트래픽 급증 대응 방안", "서버 이중화 정책 논의"],
  "summary": "회의에서는 두 가지 주요 안건에 대해 논의하였고, 실행 계획 및 책임자 분담이 완료되었습니다.",
  "decisions": [
    "정유나 팀: 3월까지 자동 확장 계획 수립",
    "이서연 팀: Q2부터 이중화 적용 시작",
    "김민수, 박지훈: 점검 회의 주최"
  ],
  "recorder": "박지훈"
}}

🎯 다시 한 번 강조합니다:
- **딱 위 구조와 키를 사용하세요**
- **JSON 이외의 설명은 절대 포함하지 마세요**

📨 입력 회의 요약:
{raw_meeting_note}
""".strip()


        return llm.invoke(raw_meeting_note, system_prompt, temperature=0.5)


def safe_parse_meeting_json(output: str) -> dict:
    """LLM 응답에서 JSON 블록만 추출 후 파싱"""
    match = re.search(r"```json\s*([\s\S]+?)\s*```", output)
    json_text = match.group(1).strip() if match else output.strip()
    return json.loads(json_text)


def validate_meeting_json(parsed: dict):
    required = [
        "title", "datetime", "location",
        "attendees", "agenda", "summary",
        "decisions", "recorder"
    ]
    missing = [f for f in required if f not in parsed]
    if missing:
        raise ValueError(f"❌ 필수 필드 누락: {', '.join(missing)}")


async def formatting_meeting(state: dict, send_event=None) -> dict:
    plan_index = state.get("plan_index", 0)
    raw = state.get("summary_text") or state.get("user_query") or ""

    if not raw:
        return {
            **state,
            "output": {"error": "❌ 회의 요약 내용이 비어 있어 포매팅할 수 없습니다."},
            "status": "❌ formatting_meeting 실패",
            "plan_index": plan_index + 1
        }

    if send_event:
        await send_event("📝 회의록 JSON 생성 중...")

    formatter = MeetingFormatTool()
    last_err = ""
    for attempt in range(3):
        try:
            resp = formatter._run(raw)
            parsed = safe_parse_meeting_json(resp if isinstance(resp, str) else str(resp))
            validate_meeting_json(parsed)
            return {
                **state,
                "output": parsed,
                "status": "📋 회의록 포매팅 완료",
                "plan_index": plan_index + 1
            }
        except Exception as e:
            last_err = str(e)
            print(f"[RETRY {attempt + 1}] JSON 파싱 또는 필드 검증 실패: {last_err}")

    return {
        **state,
        "output": {"error": f"❌ 회의록 포매팅 실패: {last_err}"},
        "status": "❌ formatting_meeting 실패",
        "plan_index": plan_index + 1
    }
