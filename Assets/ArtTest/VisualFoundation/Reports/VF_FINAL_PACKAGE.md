# VF_FINAL_PACKAGE (short): original courtyard vs Visual Foundation, camera A2

BEFORE = original `ArtTest_TempleCourtyard.unity` (played unsaved, hash b30065166bf45252 unchanged). AFTER = `ArtTest_VisualFoundation.unity` as saved before the art-first passes ("previous version"). A2 = 42 deg, ortho 8.5, 1920x1080 with HUD, no hits. Editor-only numbers.

Pictures: `Captures/final_package/overview_A2.png` (all six, before left / after right) and `Captures/final_package/composites/A2_<pose>_before_after.png`. Raw frames `Captures/final_package/{before,after}_A2_<pose>.png`. Long version kept as `VF_FINAL_PACKAGE_long_*.md.txt`.

| A2 pose | floor luma | player sep | enemy sep | lift | dim<0.12 |
|---|---|---|---|---|---|
| centre | 0.383 -> 0.381 | -0.095 -> -0.054 | -0.120 -> -0.085 | 0.141 -> 0.139 | 1.9 -> 1.5 % |
| north | 0.297 -> 0.312 | -0.094 -> 0.012 | 0.000 -> -0.025 | 0.136 -> 0.139 | 26.6 -> 9.1 % |
| west | 0.287 -> 0.251 | -0.069 -> 0.004 | -0.093 -> -0.021 | 0.160 -> 0.176 | 18.5 -> 15.5 % |
| dais | 0.350 -> 0.363 | -0.071 -> -0.031 | -0.084 -> -0.028 | 0.164 -> 0.148 | 7.2 -> 5.6 % |
| arch | 0.321 -> 0.310 | -0.096 -> -0.039 | -0.058 -> -0.004 | 0.136 -> 0.145 | 25.8 -> 14.6 % |
| edge | 0.332 -> 0.329 | -0.098 -> -0.056 | -0.119 -> -0.080 | 0.138 -> 0.138 | 51.1 -> 12.6 % |

Cost (centre, Editor): draw calls 1342 -> 1428, frame 4.79 -> 7.13 ms. Open: enemy-material cause UNVERIFIED; A2 dais enemy separation -0.028.
