#!/bin/bash
# usage: capture_pose.sh <centre|north|west|dais|arch|edge> [out.png]   (A2, 1920x1080, HUD, no hit, enemy parked)
# Needs the Editor open on ArtTest_VisualFoundation.unity with the Game view set to Full HD 1920x1080, and the editor lock free (see CAPTURE_HOWTO.md).
POSE=${1:?pose}; OUT=${2:-/Users/landerstudio/MythicRoguelite/Assets/ArtTest/VisualFoundation/Captures/art_pass/$POSE.png}
HERE="$(cd "$(dirname "$0")" && pwd)"; cd /Users/landerstudio/MythicRoguelite; mkdir -p "$(dirname "$OUT")"; rm -f "$OUT"
unity command editor focus --result-only >/dev/null 2>&1
unity command editor.playmode start --result-only >/dev/null 2>&1; sleep 14
CODE=$(sed "s#__POSE__#$POSE#; s#__OUT__#$OUT#" "$HERE/capture_pose.cs.txt")
unity command script eval "$CODE" --timeout 120 --result-only >/dev/null 2>&1
for i in $(seq 1 30); do [ -s "$OUT" ] && break; sleep 2; done
unity command editor.playmode stop --result-only >/dev/null 2>&1
[ -s "$OUT" ] && echo "OK $OUT" || echo "FAILED (check the Unity console; Game view must be 1920x1080)"
