#!/bin/bash
R=/Users/landerstudio/.hermes/profiles/unity-engineer/cache/scratch/runcfg.sh
Q=idle,run,dash_rest,dash_run,attack,dodge,chain,edge_up,edge_down,far_chase_up,far_chase_down
for m in cap60 uncapped; do
  $R A_plain 8 15.28 0 $m $Q
  $R B_plain 9 18 0 $m $Q
  $R C_plain 11 18 0 $m $Q
done
$R A_focusON 8 15.28 1 cap60 $Q
$R B_focusON 9 18 1 cap60 $Q
echo MATRIX_DONE
