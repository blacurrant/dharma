#!/bin/bash
# usage: runcfg.sh <cfgName> <size> <offY> <biased:0|1> <fpsMode:cap60|uncapped> <seqs comma list>
source /Users/landerstudio/.hermes/profiles/unity-engineer/cache/scratch/ue.sh
cfg=$1; size=$2; offy=$3; biased=$4; mode=$5; seqs=$6
D=/Users/landerstudio/MythicRoguelite/Assets/ArtTest/Reviews/Gate1/data
tf=60; interval=16; [ "$mode" = "uncapped" ] && { tf=-1; interval=0; }
bflag=false; [ "$biased" = "1" ] && bflag=true
sq=$(echo $seqs | sed 's/,/","/g')
unity command editor set_auto_tick --enable true --interval_ms $interval --persist false --result-only >/dev/null 2>&1
unity command editor focus --result-only >/dev/null 2>&1
play start >/dev/null; sleep 10
ue "var r=ArtTestSequenceRunner.Create(); r.outDir=\"$D\"; var s=r.ApplyConfig(${size}f,new UnityEngine.Vector3(12f,${offy}f,-12f),$bflag,$tf); r.RunMatrix(\"$cfg\",\"$mode\",new[]{\"$sq\"}); return s+\" pitch=\"+UnityEngine.Mathf.Atan2(${offy}f,16.9706f)*57.2958f;"
end=$((SECONDS+900))
while [ $SECONDS -lt $end ]; do
  sleep 6
  st=$(ue 'var r=ArtTestSequenceRunner.I; return r.status+" done="+r.done+" t="+UnityEngine.Time.time.ToString("F1");')
  echo "$st"
  case "$st" in *done=True*) break;; esac
done
ue "return ArtTestSequenceRunner.I.Dump(\"$D/${cfg}_${mode}.csv\");"
ue 'return "avg fps context: targetFps="+UnityEngine.Application.targetFrameRate+" vsync="+UnityEngine.QualitySettings.vSyncCount;'
play stop >/dev/null
