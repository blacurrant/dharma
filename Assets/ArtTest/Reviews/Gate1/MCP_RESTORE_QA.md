# MCP restore check (QA, read-only) - 2026-10-26 ~13:03 IST

Result: the unity MCP tools are NOT visible in the qa-reviewer session. Items 1-3 FAIL (no tool access). Item 4 is UNVERIFIED via MCP; a disk-only read is given as a substitute and is not MCP proof.

## Attempts
1. tool_search for "unity list_instances", "unity editor state compile", "unity get_fields", "unity list_open scene", "unity", "mcp__unity".
   Raw: `"matches": []` for every query. available_sources: blender(30), browser, catalog, computer_use, cronjob, desktop_ui(10), project, session_search, terminal, todo, x_search. No "unity" source.
2. manage_connections action=enable, connectors=[{"name":"unity","mcp":true}].
   Raw: `"state": "not_connected"`, `"settled_by": "deadline"`, status "settled". No error text and no retry-cooldown text was returned.
3. tool_describe ["mcp__unity__list_instances"].
   Raw: `"tools": {}, "not_found": ["mcp__unity__list_instances"], "hint": "Names in not_found are not currently available. Re-run tool_search to refresh."`
No unity tool was called. No write, create, delete, save, import, component-set or Play Mode call was made.

## Items
| # | Item | Result |
|---|---|---|
| 1 | Instance list and project path via MCP | FAIL - tool not available (see above) |
| 2 | Editor not playing / not compiling via MCP | FAIL - tool not available |
| 3 | Active scene and dirty flag via MCP | FAIL - tool not available |
| 4 | Key light rotation (38,45,0), camera size 9, offset (12,18,-12) via MCP | UNVERIFIED via MCP |

## Disk-only evidence (not MCP, saved scene file)
- Unity processes are running (started 12:54-12:55, Unity 6000.6.7f1 Editor). `ps` shows the Editor; this does not prove the MCP bridge or the project path.
- Saved scene `Assets/Scenes/ArtTest_TempleCourtyard.unity` (mtime 2026-10-25 01:17:24):
  - `offset: {x: 12, y: 18, z: -12}` (line 19676), `orthographicSize: 9` (line 19678) - match expected.
  - Directional Light local quaternion {0.30078575, 0.36183435, -0.12458955, 0.8735453}: forward (0.557, -0.616, 0.557), i.e. elevation 38 deg, yaw 45 deg, 63.4 deg from the camera. Matches (38,45,0). Note the YAML `m_LocalEulerAnglesHint` still reads (50,-30,0); the quaternion is authoritative.
- The scene dirty flag and Play/compile state cannot be read from disk.

## Write-capable tool list
Cannot be produced: I cannot enumerate the 166 tools. Only the 6 read-style tools I saw earlier are known by name (list_instances, list_open, get_hierarchy, get_fields read-only; eval, start/stop/clear are NOT read-only: eval runs arbitrary C#, start enters Play Mode). Please supply the tool list, or restore access, and I will classify it. No allowlist applied.

## Likely causes (unproven)
The enable call settled by deadline with state not_connected and no error text; the server may need approval in the desktop app or a bridge restart for this profile.
