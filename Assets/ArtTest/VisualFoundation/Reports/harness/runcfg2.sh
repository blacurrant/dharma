#!/bin/bash
# usage: runcfg2.sh <cfg> <size> <offY> <fpsMode> <seqs>   (VF scene, no screenshots, per-frame log)
source /Users/landerstudio/.hermes/profiles/unity-engineer/cache/scratch/ue.sh
cfg=$1; size=$2; offy=$3; mode=$4; seqs=$5
D=/Users/landerstudio/MythicRoguelite/Assets/ArtTest/VisualFoundation/Reports/gate1set
mkdir -p $D
tf=60; interval=16; [ "$mode" = "uncapped" ] && { tf=-1; interval=0; }
sq=$(echo $seqs | sed 's/,/","/g')
unity command editor set_auto_tick --enable true --interval_ms $interval --persist false --result-only >/dev/null 2>&1
unity command editor focus --result-only >/dev/null 2>&1
ue 'var gvT=typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.GameView"); var gv=UnityEditor.EditorWindow.GetWindow(gvT); gv.Focus(); return "gameview focused";' >/dev/null; play start >/dev/null; sleep 10
ue "var r=ArtTestSequenceRunner.Create(); r.noShots=true; r.outDir=\"$D\"; var s=r.ApplyConfig(${size}f,new UnityEngine.Vector3(12f,${offy}f,-12f),false,$tf); r.RunMatrix(\"$cfg\",\"$mode\",new[]{\"$sq\"}); return s;" >/dev/null
end=$((SECONDS+900))
while [ $SECONDS -lt $end ]; do sleep 6; st=$(ue 'var r=ArtTestSequenceRunner.I; return r.status+" done="+r.done;'); case "$st" in *done=True*) break;; esac; done
ue "return ArtTestSequenceRunner.I.Dump(\"$D/${cfg}_${mode}.csv\");" >/dev/null
echo "$cfg $mode finished: $st"; python3 - <<PY
import csv
rows=list(csv.DictReader(open("$D/${cfg}_${mode}_perframe.csv")))
run=[r for r in rows if r["sequence"]=="run"]
print("  sanity: run-seq enemy dist range",min(float(r["player_enemy_m"]) for r in run),max(float(r["player_enemy_m"]) for r in run),"dash frames",sum(int(r["dashing"]) for r in rows))
PY
play stop >/dev/null
