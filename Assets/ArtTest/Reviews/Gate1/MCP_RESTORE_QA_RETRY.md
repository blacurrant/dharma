# MCP restore QA - controlled retry (read-only) - 2026-10-26

## Summary
| Item | Verdict |
|---|---|
| Bridge connectivity | PASS |
| Tool visibility (no new session) | PASS (110 tools, not 166) |
| Successful read-only tool call | PASS |
| Independent evidence verification | PASS for items checked; editor playing/idle state UNVERIFIED (no read-only tool; only `eval` could answer it, which I did not call) |

## 1. Enable (called once)
`manage_connections action=enable {"name":"unity","mcp":true}` -> `"state": "connected"`, `"settled_by": "all_resolved"`, status "settled". The call returned the tool list directly; no error and no cooldown text. Approval was granted. The tools were callable through `tool_describe`/`tool_call` in this same session, with no new session needed.
Discrepancy: the listing says `unity tools (110)`, not 166 as the Director reported. Possibly the bridge's 166 includes non-MCP or hidden items; unexplained.

## 2. Raw read-only calls (my own MCP session)
- list_instances: `{"count":1,"instances":[{"name":"Main Editor","role":"main","port":7800,"pid":75473,"vpId":null,"projectPath":"/Users/landerstudio/MythicRoguelite"}]}`
- recompile_status: `{"status":"idle","failed":false,"errors":[],"compilationFailed":false}`
- list_open: `{"count":1,"scenes":[{"name":"ArtTest_TempleCourtyard","path":"Assets/Scenes/ArtTest_TempleCourtyard.unity","isLoaded":true,"isDirty":false,"isActive":true,"rootCount":12}]}`
- get_fields /Directional Light Transform: `m_LocalRotation {x:0.30078575, y:0.361834347, z:-0.124589548, w:0.8735453}`, `m_LocalPosition (0,3,0)`.
- get_fields /Main Camera IsoCameraFollow: `offset {12,18,-12}`, `followSpeed 14`, `orthographicSize 9`; target = `/CameraFocus`.
- get_fields /Main Camera Camera `orthographic size`: `9`.

## 3. Comparison with disk
| Item | Live (MCP) | Saved scene (disk) | Result |
|---|---|---|---|
| Light quaternion | 0.30078575, 0.361834347, -0.124589548, 0.8735453 | 0.30078575, 0.36183435, -0.12458955, 0.8735453 | match (float rounding only). This equals euler (38,45,0): elevation 38 deg, yaw 45 deg, 63.4 deg from camera. |
| Camera offset | (12,18,-12) | (12,18,-12) | match |
| orthographicSize | 9 (both IsoCameraFollow and Camera) | 9 | match |
| Scene / dirty | ArtTest_TempleCourtyard, isDirty false | n/a | PASS |
Note: the live Transform returns a quaternion, not Euler angles; euler (38,45,0) is my conversion, not a tool output.
Editor state: not compiling (idle, no errors). Playing/importing state: not read. Indirect hints only: scene not dirty, rootCount 12 (no runtime-created roots), active scene is ArtTest. This is not proof of Edit Mode.

## 4. Tool classification (110 tools)
Only these 8 had their schema/description read: list_instances, status, list_open, get_properties, get, find, recompile_status, get_fields. All other classifications are BY NAME ONLY and unverified.

### Read-only (proposed allowlist; * = schema read by me)
list_instances*, list_open*, get_fields*, get_properties*, find*, recompile_status*, get* (AnimationClip read, named `get`), get_hierarchy, get_controller, get_import_settings, get_performance, get_root, get_selection, get_settings, get_shader_properties, list, list_platforms, list_profiles, list_shaders, read_text, search, bake_status, audit_status, switch_status, wait_status, report_evals, status* (build status; description says status of current/most recent build)

### Uncertain (could write files or change view/focus; confirm before allowing)
screenshot, game_view, scene_view, focus, wait, wait_cancel, get_selection side effects none expected but unconfirmed

### Arbitrary execution (never on a read-only profile)
eval, eval_file, invoke_menu, run, run_audit, batch

### State-changing (by name)
add, add_clip, add_layer, add_parameter, add_state, add_to_build, add_track, add_transition, apply_overrides, attach, bake, bake_surfaces, cancel, cancel_bake, cleanup, clear, clear_bake, copy, create, create_controller, create_folder, create_many, create_profile, create_variant, delete, generate_link_xml, import, instantiate, move, open, pause, quit, recompile, reload, reload_editor, reload_player, remove, remove_curve, remove_from_build, rename, resolve, revert_overrides, save, save_all, save_contents, set, set_active, set_auto_tick, set_curve, set_field, set_import_settings, set_layer, set_parent, set_profile, set_properties, set_root, set_run_in_background, set_selection, set_settings, set_tag, set_target_frame_rate, set_time_scale, set_transform, simulate_key, simulate_pointer, start, stop, switch, unpack, write, write_text

## 5. PROPOSED read-only allowlist (NOT applied; no config, permission or allowlist edited)
- mcp__unity__list_instances
- mcp__unity__list_open
- mcp__unity__get_fields
- mcp__unity__get_properties
- mcp__unity__get_hierarchy
- mcp__unity__find
- mcp__unity__search
- mcp__unity__recompile_status
- mcp__unity__get_performance
- mcp__unity__get_settings
- mcp__unity__get_import_settings
- mcp__unity__get_root
- mcp__unity__get_selection
- mcp__unity__get_shader_properties
- mcp__unity__get_controller
- mcp__unity__get
- mcp__unity__list, list_platforms, list_profiles, list_shaders
- mcp__unity__read_text
- mcp__unity__bake_status, audit_status, switch_status, wait_status, status
Gap: no read-only tool reports Play Mode or importing state; the only way found is `eval` (excluded). Ask the Unity Engineer for a read-only editor-state tool if that is required.
Caveat: `get_hierarchy` returned about 130 KB earlier; `get_performance` and `status` semantics not verified.

## Compliance
No Play Mode, save, import, asset/scene edit, bake, config edit, or eval was used. Four Unity-generated files, Blender and production .blend were not touched.
