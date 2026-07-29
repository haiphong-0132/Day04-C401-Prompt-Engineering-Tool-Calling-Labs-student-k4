---
name: keywords
track: core
kind: local_formatter
requires_env: []
inputs: [text, max_keywords]
outputs: [keywords, keyword_count]
side_effect: false
---
# keywords

Extracts frequent keywords from text the agent already has. It does not search
the web and does not infer facts beyond the supplied text.
