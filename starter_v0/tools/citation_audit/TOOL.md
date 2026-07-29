---
name: citation_audit
track: core
kind: local_formatter
requires_env: []
inputs: [draft, allowed_urls]
outputs: [cited_urls, missing_from_sources, unused_sources, all_citations_known]
side_effect: false
---
# citation_audit

Checks URLs in a draft against a source URL allow-list. It verifies link
membership only; it does not verify that a written claim is factually true.
