import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from tools.tool_registry import registry

# 외부 MCP 서버 주소
MCP_SERVER_NAME = "remote_mcp"
MCP_SERVER_URL = "http://210.123.77.173:3600/sse"

async def register_remote_mcp():
    print(f"[🔌] MCP 연결 시도: {MCP_SERVER_URL}")
    async with MultiServerMCPClient({
        MCP_SERVER_NAME: {
            "url": MCP_SERVER_URL,
            "transport": "sse"
        }
    }) as client:
        tools = client.get_tools()
        print(f"[📦] MCP 서버 '{MCP_SERVER_NAME}'에서 {len(tools)}개 툴 로드됨")

        for tool in tools:
            registry.register(
                name=tool.name,
                description=tool.description,
                params=tool.args_schema.schema().get("properties", {}),
                func=tool.coroutine
            )
            print(f"[✅] 툴 등록됨: {tool.name}")

        print("[🎉] MCP 툴 전체 등록 완료")

if __name__ == "__main__":
    asyncio.run(register_remote_mcp())
