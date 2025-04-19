from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from models.schemas import ChatCompletionRequest
from tools.tool_registry import registry
from graph.flow import build_graph
import asyncio
import time
import json
import httpx
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools

app = FastAPI()
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

async def stream_response(prompt: str):
    yield 'data: ' + json.dumps({
        "id": "stream-001",
        "object": "chat.completion.chunk",
        "model": "deepseek-stream",
        "choices": [{"delta": {"role": "assistant"}}]
    }) + '\n\n'

    async for step in graph_executor.stream({"input": prompt}):
        if "status" in step:
            yield 'data: ' + json.dumps({
                "choices": [{"delta": {"content": step["status"]}}]
            }) + '\n\n'

        if "output" in step:
            output = ensure_think_format(step["output"])
            for chunk in output.split():
                yield 'data: ' + json.dumps({
                    "choices": [{"delta": {"content": chunk + " "}}]
                }) + '\n\n'

    yield 'data: ' + json.dumps({
        "choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}]
    }) + '\n\n'
    yield 'data: [DONE]\n\n'

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    user_messages = [m for m in request.messages if m.role == "user"]
    system_messages = [m for m in request.messages if m.role == "system"]

    user_input = user_messages[-1].content if user_messages else ""
    system_instruction = system_messages[-1].content if system_messages else ""

    prompt = f"**[시스템 지시]**\n{system_instruction.strip()}\n\n**[질문]**\n{user_input.strip()}"

    if request.stream:
        return StreamingResponse(stream_response(prompt), media_type="text/event-stream")
    else:
        result = await graph_executor.invoke({"input": prompt})
        output = ensure_think_format(result["output"])
        return {
            "id": "chatcmpl-001",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": output},
                "finish_reason": "stop"
            }]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)