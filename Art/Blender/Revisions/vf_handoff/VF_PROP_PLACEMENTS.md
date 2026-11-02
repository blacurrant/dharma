# Prop placements (existing kit parts only) - iteration 1

Machine-readable: `VF_PROP_PLACEMENTS.json` (+ `scripts/14_prop_placements.py`, which also validates each row). Unity convention: x/z metres, yaw clockwise from above, 0 = +Z (same as `TempleCourtyard_Placement.json`).

**Focal axis.** Centre → altar. The altar currently stands at the NW corner (x −14.08, z +14.08, r 19.9 m), so the list builds the hierarchy toward it *where it is*. Whether a central structure replaces or joins it is Nishant's decision; nothing here assumes it. Gameplay camera sits toward +x/−z and looks toward −x/+z, so this axis runs up the screen.

| # | Part | x, z (m) | yaw | Reason | r from centre | nearest existing |
|---|---|---|---|---|---|---|
| 1 | Brazier_A | −6.86, +10.82 | 0 | Lit pair 3 m before the stairs frames the approach and pulls the eye along the axis. Warm light, outside the clear circle. | 12.8 | Stairs_A 4.1 m |
| 2 | Brazier_A | −10.82, +6.86 | 0 | Partner of #1 (5.6 m gap). The only deliberate symmetry: the formal entrance to the focal zone. | 12.8 | Stairs_A 4.1 m |
| 3 | Banner_A | −19.40, +11.00 | 90 | Crimson (the kit's only crimson) concentrated at the focal corner = colour hierarchy. Wall-mounted: no combat footprint. | 22.3 | Wall_B 1.2 m |
| 4 | Banner_A | −11.00, +19.40 | 180 | Flanks the dais from the other wall; same yaw convention as the existing wall banners. | 22.3 | Wall_A 1.2 m |
| 5 | ColumnDrum_A | −12.00, +5.50 | 70 | Fallen drum (1.1 m tall) on the flank; its diagonal leads toward the altar without blocking the sight line. | 13.2 | Pillar_A 3.4 m |
| 6 | Rubble_A | −5.50, +12.20 | 40 | Breaks the clean floor beside the approach; 0.44 m tall. | 13.4 | Pillar_B 2.5 m |
| 7 | Rubble_B | −17.00, +3.00 | 100 | Pushes debris to the wall edge, away from the combat circle and the lane (0.30 m tall). | 17.3 | Pillar_A 2.2 m |
| 8 | Rubble_B | +15.50, +16.50 | 160 | Weights the far corner so the frame is not empty away from the altar. | 22.6 | Rubble_A 2.8 m |

Checks run by script for all 8: r ≥ 11 m (all ≥ 12.8), nothing in the r = 10 m circle, ≥ 2.2 m from every existing non-floor instance (banners excluded: they sit on walls), inside the 19.5 m wall face. Measured heights: Brazier_A 1.34 m, ColumnDrum_A 1.10 m, Rubble_A 0.44 m, Rubble_B 0.30 m, Banner_A 2.52 m (wall-mounted); the only tall pieces remain the existing pillars (6.3 m, Pillar_D 3.7 m).

**Not done / UNVERIFIED:** these are not placed or rendered in a scene (list only), so sight-line and silhouette effects from the gameplay camera are untested; collision footprints were not checked in Unity; Brazier_A light radius/intensity on the telegraph is a Unity-side question. Existing Pillar_D (−2.0, −12.5) is on the camera side of the circle and may occlude the floor from the elevated camera; flagged, not changed.
