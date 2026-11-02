# Art-test script history (dated copies taken BEFORE each edit)
Format: copy file | source | what changed afterwards (one line). Written 2026-10-26 17:4x; going forward every edit gets a copy + a line here.
- ArtTestSequenceRunner_20261026_1558_pre-iter3-followups.cs.txt | Assets/ArtTest/Scripts/ArtTestSequenceRunner.cs | (snapshot before follow-ups)
- ArtTestSequenceRunner_20261026_1603_before-settle.cs.txt | same | +1 line: 2-frame settle (`yield return null; yield return null;`) after the config change, before logging. Current file (mtime 16:03:49) differs from this copy by exactly that line.
- VFRunner_20261026_1558_pre-iter3-followups.cs.txt and VFRunner_20261026_1603_before-evidence-and-rimfix.cs.txt | Assets/ArtTest/VisualFoundation/Scripts/VFRunner.cs | both copies are identical to each other (no edit between 15:58 and 16:03). Current file (mtime 16:03) differs by 25 lines: settle in RunCfgs (+ frameIdx/lastHp reset moved), evidence-frame saving, rim light switched from Light.renderingLayerMask to UniversalAdditionalLightData.renderingLayers.
- VFBuilder/VF2Builder/VF3Builder, ArtTestCameraFocus/CyanTelegraphPreview/Harness/Lighting/CourtyardBuilder `*_1558_pre-iter3-followups*` | snapshots, unchanged since.
- VF4Builder_1633_graybox-final | VF4Builder before later edits (none since).
- VF5Builder_1633_before-BuildReal; _1634_before-capsule-radius; _1636_before-capsule-vertices; _1657_before-north-off; _1700_before-hand-colliders; _1735_before-arch-removal | each copy = state before that named edit.
Gap, stated honestly: edits made before 15:58 (iteration 2 and early iteration 3, including ArtTestSequenceRunner changes at 14:17 and 14:42) have no earlier copy; I cannot reconstruct them. Harness one-off scripts live as .cs.txt in Reports/harness/ (not Assets code).

## 2026-10-26 outer ground (Director GO)
- VF_OuterGround.mat `_BaseColor` (and `_Color`) 0.1100,0.0900,0.0750 -> 0.2750,0.2250,0.1875 (x2.5). Revert: set both back to 0.11,0.09,0.075 (old file copy: `VF_OuterGround_*_before-x2.5.mat.txt`, SHA-256 of the old .mat starts d8e999fb51d8). Note: `VFBuilder.cs` still creates the material with the old value, do not re-run it without updating.
- VF5Builder_*_before-pylon4-offset | VF5Builder.cs | +1 constant `Pylon4EastOffset=1.0` and +1 line shifting B1_Pylon_4 by +1 m x in the scene (table untouched). Revert: set 0 and BuildReal.
- VF5Builder_*_before-approach-fill-lights | VF5Builder.cs | +1 flag `ApproachFillLights` and a block adding two warm no-shadow point lights (3.0, range 5.5) at (-6.9,1.7,10.8) and (-10.8,1.7,6.9) under VF_Batch1/VF_Batch1_ApproachFillLights. Revert: set false + BuildReal.

## 2026-10-26 outer ground texture test (Director GO)
- Before: VF_OuterGround.mat _BaseColor 0.275,0.225,0.1875, no BaseMap (copy VF_OuterGround_*_before-macro-gradient.mat.txt). After: BaseMap = Textures/VF_OuterGround_MacroGradient_1024.png (baked by Reports/outer_ground_bake.py from the unedited NoDamp macro map, one cycle per 70 m, +-12 pct contrast, distance gradient to the fog colour from the parapet foot), _BaseColor white. Revert: remove BaseMap and set _BaseColor to 0.275,0.225,0.1875.
