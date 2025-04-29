import os
import shutil
import subprocess
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from utils.stream_formatter import stream_spinner

async def generate_report_pdf(state: dict, send_event=None) -> dict:
    """이 도구는 구조화된 JSON 데이터를 기반으로 리포트 PDF 문서를 생성합니다."""

    plan_index = state.get("plan_index", 0)
    report_data = state.get("json_data")
    if not isinstance(report_data, dict) or "sections" not in report_data:
        return {
            **state,
            "output": "❌ PDF 생성 실패: 리포트 구조가 유효하지 않음",
            "status": "PDF 생성:",
            "plan_index": state.get("plan_index", 0) + 1,
        }
    print("~~~~~")
    print(report_data)

    print(f"[DEBUG] generate_pdf 실행됨: {plan_index}", flush=True)
    if send_event:
        async for chunk in stream_spinner("내부 문서 검색 중..."):
            await send_event(chunk)
    if not isinstance(report_data, dict) or "sections" not in report_data:
        return {
            **state,
            "output": "❌ PDF 생성 실패: 생성한 구조가 유효하지 않습니다.",
            "status": "PDF 생성",
            "plan_index": plan_index + 1,
        }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("outputs", "pdf")
    os.makedirs(output_dir, exist_ok=True)

    base_filename = f"report_{timestamp}"
    tex_path = os.path.join(output_dir, f"{base_filename}.tex")
    pdf_path = os.path.join(output_dir, f"{base_filename}.pdf")
    logo_src = os.path.join("tools", "company_logo.png")
    logo_dst = os.path.join(output_dir, "company_logo.png")

    try:
        # 템플릿 렌더링 및 .tex 저장
        env = Environment(loader=FileSystemLoader("tools"))
        template = env.get_template("report_template.tex")
        rendered = template.render(**report_data)

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(rendered)

        # 이미지 복사
        if os.path.exists(logo_src):
            shutil.copyfile(logo_src, logo_dst)
        else:
            print(f"[WARN] 회사 로고 이미지 없음: {logo_src}")

        # PDF 컴파일 (2-pass)
        for _ in range(2):
            subprocess.run([
                "xelatex",
                "-output-directory", output_dir,
                "-interaction=nonstopmode",  # 중간 에러로 멈추지 않도록
                tex_path
            ], check=True)

        print(f"[INFO] PDF 생성 완료 → {pdf_path}", flush=True)

        return {
            **state,
            "output": "▫️▫️⚙️ pdf 파일 배달하는 중",
            "pdf_path": [{
                "pdf_path": os.path.abspath(pdf_path),
                "filename": os.path.basename(pdf_path)
            }],
            "status": "📄 PDF 파일 생성:\n\n",
            "plan_index": plan_index + 1,
        }

    except Exception as e:
        log_path = os.path.join(output_dir, f"{base_filename}.log")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                last_lines = f.readlines()[-30:]
            print("[LaTeX 로그 요약]")
            print("".join(last_lines))
        return {
            **state,
            "output": {"error": f"❌ PDF 생성 중 오류: {str(e)}"},
            "status": "PDF 생성",
            "plan_index": plan_index + 1,
        }

    finally:
        # 중간 파일 정리 (.tex, .aux, .log, .out, toc)
        for ext in [".tex", ".aux", ".log", ".out", ".toc"]:
            try:
                os.remove(os.path.join(output_dir, f"{base_filename}{ext}"))
            except FileNotFoundError:
                pass

        # 로고도 삭제 (복사된 파일만 삭제)
        try:
            os.remove(logo_dst)
        except FileNotFoundError:
            pass

def preprocess_meeting_data(meeting: dict) -> dict:
    """LaTeX에서 사용 가능한 형태로 회의 데이터를 전처리"""
    def join_lines(items):
        return r"\\newline ".join(items) if isinstance(items, list) else items

    return {
        "title": meeting.get("title", ""),
        "datetime": meeting.get("datetime", ""),
        "location": meeting.get("location", ""),
        "attendees": ", ".join(meeting.get("attendees", [])),
        "agenda": join_lines(meeting.get("agenda", [])),
        "summary": meeting.get("summary", ""),
        "decisions": join_lines(meeting.get("decisions", [])),
        "recorder": meeting.get("recorder", "")
    }


async def generate_meeting_pdf(state: dict, send_event=None) -> dict:
    """회의록 JSON 데이터를 기반으로 LaTeX PDF 생성"""
    print("[aa]:"+state)
    plan_index = state.get("plan_index", 0)
    meeting_data = state.get("output")

    print(f"[DEBUG] generate_meeting_pdf 실행됨: {plan_index}", flush=True)

    if send_event:
        async for chunk in stream_spinner("회의록 PDF 생성 중..."):
            await send_event(chunk)

    if not isinstance(meeting_data, dict) or "title" not in meeting_data:
        return {
            **state,
            "output": {"error": "❌ PDF 생성 실패: 회의록 데이터에 필수 필드가 없음"},
            "status": "PDF 생성",
            "plan_index": plan_index + 1,
        }

    # 전처리된 데이터 준비
    data = preprocess_meeting_data(meeting_data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("outputs", "pdf")
    os.makedirs(output_dir, exist_ok=True)

    base_filename = f"meeting_{timestamp}"
    tex_path = os.path.join(output_dir, f"{base_filename}.tex")
    pdf_path = os.path.join(output_dir, f"{base_filename}.pdf")
    logo_src = os.path.join("tools", "company_logo.png")
    logo_dst = os.path.join(output_dir, "company_logo.png")

    try:
        # 템플릿 렌더링
        env = Environment(loader=FileSystemLoader("tools"))
        template = env.get_template("meeting_template.tex")
        rendered = template.render(**data)

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(rendered)

        # 로고 복사
        if os.path.exists(logo_src):
            shutil.copyfile(logo_src, logo_dst)
        else:
            print(f"[WARN] 회사 로고 이미지 없음: {logo_src}")

        # PDF 컴파일 2회
        for _ in range(2):
            subprocess.run([
                "xelatex",
                "-output-directory", output_dir,
                "-interaction=nonstopmode",
                tex_path
            ], check=True)

        print(f"[INFO] PDF 생성 완료 → {pdf_path}", flush=True)

        return {
            **state,
            "output": {
                "message": "📄 회의록 PDF 생성 완료",
                "pdf_path": os.path.abspath(pdf_path),
                "filename": os.path.basename(pdf_path)
            },
            "status": "📄 PDF 파일 생성 중입니다.",
            "plan_index": plan_index + 1,
        }

    except Exception as e:
        log_path = os.path.join(output_dir, f"{base_filename}.log")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                last_lines = f.readlines()[-30:]
            print("[LaTeX 로그 요약]")
            print("".join(last_lines))
        return {
            **state,
            "output": {"error": f"❌ PDF 생성 중 오류: {str(e)}"},
            "status": "❌ PDF 생성 실패",
            "plan_index": plan_index + 1,
        }

    finally:
        for ext in [".tex", ".aux", ".log", ".out", ".toc"]:
            try:
                os.remove(os.path.join(output_dir, f"{base_filename}{ext}"))
            except FileNotFoundError:
                pass
        try:
            os.remove(logo_dst)
        except FileNotFoundError:
            pass