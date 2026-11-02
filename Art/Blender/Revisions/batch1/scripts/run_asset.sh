#!/bin/bash
# run_asset.sh <Name>: bake + verify. Retries ONLY when Blender crashed (no Python traceback in the log: the known intermittent Metal bake crash).
# A Python traceback / assertion is a deterministic bug or a failed check: stop immediately and report it (never mask it as a crash).
cd /Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/batch1
B=/Applications/Blender.app/Contents/MacOS/Blender
N=$1
for i in 1 2 3 4; do
  $B -b --factory-startup --python scripts/22_verify_bake.py -- $N > evidence/22_verify_$N.log 2>&1
  if grep -q "VERIFY_DONE" evidence/22_verify_$N.log; then echo "$N VERIFIED attempt $i"; exit 0; fi
  if grep -q "Traceback" evidence/22_verify_$N.log; then echo "$N FAILED (python error, no retry): $(grep -E 'Traceback' -A8 evidence/22_verify_$N.log | tr '\n' ' ' | cut -c1-500)"; exit 2; fi
  echo "$N attempt $i: Blender exited without VERIFY_DONE and without a traceback (crash) -> retry"
done
echo "$N GAVE UP after crashes"; exit 1
