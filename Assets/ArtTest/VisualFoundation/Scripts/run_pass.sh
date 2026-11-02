#!/bin/bash
# usage: run_pass.sh <tag> <ortho> <offY> <setup.cs.txt|-> ; captures duel_centre/dais/west/north/edge at the given camera into Captures/art_pass/UE_<tag>_*.png and writes Reports/ap_metrics_<tag>.csv
H="$(cd "$(dirname "$0")" && pwd)"; TAG=$1; ORTHO=$2; OFFY=$3; SETUP=$4; TMP=/tmp/pass_$TAG.cs
python3 - "$H/artpass.cs.txt" "$TAG" "$ORTHO" "$OFFY" "$SETUP" > $TMP <<'PY'
import sys
t=open(sys.argv[1]).read(); s='' if sys.argv[5]=='-' else open(sys.argv[5]).read()
print(t.replace('__TAG__',sys.argv[2]).replace('__ORTHO__',sys.argv[3]).replace('__OFFY__',sys.argv[4]).replace('__SETUP__',s))
PY
cd /Users/landerstudio/MythicRoguelite
unity command editor focus --result-only >/dev/null 2>&1; unity command editor.playmode start --result-only >/dev/null 2>&1; sleep 14
unity command script eval "$(cat $TMP)" --timeout 120 --result-only 2>&1 | head -c 400
for i in $(seq 1 100); do sleep 5; st=$(unity command script eval 'return VFRunner.I.status;' --timeout 30 --result-only 2>&1 | head -c 300); case "$st" in *"stack done"*) break;; esac; done
unity command editor.playmode stop --result-only >/dev/null 2>&1; echo "PASS $TAG: $st"
