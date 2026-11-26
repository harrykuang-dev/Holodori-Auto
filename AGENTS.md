# Maintenance

- Maintain the five features together in components/. Record imported-source provenance in document/SOURCE-ORIGINS.json.
- Keep component imports in separate child processes. Only one component may register its global shortcuts at a time.
- Switch only after the active component accepts deactivation and completes its original close routine. Never interrupt an active game to change tabs.
- Preserve each original program's settings, records, models, diagnostics and required notices.
- Verify source and frozen embedded interfaces with `tools/smoke_test.py`. Smoke tests use temporary AppData, disable shortcuts and never start automation.
- Use concise developer-facing documentation and short English commit subjects. Keep English and Traditional Chinese README content aligned.
