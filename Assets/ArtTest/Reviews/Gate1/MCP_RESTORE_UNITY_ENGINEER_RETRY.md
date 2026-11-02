# Unity MCP restore: controlled retry (unity-engineer, read-only)

## Enable (called once)
`manage_connections` action=enable `{"name":"unity","mcp":true}` -> `state: connected`, `settled_by: all_resolved`, 110 tools listed (`mcp__unity__*`). The tools became callable in this same session; no new session was needed. Approval was granted (the call settled as connected, not by deadline).

## Raw read-only MCP outputs
1. `mcp__unity__list_instances`:
```
{"count":1,"instances":[{"name":"Main Editor","role":"main","port":7800,"pid":75473,"vpId":null,"projectPath":"/Users/landerstudio/MythicRoguelite"}]}
```
2. `mcp__unity__list_open`:
```
{"count":1,"scenes":[{"name":"ArtTest_TempleCourtyard","path":"Assets/Scenes/ArtTest_TempleCourtyard.unity","isLoaded":true,"isDirty":false,"isActive":true,"rootCount":12}]}
```
3. `mcp__unity__eval` (read-only expression: editor flags, active scene, key light rotation):
```
isPlaying=False isCompiling=False isUpdating=False scene=ArtTest_TempleCourtyard dirty=False keyEuler=(38.00, 45.00, 0.00)
```

## Results
- Bridge connectivity: PASS
- Tool visibility: PASS
- Successful read-only tool call: PASS
- Evidence: PASS (this file)

No Play Mode, save, import, asset/scene edit or bake was performed. The four Unity-generated files were not touched. No config, permission, Blender, git staging/commit/LFS action.
