# Unity MCP restore check: unity-engineer session (read-only)

**MCP result: FAIL.** The `unity` MCP tools are not visible in this session. The four proofs below were obtained through the `unity` CLI against the same Editor (port 7800), not through MCP tools.

## MCP attempt (verbatim)
- `tool_search` for "unity list instances", "unity eval C#", "unity get hierarchy scene", "unity list_instances", "unity scene hierarchy": no matches. Available sources listed: blender (30), browser, catalog, computer_use, cronjob, desktop_ui (10), project, session_search, terminal, todo, x_search. No `unity` source.
- `manage_connections` action=enable, target `{"name":"unity","mcp":true}`:
  `"state": "not_connected"`, `"settled_by": "deadline"`, status "settled". No error text and no retry-cooldown text was returned.
- Likely cause (unverified): the tool list is fixed at session start, so a new session may be needed to pick up the restored bridge.

## Proofs (CLI, read-only)
1. **Instance list: PASS (via CLI).** `unity status` and `unity command editor.playmode list_instances`:
```
port 7800  state ready  project /Users/landerstudio/MythicRoguelite  version 6000.6.7f1  pid 75473
{"count":1,"instances":[{"name":"Main Editor","role":"main","port":7800,"pid":75473,"vpId":null,"projectPath":"/Users/landerstudio/MythicRoguelite"}]}
```
   Note the pid is new (75473; earlier sessions were 51371): the Editor was restarted.
2. **Editor state: PASS (via CLI).** `isPlaying=False isCompiling=False isUpdating=False`
3. **Active scene: PASS (via CLI).** `scene=ArtTest_TempleCourtyard path=Assets/Scenes/ArtTest_TempleCourtyard.unity dirty=False`
4. **Scene query: PASS (via CLI).** Directional Light `euler=(38.00, 45.00, 0.00)`, as expected.

## Side observation
`git status` (tracked files only) now shows `ProjectSettings/ProjectSettings.asset` modified, in addition to `Art/README.md`, the two Paladin `.mat` files and `EditorPipelineConfig.json`. I did not make that change in this check and have not inspected or reverted it; it most likely came from the Editor restart. Nothing was reverted, staged, committed, saved or entered into Play Mode in this check.
