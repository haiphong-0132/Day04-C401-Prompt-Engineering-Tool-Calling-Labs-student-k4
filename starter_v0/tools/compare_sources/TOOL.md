---
name: compare_sources
track: core
kind: local_formatter
requires_env: []
inputs: [items, focus]
outputs: [shared_terms, all_terms, sources]
side_effect: false
---
# compare_sources

Compares text already collected from two or more sources. It highlights shared
and source-specific terms; it does not judge factual accuracy or fetch URLs.
