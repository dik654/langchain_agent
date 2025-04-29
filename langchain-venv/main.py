from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from models.schemas import ChatCompletionRequest
from tools.tool_registry import registry
from graph.flow import build_graph
from typing import List
import asyncio
import time
import json
import httpx
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from utils.stream_formatter import extract_user_and_source, make_chunk_event, format_agent_step_for_stream
from fastapi.staticfiles import StaticFiles
from models.llm import llm

app = FastAPI()
# PDF 파일 경로를 서빙할 디렉토리 등록
PDF_OUTPUT_DIR = "/home/filadmin/ai/langchain-venv/outputs/pdf"
app.mount("/static/pdf", StaticFiles(directory=PDF_OUTPUT_DIR), name="static-pdf")

graph_executor = build_graph()

# ---------- MCP 등록 ----------
@app.post("/mcp/register")
async def add_mcp_server(request: Request):
    body = await request.json()
    name = body.get("name")
    url = body.get("path")

    try:
        session = await ClientSession.create(base_url=url)
        tools = await load_mcp_tools(session)

        for tool in tools:
            registry.register(
                name=tool.name,
                description=tool.description,
                params=tool.args_schema.schema().get("properties", {}),
                func=tool.coroutine  # 실제 실행 연결됨
            )

        return {"message": f"MCP 서버 '{name}'에서 {len(tools)}개 툴 등록 완료"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------- Open WebUI MCP Tool Server ----------
@app.get("/openapi.json")
async def openapi_spec():
    return JSONResponse(registry.get_openapi_spec())

@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    data = await request.json()
    result = registry.run(tool_name, data)
    return {"result": result}

# ---------- OpenAI 호환 /v1/chat/completions ----------
def ensure_think_format(text: str) -> str:
    if "</think>" in text and "<think>" not in text:
        return "<think>\n" + text
    return text

# async def stream_response(prompt: str):
#     yield 'data: ' + json.dumps({
#         "id": "stream-001",
#         "object": "chat.completion.chunk",
#         "model": "deepseek-stream",
#         "choices": [{"delta": {"role": "assistant"}}]
#     }) + '\n\n'

#     async for step in graph_executor.astream({"input": prompt}):
#         if "status" in step:
#             yield 'data: ' + json.dumps({
#                 "choices": [{"delta": {"content": step["status"]}}]
#             }) + '\n\n'

#         if "output" in step:
#             output = ensure_think_format(step["output"])
#             for chunk in output.split():
#                 yield 'data: ' + json.dumps({
#                     "choices": [{"delta": {"content": chunk + " "}}]
#                 }) + '\n\n'

#     yield 'data: ' + json.dumps({
#         "choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}]
#     }) + '\n\n'
#     yield 'data: [DONE]\n\n'

async def stream_response(source_text: str, user_query: str, request: Request):
    yield make_chunk_event("")

    async for step in graph_executor.astream({"context": source_text, "user_query": user_query}):
        # ✂️ 클라이언트 연결 끊김 감지
        if await request.is_disconnected():
            print("🔌 클라이언트 연결 끊김: 스트리밍 중단됨")
            break

        for chunk in format_agent_step_for_stream(step):
            yield chunk

    yield make_chunk_event("", finish=True)



@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "Agentic-DeepSeek-R1",
                "object": "model",
                "created": 1744630404,
                "owned_by": "local",
                "permission": [
                    {
                        "id": "modelperm-local",
                        "object": "model_permission",
                        "created": 1744630404,
                        "allow_create_engine": False,
                        "allow_sampling": True,
                        "allow_logprobs": True,
                        "allow_view": True,
                        "allow_fine_tuning": False,
                        "organization": "*",
                        "is_blocking": False,
                    }
                ],
            }
        ],
    }

@app.post("/v1/chat/completions")
async def debug_endpoint(request: Request):
    print(request)
    body = await request.body()

    try:
        json_data = json.loads(body)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format."}

    messages = json_data.get("messages", [])

    # ✅ 1. 제목 생성 쿼리 필터링
    def is_title_or_tag_request(messages):
        if not messages:
            return False
        last_msg = messages[-1]
        if not isinstance(last_msg, dict):
            return False
        content = last_msg.get("content", "")
        return (
            # 제목 생성 요청
            ("Generate a concise, 3-5 word title" in content and "### Chat History" in content)
            or
            # 태그 요청
            ("Generate 1-3 broad tags" in content and "JSON format" in content and "### Chat History" in content)
        )

    if is_title_or_tag_request(messages):
        print("📛 제목/태그 생성 쿼리 감지 → 응답 생략 또는 고정 응답")
        return JSONResponse(content={
            "id": "chatcmpl-meta",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "Agentic-DeepSeek-R1",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": '{"title": "🤖 Chat Summary"}'},
                    "finish_reason": "stop"
                }
            ]
        })

    source_text, user_query = extract_user_and_source(messages)

    print("@SOURCE:", source_text)
    print("@QUERY:", user_query)

    return StreamingResponse(stream_response(source_text, user_query, request), media_type="text/event-stream")

# @app.post("/v1/chat/completions")
# async def chat_completions(
#     model: str = Form(...),
#     messages: str = Form(...),  # JSON string
#     temperature: float = Form(0.6),
#     files: List[UploadFile] = File(default=None)
# ):
#     print("!"+model)
#     print("!"+messages)
#     print("!"+temperature)
#     print("!"+files)
#     # 메시지를 파싱
#     import json
#     parsed_messages = json.loads(messages)

#     # 파일 내용 확인
#     file_contents = {}
#     if files:
#         for file in files:
#             content = await file.read()
#             file_contents[file.filename] = content.decode('utf-8', errors='ignore')

#     return {
#         "model": model,
#         "messages": parsed_messages,
#         "file_preview": {name: content[:200] for name, content in file_contents.items()}
#     }

# @app.post("/v1/chat/completions")
# async def chat_completions(request: ChatCompletionRequest):
#     print(request)
#     user_messages = [m for m in request.messages if m.role == "user"]
#     system_messages = [m for m in request.messages if m.role == "system"]

#     user_input = user_messages[-1].content if user_messages else ""
#     system_instruction = system_messages[-1].content if system_messages else ""

#     prompt = f"{user_input.strip()}"

#     # if request.stream:
#     #     return StreamingResponse(stream_response(prompt), media_type="text/event-stream")
#     # else:
#     #     result = await graph_executor.invoke({"input": prompt})
#     #     output = ensure_think_format(result["output"])
#     #     return {
#     #         "id": "chatcmpl-001",
#     #         "object": "chat.completion",
#     #         "created": int(time.time()),
#     #         "model": request.model,
#     #         "choices": [{
#     #             "index": 0,
#     #             "message": {"role": "assistant", "content": output},
#     #             "finish_reason": "stop"
#     #         }]
#     #     }
#     return StreamingResponse(stream_response(prompt), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)