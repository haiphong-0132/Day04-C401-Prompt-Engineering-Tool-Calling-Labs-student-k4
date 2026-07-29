from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import run_model_tool_loop, trim_history

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent UI", layout="wide")
st.title("Research Agent — Tool & Run Inspector")

# Sidebar controls
with st.sidebar.form(key="config"):
    provider = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini", "nvidia"], index=0)
    model = st.text_input("Model (optional)", value="")
    versions = st.text_input("Versions to compare (comma-separated)", value="v3")
    system_prompt_path = st.text_input("System prompt path", value=str(ARTIFACTS_DIR / "system_prompt.md"))
    tools_path = st.text_input("Tools declaration path", value=str(ARTIFACTS_DIR / "tools.yaml"))
    max_tool_rounds = st.number_input("Max tool rounds", value=4, min_value=1, max_value=10)
    history_window = st.number_input("History window", value=5, min_value=0, max_value=20)
    submit_config = st.form_submit_button("Apply")

st.write("## Input")
user_input = st.text_area("User request", value="Tóm tắt trang Wikipedia về GPT-4", height=120)
run_button = st.button("Run across versions")

# Helper to run one scenario
def run_scenario(version: str) -> dict[str, Any]:
    system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(Path(tools_path))
    openai_tools = to_openai_tools(tool_declarations)
    provider_obj = make_provider(provider)
    selected_model = model or getattr(provider_obj, "default_model", None)
    artifact_version = build_artifact_version(version, Path(system_prompt_path), Path(tools_path))

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    result = run_model_tool_loop(
        provider=provider_obj,
        messages=messages,
        tools=openai_tools,
        model=selected_model,
        max_tool_rounds=max_tool_rounds,
    )

    transcript = {
        "version": version,
        **artifact_version_dict(artifact_version),
        "provider": provider,
        "model": selected_model,
        "system_prompt": system_prompt_path,
        "tools": tools_path,
        "user_input": user_input,
        "result": result,
    }
    return transcript


if run_button:
    versions_list = [v.strip() for v in versions.split(",") if v.strip()]
    if not versions_list:
        st.warning("Please enter at least one version label (e.g. v1)")
    else:
        cols = st.columns(len(versions_list))
        transcripts = {}
        for i, ver in enumerate(versions_list):
            with cols[i]:
                st.subheader(ver)
                try:
                    with st.spinner(f"Running {ver}..."):
                        transcript = run_scenario(ver)
                        transcripts[ver] = transcript
                        res = transcript["result"]

                        st.write("**Final assistant text**")
                        st.text_area("assistant_text", value=res.get("assistant_text", ""), height=150)

                        st.write("**Rounds**")
                        for rd in res.get("rounds", []):
                            st.markdown(f"**Round {rd['round']}**")
                            st.write("Assistant text:")
                            st.write(rd.get("assistant_text"))
                            st.write("Tool calls:")
                            st.json([{"name": c["name"], "args": c["args"]} for c in rd.get("tool_calls", [])])
                            st.write("Tool results:")
                            st.json(rd.get("tool_results", []))

                        st.write("**Tool events (all)**")
                        st.json(res.get("tool_events", []))

                        st.write("**Artifact version**")
                        st.json({"artifact_version": transcript.get("artifact_version")})

                except Exception as exc:
                    st.error(f"Error running version {ver}: {type(exc).__name__}: {exc}")

        # Allow download of combined transcripts
        combined = {v: t for v, t in transcripts.items()}
        st.download_button("Download transcripts JSON", data=json.dumps(combined, ensure_ascii=False, indent=2), file_name="transcripts.json")

st.write("---")
st.write("You can run the same user input across different artifact versions to compare tool calls, arguments and results.")

