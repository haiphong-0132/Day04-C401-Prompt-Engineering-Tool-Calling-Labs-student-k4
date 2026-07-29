import json

# Manual merge
final_dict = {
  "dataset_id": "day04_v2_team_eval",
  "dataset_role": "group",
  "description": "Team-authored routing eval: 5 single-turn và 5 multi-turn + Added Wikipedia cases.",
  "allowed_failure_types": ["wrong_tool", "wrong_arg_value", "wrong_boundary", "unnecessary_tool", "out_of_scope", "missing_info"],
  "cases": []
}

# The easiest way is to just load my cases from the backup or recreate them.
# But they are inside eval_group.json. Let's extract them using simple string manipulation.

with open("data/eval_group.json", "r", encoding="utf-8") as f:
    text = f.read()

import re

# extract cases array from HEAD
head_cases_match = re.search(r'<<<<<<< HEAD.*?\"cases\": \[\s*(.*?)\s*\]\n======', text, re.DOTALL)
origin_cases_match = re.search(r'======.*?\"cases\": \[\s*(.*?)\s*\]\n>>>>>>>', text, re.DOTALL)

if head_cases_match and origin_cases_match:
    head_cases_str = "[" + head_cases_match.group(1) + "]"
    origin_cases_str = "[" + origin_cases_match.group(1) + "]"
    
    # fix missing commas
    head_cases_str = re.sub(r'\}\s*\{', '},{', head_cases_str)
    origin_cases_str = re.sub(r'\}\s*\{', '},{', origin_cases_str)

    try:
        head_cases = json.loads(head_cases_str)
    except:
        print("HEAD cases parse failed")
        head_cases = []
        
    try:
        origin_cases = json.loads(origin_cases_str)
    except:
        print("Origin cases parse failed")
        origin_cases = []
        
    merged = head_cases + origin_cases
    for i, c in enumerate(merged):
        c['id'] = f"G{i+1:02d}_{c['id'].split('_', 1)[1] if '_' in c['id'] else c['id']}"
        
    final_dict["cases"] = merged
    
    with open("data/eval_group.json", "w", encoding="utf-8") as f:
        json.dump(final_dict, f, ensure_ascii=False, indent=2)
    print("Fixed!")
else:
    print("Regex failed")
