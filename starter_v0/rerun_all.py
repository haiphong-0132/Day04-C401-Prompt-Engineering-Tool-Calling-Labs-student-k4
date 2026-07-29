import os
import subprocess
import time
import json
from pathlib import Path

def set_model(model_name):
    provider_path = "providers/nvidia_provider.py"
    with open(provider_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    import re
    new_content = re.sub(r'default_model="[^"]+"', f'default_model="{model_name}"', content)
    with open(provider_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Set model to {model_name}")

def run_eval(version, system_prompt, tools):
    cmd = [
        ".venv\\Scripts\\python.exe", "run_eval.py",
        "--provider", "nvidia",
        "--version", version,
        "--suite", "base",
        "--eval-cases", "data/eval_base.json",
        "--system-prompt", system_prompt,
        "--tools", tools
    ]
    print(f"Running {version}...")
    subprocess.run(cmd)

set_model("meta/llama-3.1-8b-instruct")
run_eval("v0", "artifacts/system_prompt.md", "artifacts/tools.yaml")
run_eval("v1", "artifacts/system_prompt_v1.md", "artifacts/tools.yaml")
run_eval("v2", "artifacts/system_prompt_v1.md", "artifacts/tools_v2.yaml")

set_model("meta/llama-3.1-70b-instruct")
run_eval("v2_70b", "artifacts/system_prompt_v1.md", "artifacts/tools_v2.yaml")

# Run parser
subprocess.run([".venv\\Scripts\\python.exe", "scripts/parse_runs.py", "runs/", "--output", "analysis/base_runs.csv"])
print("Done! You can now manually add them to version_log.csv with the parsed hashes.")
