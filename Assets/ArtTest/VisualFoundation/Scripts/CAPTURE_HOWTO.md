# Capturing a Game-view frame (saved A2 camera, 1920x1080, HUD) for a named pose

Poses (player position x,z): centre (0,0), north (-8,16), west (-16,-2), dais (-8,8), arch (4,15), edge (13,-13). Camera = the saved scene camera (A2 pitch, 42 deg; ortho 7.5 since art pass 4), plain follow (focus helper off), enemy parked 60 m away and disabled (no telegraph, no hit), HUD on, waits until the HUD "HIT" text has lapsed.

## One command
```
Assets/ArtTest/VisualFoundation/Scripts/capture_pose.sh dais Assets/ArtTest/VisualFoundation/Captures/art_pass/EA_dais.png
```
Run from anywhere; the second argument is optional (default `Captures/art_pass/<pose>.png`). It focuses the Editor, enters Play Mode, runs the pose script, writes the PNG, leaves Play Mode, prints `OK <path>`. About 30 s per frame.

Prerequisites: the Editor is open on `Assets/Scenes/ArtTest_VisualFoundation.unity`; the Game view is set to **Full HD (1920x1080)** (the script aborts with a console error and no file if it is not); the editor lock is free (below).

## The raw commands (what the script does)
```
unity command editor focus
unity command editor.playmode start        # wait ~14 s for the domain/scene start
unity command script eval "<contents of Scripts/capture_pose.cs.txt with __POSE__ and __OUT__ replaced>" --timeout 120
unity command editor.playmode stop
```
Alternative once in Play Mode, without the script: place the player by `script eval` and call `unity command capture game_view --width 1920 --height 1080 --source screen --save_path <png>` (this captured correctly in earlier work, but pose, camera and HUD state are then on you).
With MCP tools, the equivalents are the Unity MCP `editor.playmode`, script-eval and game-view capture calls; the pose script above is the same code.

## Do not
- Do not save the scene while in Play Mode; the script changes nothing that is saved (camera, enemy and player moves are runtime only).
- Do not put `.cs` capture scripts under `Assets/`: they would be compiled and a broken one blocks every recompile. Use `.cs.txt`.

## Editor lock
File: `Assets/ArtTest/VisualFoundation/EDITOR_LOCK.txt`. Whoever drives the Editor (Play Mode, scene edits, captures, saves) first checks it:
1. If the file contains a name and time, the other party holds the Editor: do not enter Play Mode, do not save the scene, wait or ask.
2. If empty or absent: write `<name> <ISO time> <what you are doing>` (one line), then work.
3. When the scene is saved (or the work is abandoned) and the Editor is out of Play Mode, clear the file (empty it).
Stale lock (older than about 30 minutes with the Editor idle): ask the holder first, then clear it and say so in the pass log.
Before each art pass, save a dated scene copy to `Assets/Scenes/_art_pass/` (`ArtTest_VisualFoundation_<yyyymmdd_hhmm>_<name>.unity`).
Do not edit another owner's objects: `VF_EA_*` roots belong to the Environment Artist, the rest of the VF scene to the Unity Engineer.
