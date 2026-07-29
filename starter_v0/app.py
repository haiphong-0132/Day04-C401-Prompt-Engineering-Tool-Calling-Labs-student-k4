"""Giao diện Streamlit cho Research Agent của Day 04."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)


def redact(value: Any) -> Any:
    """Không hiển thị mẫu API key phổ biến trong trace hoặc bản tải xuống."""
    if isinstance(value, str):
        return re.sub(r"(?:sk|tvly|fc)-[A-Za-z0-9_-]{12,}", "[REDACTED]", value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def json_view(value: Any) -> str:
    return json.dumps(redact(value), ensure_ascii=False, indent=2, default=str)


def tool_result_summary(result: Any) -> str:
    """Trả về tóm tắt ngắn để không đẩy toàn bộ JSON lên màn hình."""
    if not isinstance(result, dict):
        return "Tool đã trả về kết quả."
    if result.get("error"):
        return f"Lỗi: {result['error']}"
    if isinstance(result.get("items"), list):
        return f"Hoàn tất · tìm thấy {len(result['items'])} kết quả."
    if result.get("awaiting_user"):
        return "Đang chờ người dùng bổ sung hoặc xác nhận."
    if result.get("status"):
        return f"Trạng thái: {result['status']}"
    return "Tool đã chạy xong."


def new_transcript(
    *, artifact: Any, provider: str, model: str | None, history_window: int, max_tool_rounds: int
) -> tuple[dict[str, Any], Path]:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(artifact.version), safe_slug(provider), timestamp])
    path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    return ({
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact),
        "provider": provider,
        "model": model,
        "system_prompt": "artifacts/system_prompt.md",
        "tools": "artifacts/tools.yaml",
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }, path)


def initialise_session(
    *, artifact: Any, provider: str, model: str | None, history_window: int, max_tool_rounds: int
) -> None:
    transcript, path = new_transcript(
        artifact=artifact,
        provider=provider,
        model=model,
        history_window=history_window,
        max_tool_rounds=max_tool_rounds,
    )
    st.session_state.history = []
    st.session_state.display_messages = []
    st.session_state.transcript = transcript
    st.session_state.transcript_path = path
    st.session_state.settings_key = (provider, model, artifact.artifact_version, history_window, max_tool_rounds)


def render_trace(turn: dict[str, Any]) -> None:
    for round_record in turn.get("rounds", []):
        label = f"Vòng {round_record['round']} · {len(round_record.get('tool_calls', []))} lần gọi tool"
        with st.expander(label, expanded=False):
            if round_record.get("assistant_text"):
                st.caption("Phản hồi từ model")
                st.write(round_record["assistant_text"])
            for index, event in enumerate(round_record.get("tool_results", []), start=1):
                args = event.get("args", {})
                result = event.get("result", {})
                arg_text = ", ".join(f"`{key}`={value!r}" for key, value in args.items()) or "không có"
                st.markdown(f"**{index}. `{event['tool']}`** — {tool_result_summary(result)}")
                st.caption(f"Tham số: {arg_text}")
                detail_key = f"trace_detail_{turn.get('turn_index', 0)}_{round_record['round']}_{index}"
                if st.toggle("Hiện JSON chi tiết", key=detail_key):
                    st.code(json_view({"args": args, "result": result}), language="json")
            if not round_record.get("tool_calls"):
                st.caption("Không gọi tool — model đã trả lời trực tiếp.")


st.set_page_config(page_title="Research Agent Lab", page_icon="🔎", layout="wide")
st.title("🔎 Research Agent Lab")
st.caption("Trò chuyện research trực tiếp, theo dõi được tool trace và lưu bằng chứng transcript.")

with st.sidebar:
    st.header("Cấu hình chạy")
    provider_name = st.selectbox("Provider", ["openai", "nvidia", "openrouter", "anthropic", "gemini"], index=0)
    api_key_input = st.text_input(f"{provider_name.upper()} API Key", type="password", placeholder="Paste API Key here (optional)")
    model_override = st.text_input("Ghi đè model (không bắt buộc)", placeholder="Dùng model mặc định của provider")
    version = st.text_input("Phiên bản artifact", value="v3")
    history_window = st.slider("Số cặp hội thoại lưu ngữ cảnh", min_value=1, max_value=10, value=5)
    max_tool_rounds = st.slider("Số vòng gọi tool tối đa", min_value=1, max_value=8, value=4)

    st.divider()
    st.caption("API key được đọc từ `.env` và không bao giờ hiển thị trên UI.")

system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"
artifact = build_artifact_version(version, system_prompt_path, tools_path)
tool_declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(tool_declarations)

selected_model = model_override.strip() or None
settings_key = (provider_name, selected_model, artifact.artifact_version, history_window, max_tool_rounds)
if "settings_key" not in st.session_state or st.session_state.settings_key != settings_key:
    initialise_session(
        artifact=artifact,
        provider=provider_name,
        model=selected_model,
        history_window=history_window,
        max_tool_rounds=max_tool_rounds,
    )

left, right = st.columns([2, 1])
with left:
    st.info(f"Artifact: `{artifact.artifact_version}` · Provider: `{provider_name}` · Số tool: {len(tool_declarations)}")
with right:
    if st.button("Bắt đầu hội thoại mới", width="stretch"):
        initialise_session(
            artifact=artifact,
            provider=provider_name,
            model=selected_model,
            history_window=history_window,
            max_tool_rounds=max_tool_rounds,
        )
        st.rerun()

for message in st.session_state.display_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("turn"):
            render_trace(message["turn"])

prompt = st.chat_input("Hỏi về tin web, bài đăng mạng xã hội, đọc URL hoặc tạo digest…", submit_mode="disable")
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.display_messages.append({"role": "user", "content": prompt})

    turn: dict[str, Any] = {
        "turn_index": len(st.session_state.transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    messages = [
        {"role": "system", "content": system_prompt_path.read_text(encoding="utf-8")},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": prompt},
    ]

    with st.chat_message("assistant"):
        with st.spinner("Agent đang chọn tool phù hợp…"):
            try:
                if api_key_input.strip():
                    key_env = f"{provider_name.upper()}_API_KEY"
                    os.environ[key_env] = api_key_input.strip()

                provider = make_provider(provider_name)
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds,
                )
                turn.update(result)
                answer = result["assistant_text"]
                st.markdown(answer)
                render_trace(turn)
                st.session_state.history.extend([
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": answer},
                ])
            except Exception as exc:
                answer = "Không thể gọi provider. Hãy kiểm tra provider đã chọn, API key, quota và model."
                turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {str(exc)}", "assistant_text": answer})
                st.error(answer)
                with st.expander("Chi tiết lỗi đã được che key"):
                    st.code(json_view({"error": turn["error"]}), language="json")

    turn["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(redact(turn))
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)
    st.session_state.display_messages.append({"role": "assistant", "content": answer, "turn": turn})
    st.rerun()

st.divider()
st.caption(f"Transcript: `{st.session_state.transcript_path.relative_to(ROOT)}`")
st.download_button(
    "Tải transcript hiện tại",
    data=json_view(st.session_state.transcript),
    file_name=st.session_state.transcript_path.name,
    mime="application/json",
)
