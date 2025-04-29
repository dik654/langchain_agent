# from models.llm import llm
# from typing import Dict, Union
# import json

# def finalize_answer(state: Dict) -> Dict:
#     input_text = state.get("user_query", "") or state.get("input", "")
#     context = state.get("context", "")
#     outputs = state.get("outputs", [])

#     download_buttons = []
#     summarized_parts = []

#     # 외부에서 접근 가능한 URL 경로
#     STATIC_PDF_BASE_URL = "http://211.176.180.172:8001/static/pdf"

#     for o in outputs:
#         if isinstance(o, dict) and "pdf_path" in o and "filename" in o:
#             pdf_path = o["pdf_path"]
#             filename = o["filename"]

#             # 내부 경로를 외부 URL로 변환
#             if pdf_path.startswith("/home/filadmin/ai/langchain-venv/outputs/pdf"):
#                 relative_path = pdf_path.replace("/home/filadmin/ai/langchain-venv/outputs/pdf", "").lstrip("/")
#                 url_path = f"{STATIC_PDF_BASE_URL}/{relative_path}"

#                 button_html = f"""
# <a href="{url_path}" download="{filename}" style="
#     display: inline-block;
#     background-color: #4CAF50;
#     color: white;
#     padding: 8px 16px;
#     text-align: center;
#     text-decoration: none;
#     border-radius: 6px;
#     font-weight: bold;
#     margin-top: 10px;
# ">📄 PDF 다운로드</a>
# """
#                 download_buttons.append(button_html)
#         else:
#             summarized_parts.append(
#                 json.dumps(o, ensure_ascii=False, indent=2) if isinstance(o, dict) else str(o)
#             )

#     summarized_text = "\n".join(summarized_parts)
#     button_block = "\n".join(download_buttons)

#     if summarized_text:
#         prompt = f"""
#     다음은 사용 가능한 도구들을 통해 얻은 결과입니다.  
#     해당 정보를 바탕으로 사용자의 질문에 적절히 요약하여 응답해 주세요.

#     [사용자 질문]
#     {input_text}

#     [도구 출력 결과]
#     {summarized_text}
#     """.strip()
#     else:
#         prompt = f"""
#     아래 사용자 질문에 대해 **어떠한 도구도 사용하지 않고** 직접 응답해 주세요.  
#     간결하고 핵심적인 정보를 중심으로 대답해 주세요.

#     [사용자 질문]
#     {input_text}

#     [참고 문맥]
#     {context}
#     """.strip()

#     print("@@@@@ user_query:", input_text)
#     print("@@@@@ prompt:", prompt)

#     result = llm.invoke(input_text, prompt)
#     response = None
#     if isinstance(result, dict):
#         response = result.get("content")
#     elif hasattr(result, "content"):
#         response = result.content

#     if not response:
#         response = "❗답변 생성에 실패했습니다. 다시 시도해 주세요."

#     final_response = response + "\n\n" + button_block
#     return {
#         **state,
#         "output": final_response,
#         "status": "✅ 최종 응답 완료",
#     }

from typing import Dict
import json

def finalize_answer(state: Dict) -> Dict:
    outputs = state.get("pdf_path", [])
    download_buttons = []
    summarized_parts = []

    STATIC_PDF_BASE_URL = "http://192.168.10.1:8001/static/pdf"

    print(outputs)
    for o in outputs:
        if isinstance(o, dict) and "pdf_path" in o and "filename" in o:
            pdf_path = o["pdf_path"]
            filename = o["filename"]

            if pdf_path.startswith("/home/filadmin/ai/langchain-venv/outputs/pdf"):
                relative_path = pdf_path.replace("/home/filadmin/ai/langchain-venv/outputs/pdf", "").lstrip("/")
                url_path = f"{STATIC_PDF_BASE_URL}/{relative_path}"

                button_html = f"""
<a href="{url_path}" download="{filename}" style="
    display: inline-block;
    background-color: #4CAF50;
    color: white;
    padding: 8px 16px;
    text-align: center;
    text-decoration: none;
    border-radius: 6px;
    font-weight: bold;
    margin-top: 10px;
">📄 PDF 다운로드</a>
"""
                download_buttons.append(button_html)
        else:
            summarized_parts.append(
                json.dumps(o, ensure_ascii=False, indent=2) if isinstance(o, dict) else str(o)
            )

    button_block = "\n".join(download_buttons)

    # ✅ 여기에서 조건 처리
    if download_buttons:
        response = "- 모든 과정이 완료되었습니다. -"
    elif summarized_parts:
        response = "- 일부 결과만 요약되었습니다. -\n\n" + "\n".join(summarized_parts)
    else:
        response = "❗최종 결과를 출력할 수 없습니다."

    final_response = response + "\n\n" + button_block
    print(final_response)

    return {
        **state,
        "output": "",
        "status": final_response,
    }
