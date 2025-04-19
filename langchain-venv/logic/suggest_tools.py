# def suggest_available_tools(state: dict) -> dict:
#     tool_list = [
#         "- 🔍 검색 (search)",
#         "- 🧮 계산기 (calculator)",
#         "- 📄 문서 검색 (RAG)",
#         "- 🧠 파일 질의 (MCP)",
#         "- 🎨 이미지 생성 (image)"
#     ]
#     tool_description = "**사용 가능한 도구들:**\n" + "\n".join(tool_list)

#     return {
#         **state,
#         "status": "🛠 사용 가능한 도구를 소개합니다",
#         "tool_info": tool_description
#     }

from tools.tool_registry import registry

def suggest_available_tools(state: dict) -> dict:
    tools = registry.list()
    tool_info = "\n".join([f"- {name}: {meta['description']}" for name, meta in tools.items()])
    return {
        **state,
        "tool_info": tool_info,
        "status": "🧰 사용 가능한 툴을 분석했습니다."
    }