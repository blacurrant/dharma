# Gate 1b - method statement (written BEFORE the runs; QA method point)

Parts: Altar_A (zones 0,2,3,4,5), Pillar_C (0,2; lathe-built), Banner_A (2,3,4).

For lathe-built parts the saved UVs differ from a fresh rebuild's, so the rebuild is NOT used to verify zones or to reproduce textures.
The bake runs on the SAVED production mesh and its saved UVs (the ones the shipped textures were baked from), with zone_id (mapped by geometry in Gate 1)
restoring the SRC slots. Independent evidence, none of it derived from a rebuild:
 1. Shipped-texture classification: the shipped Staging maps already encode the original zones. zone_id is rasterised through the saved UVs
    (texel-level via a margin-0 Cycles bake of the attribute; per-face at the centroid for faces >= 9 px^2) and compared with the shipped maps.
    Thresholds fixed a priori: metal if shipped metallic > 0.25; ember if shipped emission max-channel > 0.002; crimson if albedo R/(G+B) > 2.5
    and not metal/emissive; otherwise stone/charcoal (not separable). Gold vs bronze is not separable -> reported as "metal".
 2. Re-bake vs shipped maps, per zone region (texel raster): mean abs diff, % texels > 0.1, so a wrong zone mapping would pile up in one zone's texels.
 3. Pixel locations of the largest outliers are recorded.
Banner_A (non-lathe) gets the same bar. Per-zone baked metallic means come from the texel raster (sampling-independent).
Zone MD5 is asserted at: reopen, restore, bake, material swap, save, reopen. FBX uses the exact 05_export.py settings; extents/poly counts are checked
against the shipped FBX files. Optional checks (non-unique keys; the 21 PierL faces; Brazier outliers) follow after the three assets.
