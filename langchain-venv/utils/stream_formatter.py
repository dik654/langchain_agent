import json
import re
import asyncio
from typing import List, Tuple, Union, AsyncGenerator

spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

def chunk_text(text: str, max_length: int = 20) -> List[str]:
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

def make_chunk_event(content: str, finish: bool = False):
    data = {
        "id": "stream-001",
        "object": "chat.completion.chunk",
        "model": "deepseek-stream",
        "choices": [{"delta": {"content": content + ("\n" if not finish else "")}}]
    }
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_spinner(tool_name: str = "작업", frame_count: int = 10) -> AsyncGenerator[str, None]:
    for i in range(frame_count):
        frame = spinner_frames[i % len(spinner_frames)]
        yield make_chunk_event(f"{frame} '{tool_name}' 실행 중...")
        await asyncio.sleep(0.1)

def format_agent_step_for_stream(step: dict) -> List[str]:
    chunks = []
    for key, value in step.items():
        if isinstance(value, dict):
            status = value.get("status")
            if status:
                chunks.append(make_chunk_event(status))

            output = value.get("output")
            if output:
                for chunk in chunk_text(str(output), 40):
                    chunks.append(make_chunk_event(chunk))
    return chunks


def extract_user_and_source(messages: Union[List[dict], None]) -> Tuple[List[dict], str]:
    user_query = ""
    sources = []

    if not messages:
        return [], ""

    for m in reversed(messages):
        if m.get("role") == "user":
            content = m.get("content")
            if isinstance(content, str):
                user_query = content.strip()
                break
            elif isinstance(content, list):
                for part in reversed(content):
                    if isinstance(part, dict) and part.get("type") == "text":
                        user_query = part.get("text", "").strip()
                        break
                if user_query:
                    break

    for m in messages:
        if m.get("role") != "system":
            continue
        content = m.get("content", "")
        context_match = re.search(r"<context>(.*?)</context>", content, re.DOTALL | re.IGNORECASE)
        if not context_match:
            continue
        context_block = context_match.group(1)
        source_matches = re.findall(r'<source\s+id="([^"]*)">(.*?)</source>', context_block, re.DOTALL)
        for sid, body in source_matches:
            sources.append({"id": sid.strip(), "content": body.strip()})

    return sources, user_query
