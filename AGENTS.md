# Maintenance

- Keep game behavior and original UI implementations in the four upstream repositories. Do not patch submodule source to implement integration features.
- Use `tools/sync_upstreams.py` to change upstream pins and regenerate `upstream-lock.json`; keep each source and lock entry aligned.
- Keep component imports in separate child processes. Only one component may register its global shortcuts at a time.
- Switch only after the active component accepts deactivation and completes its original close routine. Never interrupt an active game to change tabs.
- Preserve each original program's settings, records, models, diagnostics and required notices.
- Verify source and frozen embedded interfaces with `tools/smoke_test.py`. Smoke tests use temporary AppData, disable shortcuts and never start automation.
- Use concise developer-facing documentation and short English commit subjects. Keep English and Traditional Chinese README content aligned.
