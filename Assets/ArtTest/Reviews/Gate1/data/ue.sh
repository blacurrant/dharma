#!/bin/bash
# helpers for driving the live Editor through the unity CLI (MCP tools dropped from the session)
cd /Users/landerstudio/MythicRoguelite
ue()    { unity command script eval "$1" --timeout "${2:-120}" --result-only 2>&1 | python3 -c "import sys,json; t=sys.stdin.read(); 
try:
  d=json.loads(t); print(d.get('result') if d.get('success') else t)
except Exception: print(t)"; }
shot()  { unity command capture game_view --width 1920 --height 1080 --source screen --save_path "$1" --result-only 2>&1 | tail -3; }
play()  { unity command editor.playmode "$1" --result-only 2>&1 | tail -2; }
