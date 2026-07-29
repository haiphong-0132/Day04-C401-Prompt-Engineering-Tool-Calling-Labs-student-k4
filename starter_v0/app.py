from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import run_model_tool_loop, trim_history, safe_slug, now_iso, write_transcript

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent - Gemini 3.5 Flash",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title and header
st.title("⚡ Research Agent UI — Powered by Gemini 3.5 Flash")
st.caption("Lab Day 04: Research Agent Tool Evaluation & Multi-turn Execution")

# Sidebar Configuration
st.sidebar.header("⚙️ Agent Settings")

provider_name = st.sidebar.selectbox(
    "Provider",
    options=["gemini", "openrouter", "openai", "anthropic"],
    index=0,
    help="Defaulting to Gemini Provider",
)

default_model = "gemini-3.5-flash" if provider_name == "gemini" else ""
model_name = st.sidebar.text_input(
    "Model Name / Override",
    value=default_model,
    help="Model ID to invoke. Default for Gemini is gemini-3.5-flash",
)

version_label = st.sidebar.text_input(
    "Artifact Version",
    value="v0",
    help="Version label for version_log.csv tracking (e.g. v0, v1, v2, v3)",
)

history_window = st.sidebar.number_input(
    "History Window (Turns)",
    min_value=1,
    max_value=20,
    value=5,
    help="Number of turn pairs kept in conversational memory context",
)

max_tool_rounds = st.sidebar.number_input(
    "Max Tool Rounds",
    min_value=1,
    max_value=10,
    value=4,
    help="Maximum loop iterations per user turn",
)

# Load artifacts
system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"

if system_prompt_path.exists():
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
else:
    system_prompt = "You are a helpful research assistant."
    st.sidebar.warning("⚠️ `artifacts/system_prompt.md` missing.")

try:
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    st.sidebar.success(f"🛠️ Loaded {len(openai_tools)} tools from `tools.yaml`")
except Exception as e:
    openai_tools = []
    st.sidebar.error(f"❌ Error loading tools.yaml: {e}")

artifact_ver = None
try:
    artifact_ver = build_artifact_version(version_label, system_prompt_path, tools_path)
    st.sidebar.info(
        f"**Artifact Version**: `{artifact_ver.artifact_version}`\n\n"
        f"**Prompt Hash**: `{artifact_ver.prompt_hash}`\n\n"
        f"**Tools Hash**: `{artifact_ver.tools_hash}`"
    )
except Exception as e:
    st.sidebar.warning(f"Version compute warning: {e}")

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "turns_history" not in st.session_state:
    st.session_state.turns_history = []
if "transcript_id" not in st.session_state:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    st.session_state.transcript_id = f"{safe_slug(version_label)}_{safe_slug(provider_name)}_{timestamp}"

# Reset Chat Button
if st.sidebar.button("🗑️ Clear Chat / Reset Session"):
    st.session_state.messages = []
    st.session_state.turns_history = []
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    st.session_state.transcript_id = f"{safe_slug(version_label)}_{safe_slug(provider_name)}_{timestamp}"
    st.rerun()

transcript_path = TRANSCRIPTS_DIR / f"{st.session_state.transcript_id}.transcript.json"
st.sidebar.caption(f"📄 Log: `{transcript_path.name}`")

# Render previous messages in UI
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("rounds"):
            with st.expander("🔍 Trace: Tool Rounds & Results", expanded=False):
                for r in msg["rounds"]:
                    st.markdown(f"**Round {r.get('round')}**")
                    if r.get("assistant_text"):
                        st.caption(f"Assistant thought: {r['assistant_text']}")
                    for call in r.get("tool_calls", []):
                        st.code(f"Tool Call: {call.get('name')}\nArgs: {json.dumps(call.get('args', {}), ensure_ascii=False, indent=2)}", language="json")
                    for res in r.get("tool_results", []):
                        st.json(res)

# Handle Chat Input
if user_input := st.chat_input("Nhập câu hỏi hoặc yêu cầu nghiên cứu..."):
    # Add user message to UI state
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process response
    with st.chat_message("assistant"):
        with st.spinner("Agent đang xử lý bằng Gemini 3.5 Flash..."):
            try:
                provider = make_provider(provider_name)
                selected_model = model_name.strip() if model_name.strip() else "gemini-3.5-flash"

                # Construct prompt history memory
                history_turns = []
                for turn in st.session_state.turns_history:
                    history_turns.append({"role": "user", "content": turn["user"]})
                    if turn.get("assistant_text"):
                        history_turns.append({"role": "assistant", "content": turn["assistant_text"]})

                messages = [
                    {"role": "system", "content": system_prompt},
                    *trim_history(history_turns, history_window),
                    {"role": "user", "content": user_input},
                ]

                # Run loop
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds,
                )

                assistant_text = result.get("assistant_text", "")
                rounds = result.get("rounds", [])
                tool_events = result.get("tool_events", [])

                # Render assistant output
                st.markdown(assistant_text)

                if rounds:
                    with st.expander("🔍 Trace: Tool Rounds & Results", expanded=True):
                        for r in rounds:
                            st.markdown(f"**Round {r.get('round')}**")
                            for call in r.get("tool_calls", []):
                                st.code(f"🔧 Tool: {call.get('name')}\nArgs: {json.dumps(call.get('args', {}), ensure_ascii=False, indent=2)}", language="json")
                            for res in r.get("tool_results", []):
                                st.json(res)

                # Update UI state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "rounds": rounds,
                    "tool_events": tool_events,
                })

                # Save turn to history
                st.session_state.turns_history.append({
                    "turn_index": len(st.session_state.turns_history) + 1,
                    "started_at": now_iso(),
                    "user": user_input,
                    "status": result.get("status", "answered"),
                    "assistant_text": assistant_text,
                    "rounds": rounds,
                    "tool_events": tool_events,
                    "ended_at": now_iso(),
                })

                # Write transcript file
                transcript_data = {
                    "transcript_id": st.session_state.transcript_id,
                    "provider": provider_name,
                    "model": selected_model,
                    "system_prompt": str(system_prompt_path),
                    "tools": str(tools_path),
                    "history_window": history_window,
                    "max_tool_rounds": max_tool_rounds,
                    "created_at": now_iso(),
                    "updated_at": now_iso(),
                    "turns": st.session_state.turns_history,
                }
                if artifact_ver is not None:
                    transcript_data.update(artifact_version_dict(artifact_ver))

                write_transcript(transcript_path, transcript_data)

            
            
            
            
            
            
            except Exception as exc:
                err_msg = f"❌ **Lỗi gọi Provider ({provider_name})**: `{type(exc).__name__}: {exc}`"
                st.error(err_msg)
                st.info("💡 **Gợi ý**: Kiểm tra xem file `.env` đã có `GEMINI_API_KEY` hợp lệ chưa.")
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
