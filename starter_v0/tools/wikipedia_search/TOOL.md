---
name: wikipedia_search
track: core
kind: live_api
provider: MediaWiki API
requires_env: []
inputs: [query, lang, limit, summary]
outputs: [tool, query, lang, limit, items]
side_effect: none
---
# wikipedia_search

Searches Wikipedia for a given topic via the MediaWiki API and returns matching pages with brief summaries.