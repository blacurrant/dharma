// Visual Foundation iteration 2: imports the cleared Environment Artist textures (copied, never moved/edited) with the
// import settings from VF_PALETTE_USAGE_NOTE.md, and builds the layered, reversible overlay stack under VF_Environment/VF_Layers.
// Art-test scene only. Materials/Textures live under Assets/ArtTest/VisualFoundation/.
using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class VF2Builder
{
    const string Root = "Assets/ArtTest/VisualFoundation";
    static readonly string[] ColorMaps = { "VF_Floor_Cracks_2048", "VF_Floor_Wear_1024", "VF_Floor_ChippedEdges_1024", "VF_Weather_MossFloorJoints_1024", "VF_Wall_RainStreaks_1024", "VF_Weather_Salt_1024", "VF_Weather_MossWallBase_1024", "VF_Weather_SootFloorRing_1024" };
    static readonly string[] DataMaps = { "VF_Floor_MacroValue_2048", "VF_Floor_MacroValue_NoDamp_2048", "VF_Floor_MacroTint_1024" };

    public static string ImportTextures()
    {
        var sb = new StringBuilder();
        foreach (var n in ColorMaps.Concat(DataMaps))
        {
            string p = Root + "/Textures/" + n + ".png"; AssetDatabase.ImportAsset(p, ImportAssetOptions.ForceUpdate);
            var ti = (TextureImporter)AssetImporter.GetAtPath(p); bool data = DataMaps.Contains(n);
            ti.textureType = TextureImporterType.Default; ti.sRGBTexture = !data; ti.alphaSource = data ? TextureImporterAlphaSource.None : TextureImporterAlphaSource.FromInput;
            ti.alphaIsTransparency = !data; ti.mipmapEnabled = true; ti.filterMode = FilterMode.Trilinear; ti.anisoLevel = data ? 1 : 4; ti.maxTextureSize = 2048;
            ti.textureCompression = TextureImporterCompression.Uncompressed; ti.npotScale = TextureImporterNPOTScale.None;
            bool clampBoth = data || n.Contains("Soot");
            ti.wrapModeU = clampBoth ? TextureWrapMode.Clamp : TextureWrapMode.Repeat;
            ti.wrapModeV = (clampBoth || n.Contains("MossWallBase")) ? TextureWrapMode.Clamp : TextureWrapMode.Repeat; // wall-base moss: U repeat, V clamp (note)
            ti.SaveAndReimport();
            var t = AssetDatabase.LoadAssetAtPath<Texture2D>(p);
            sb.AppendLine(n + ": " + t.width + "x" + t.height + " fmt=" + t.format + " sRGB=" + ti.sRGBTexture + " alphaIsTransp=" + ti.alphaIsTransparency + " wrapU/V=" + ti.wrapModeU + "/" + ti.wrapModeV + " mips=" + t.mipmapCount);
        }
        return sb.ToString();
    }

    static Texture2D Tex(string n) => AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Textures/" + n + ".png");

    static Material MakeMat(string name, string shader, Texture2D tex, int queue, params (string, float)[] f)
    {
        string p = Root + "/Materials/" + name + ".mat"; AssetDatabase.DeleteAsset(p);
        var m = new Material(Shader.Find(shader)); m.name = name; m.SetTexture("_MainTex", tex); m.renderQueue = queue;
        foreach (var kv in f) m.SetFloat(kv.Item1, kv.Item2);
        AssetDatabase.CreateAsset(m, p); return m;
    }

    static GameObject Quad(string name, Transform parent, Vector3 pos, Quaternion rot, Vector2 size, Material m)
    {
        var q = GameObject.CreatePrimitive(PrimitiveType.Quad); q.name = name; Object.DestroyImmediate(q.GetComponent<Collider>());
        q.transform.SetParent(parent, false); q.transform.position = pos; q.transform.rotation = rot; q.transform.localScale = new Vector3(size.x, size.y, 1f);
        var r = q.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; r.lightProbeUsage = LightProbeUsage.BlendProbes;
        GameObjectUtility.SetStaticEditorFlags(q, 0); return q;
    }

    // inner face plane of a wall piece: median of (vertex . n) over vertices whose normal points to the arena
    static float InnerPlane(Transform piece, Vector3 n)
    {
        var d = new List<float>();
        foreach (var mf in piece.GetComponentsInChildren<MeshFilter>())
        {
            var mesh = mf.sharedMesh; if (mesh == null) continue; var v = mesh.vertices; var nm = mesh.normals; var l2w = mf.transform.localToWorldMatrix;
            for (int i = 0; i < v.Length; i++) { var wn = l2w.MultiplyVector(nm[i]).normalized; if (Vector3.Dot(wn, n) > 0.9f) d.Add(Vector3.Dot(l2w.MultiplyPoint3x4(v[i]), n)); }
        }
        if (d.Count == 0) return float.NaN; d.Sort(); return d[Mathf.Min(d.Count - 1, (int)(d.Count * 0.985f))]; // near-max protrusion toward the arena, so the overlay is not buried inside the relief
    }

    static readonly (string part, string src, float x, float z, float yawPlusZ)[] EAProps =
    {
        ("Brazier_A", "LAY_Brazier_A_003", -6.86f, 10.82f, 0), ("Brazier_A", "LAY_Brazier_A_003", -10.82f, 6.86f, 0),
        ("Banner_A", "LAY_Banner_A_003", -19.40f, 11.00f, 90), ("Banner_A", "LAY_Banner_A_003", -11.00f, 19.40f, 180),
        ("ColumnDrum_A", "LAY_ColumnDrum_A_001", -12.00f, 5.50f, 70), ("Rubble_A", "LAY_Rubble_A_001", -5.50f, 12.20f, 40),
        ("Rubble_B", "LAY_Rubble_B_001", -17.00f, 3.00f, 100), ("Rubble_B", "LAY_Rubble_B_001", 15.50f, 16.50f, 160),
    };

    public static string Build()
    {
        var sc = EditorSceneManager.GetActiveScene();
        if (sc.path != "Assets/Scenes/ArtTest_VisualFoundation.unity") return "WRONG SCENE " + sc.path;
        var root = GameObject.Find("VF_Environment").transform; var sb = new StringBuilder();
        // remove iteration-1 placeholders that now have textures: floor mottling, moss placeholders, the 6 iteration-1 props
        foreach (var n in new[] { "VF_FloorOverlays", "VF_Props", "VF_Layers" }) { var o = root.Find(n); if (o != null) Object.DestroyImmediate(o.gameObject); }
        var wb = root.Find("VF_WallBase"); if (wb != null) foreach (var c in wb.Cast<Transform>().Where(c => c.name.StartsWith("Moss")).ToList()) Object.DestroyImmediate(c.gameObject);
        var layers = new GameObject("VF_Layers").transform; layers.SetParent(root, false);

        // floor top height (median of max vertex Y per floor tile)
        var tops = new List<float>(); foreach (Transform t in GameObject.Find("LAY_Floor").transform) { float mx = -9f; foreach (var mf in t.GetComponentsInChildren<MeshFilter>()) { var l2w = mf.transform.localToWorldMatrix; foreach (var v in mf.sharedMesh.vertices) mx = Mathf.Max(mx, l2w.MultiplyPoint3x4(v).y); } tops.Add(mx); }
        tops.Sort(); float floorTop = tops[tops.Count / 2]; float fy = floorTop + 0.014f;
        sb.AppendLine("floor top y: min " + tops[0].ToString("F3") + " median " + floorTop.ToString("F3") + " max " + tops[tops.Count - 1].ToString("F3") + " -> overlay quads at y=" + fy.ToString("F3"));
        var down = Quaternion.Euler(90, 0, 0); var big = new Vector2(40, 40); var center = new Vector3(0, fy, 0);

        GameObject Group(string n, bool on = true) { var g = new GameObject(n); g.transform.SetParent(layers, false); g.SetActive(on); return g; }
        // L01 macro value (damped asset) and the exclusive alternatives; L02 macro tint
        var g1 = Group("L01_MacroValue_Damped"); Quad("quad", g1.transform, center, down, big, MakeMat("VF2_MacroValue_Damped", "VF/WorldMultiply", Tex("VF_Floor_MacroValue_2048"), 2501, ("_Opacity", 0.75f), ("_IsTint", 0f), ("_CenterW", 1f)));
        var g1b = Group("L01b_MacroValue_NoDamp_ShaderRadial", false); Quad("quad", g1b.transform, center, down, big, MakeMat("VF2_MacroValue_NoDamp_Radial", "VF/WorldMultiply", Tex("VF_Floor_MacroValue_NoDamp_2048"), 2501, ("_Opacity", 0.75f), ("_IsTint", 0f), ("_CenterW", 0.25f), ("_RadIn", 8f), ("_RadOut", 14f)));
        var g1c = Group("L01c_MacroValue_NoDamp_NoWeight", false); Quad("quad", g1c.transform, center, down, big, MakeMat("VF2_MacroValue_NoDamp_Flat", "VF/WorldMultiply", Tex("VF_Floor_MacroValue_NoDamp_2048"), 2501, ("_Opacity", 0.75f), ("_IsTint", 0f), ("_CenterW", 1f)));
        var g2 = Group("L02_MacroTint"); Quad("quad", g2.transform, center + Vector3.up * 0.0005f, down, big, MakeMat("VF2_MacroTint", "VF/WorldMultiply", Tex("VF_Floor_MacroTint_1024"), 2502, ("_Opacity", 0.60f), ("_IsTint", 1f), ("_CenterW", 1f)));

        // floor colour overlays (lit alpha-lerp). inside-circle weight from the note; ramp 10 -> 13 m
        void FloorLayer(string gname, string mname, string tex, float tile, float op, float cw, int q)
        {
            var g = Group(gname); Quad("quad", g.transform, center + Vector3.up * (q - 2500) * 0.0004f, down, big,
                MakeMat(mname, "VF/WorldOverlayLit", Tex(tex), q, ("_Opacity", op), ("_TileU", tile), ("_TileV", tile), ("_MapMode", 0f), ("_CenterW", cw), ("_RadIn", 10f), ("_RadOut", 13f), ("_Smooth", 0.05f)));
        }
        FloorLayer("L03_Cracks", "VF2_Cracks", "VF_Floor_Cracks_2048", 8f, 0.75f, 0.35f, 2503);
        {   // second, off-axis copies of cracks/wear (different scale and rotation, lower opacity) to break the 8 m / 4 m exact repetition. Test layers, default OFF.
            var gb = Group("L03b_Cracks_SecondScale", false); var mb2 = MakeMat("VF2_Cracks_B", "VF/WorldOverlayLit", Tex("VF_Floor_Cracks_2048"), 2511, ("_Opacity", 0.55f), ("_TileU", 11.3f), ("_TileV", 11.3f), ("_MapMode", 0f), ("_CenterW", 0.35f), ("_RadIn", 10f), ("_RadOut", 13f), ("_Smooth", 0.05f), ("_Rot", 27f)); mb2.SetVector("_UVOff", new Vector4(0.31f, 0.57f, 0, 0)); Quad("quad", gb.transform, center + Vector3.up * 0.0012f, down, big, mb2);
            var gw = Group("L04b_Wear_SecondScale", false); var mw2 = MakeMat("VF2_Wear_B", "VF/WorldOverlayLit", Tex("VF_Floor_Wear_1024"), 2512, ("_Opacity", 0.30f), ("_TileU", 5.7f), ("_TileV", 5.7f), ("_MapMode", 0f), ("_CenterW", 0.40f), ("_RadIn", 10f), ("_RadOut", 13f), ("_Smooth", 0.05f), ("_Rot", -19f)); mw2.SetVector("_UVOff", new Vector4(0.12f, 0.73f, 0, 0)); Quad("quad", gw.transform, center + Vector3.up * 0.0016f, down, big, mw2);
        }
        {   // per-cell mirror/rotate variants of cracks (8 m cells) and wear (4 m cells): exact-repeat breaker, seams possible at cell borders. Test layers, default OFF.
            var gc = Group("L03c_Cracks_PerCellFlip", false); Quad("quad", gc.transform, center + Vector3.up * 0.0020f, down, big, MakeMat("VF2_Cracks_CellVar", "VF/WorldOverlayLit", Tex("VF_Floor_Cracks_2048"), 2513, ("_Opacity", 0.75f), ("_TileU", 8f), ("_TileV", 8f), ("_MapMode", 0f), ("_CenterW", 0.35f), ("_RadIn", 10f), ("_RadOut", 13f), ("_Smooth", 0.05f), ("_CellVar", 1f)));
            var gv2 = Group("L04c_Wear_PerCellFlip", false); Quad("quad", gv2.transform, center + Vector3.up * 0.0024f, down, big, MakeMat("VF2_Wear_CellVar", "VF/WorldOverlayLit", Tex("VF_Floor_Wear_1024"), 2514, ("_Opacity", 0.50f), ("_TileU", 4f), ("_TileV", 4f), ("_MapMode", 0f), ("_CenterW", 0.40f), ("_RadIn", 10f), ("_RadOut", 13f), ("_Smooth", 0.05f), ("_CellVar", 1f)));
        }
        FloorLayer("L04_Wear", "VF2_Wear", "VF_Floor_Wear_1024", 4f, 0.50f, 0.40f, 2504);
        FloorLayer("L05_ChippedEdges", "VF2_ChippedEdges", "VF_Floor_ChippedEdges_1024", 2f, 0.85f, 0.50f, 2505);
        FloorLayer("L06_MossJoints", "VF2_MossJoints", "VF_Weather_MossFloorJoints_1024", 2f, 0.80f, 0.0f, 2506);
        FloorLayer("L07_Salt", "VF2_Salt", "VF_Weather_Salt_1024", 2f, 0.55f, 0.30f, 2507);

        // wall layers: one quad per wall piece on its inner face (so arch gaps stay open)
        var rain = MakeMat("VF2_WallRain", "VF/WorldOverlayLit", Tex("VF_Wall_RainStreaks_1024"), 2508, ("_Opacity", 0.65f), ("_TileU", 3f), ("_TileV", 3f), ("_CenterW", 1f), ("_RadIn", 0f), ("_RadOut", 0.01f), ("_VClip", 0f), ("_Smooth", 0.05f));
        var mossW = MakeMat("VF2_WallMossBase", "VF/WorldOverlayLit", Tex("VF_Weather_MossWallBase_1024"), 2509, ("_Opacity", 0.80f), ("_TileU", 3f), ("_TileV", 3f), ("_CenterW", 1f), ("_RadIn", 0f), ("_RadOut", 0.01f), ("_VClip", 1f), ("_Smooth", 0.05f));
        var g8 = Group("L08_WallRainStreaks"); var g9 = Group("L09_WallMossBase"); int walls = 0;
        foreach (Transform piece in GameObject.Find("LAY_Walls").transform)
        {
            var p = piece.position; Vector3 n; if (Mathf.Abs(Mathf.Abs(p.x) - 20f) < 0.6f) n = new Vector3(-Mathf.Sign(p.x), 0, 0); else if (Mathf.Abs(Mathf.Abs(p.z) - 20f) < 0.6f) n = new Vector3(0, 0, -Mathf.Sign(p.z)); else continue;
            float d = InnerPlane(piece, n); if (float.IsNaN(d)) { sb.AppendLine("no inner plane for " + piece.name); continue; }
            Vector3 c = (n.x != 0) ? new Vector3(d * n.x, 1.5f, p.z) : new Vector3(p.x, 1.5f, d * n.z); c += n * 0.012f;
            var rot = Quaternion.LookRotation(n);
            foreach (var (g, m) in new[] { (g8, rain), (g9, mossW) })
            {
                var m2 = new Material(m); // per-wall-axis map mode (X-facing planes use u=z, Z-facing use u=x)
                var q = Quad(piece.name, g.transform, c, rot, new Vector2(4f, 3f), m); q.GetComponent<MeshRenderer>().sharedMaterial = m;
                var mpb = new MaterialPropertyBlock(); q.GetComponent<MeshRenderer>().GetPropertyBlock(mpb); mpb.SetFloat("_MapMode", n.x != 0 ? 2f : 1f); q.GetComponent<MeshRenderer>().SetPropertyBlock(mpb);
                Object.DestroyImmediate(m2);
            }
            walls++; if (walls <= 3) sb.AppendLine("wall " + piece.name + " n=" + n + " inner plane d=" + d.ToString("F3") + " (piece pos " + p + ")");
        }
        sb.AppendLine("wall quads per layer: " + walls);

        // soot: asymmetric smudge decals near the 4 floor braziers only (existing 003/004 + the two new approach braziers), random yaw per instance
        var g10 = Group("L10_SootSmudges"); var soot = MakeMat("VF2_Soot", "VF/WorldOverlayLit", Tex("VF_Weather_SootFloorRing_1024"), 2510, ("_Opacity", 0.85f), ("_MapMode", 3f), ("_CenterW", 1f), ("_RadIn", 0f), ("_RadOut", 0.01f), ("_Smooth", 0.05f));
        var rng = new System.Random(7); var sootAt = new List<Vector2> { new Vector2(-1.4f, 17.6f), new Vector2(9.4f, 17.6f), new Vector2(-6.86f, 10.82f), new Vector2(-10.82f, 6.86f) };
        foreach (var s in sootAt) { float yaw = (float)rng.NextDouble() * 360f; Quad("soot_" + s.x + "_" + s.y, g10.transform, new Vector3(s.x, fy + 0.012f, s.y), Quaternion.Euler(0, yaw, 0) * down, new Vector2(3.2f, 3.2f), soot); }

        // approach-brazier warm point lights (test layer, default OFF): amber, no shadows, local range
        var g11 = Group("L11_BrazierLights", false); foreach (var bp in new[] { new Vector3(-6.86f, 1.7f, 10.82f), new Vector3(-10.82f, 1.7f, 6.86f) })
        { var lo = new GameObject("BrazierGlow"); lo.transform.SetParent(g11.transform, false); lo.transform.position = bp; var lt = lo.AddComponent<Light>(); lt.type = LightType.Point; lt.color = new Color(1f, 0.62f, 0.30f); lt.intensity = 3f; lt.range = 5.5f; lt.shadows = LightShadows.None; lt.lightmapBakeType = LightmapBakeType.Realtime; }
        // props: the Environment Artist's list (8, existing kit parts), cloned from the matching scene instances; yaw column plusZ -> scene (minusZ) = +180
        var pr = new GameObject("VF_Props").transform; pr.SetParent(root, false); int pi = 0;
        foreach (var e in EAProps)
        {
            var src = GameObject.Find(e.src); if (src == null) { sb.AppendLine("missing source " + e.src); continue; }
            var g = Object.Instantiate(src, pr); g.name = "VFProp_" + (++pi) + "_" + e.part; g.transform.position = new Vector3(e.x, src.transform.position.y > 0.3f && e.part == "Banner_A" ? src.transform.position.y : 0f, e.z); g.transform.rotation = Quaternion.Euler(0, (e.yawPlusZ + 180f) % 360f, 0);
            foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.receiveGI = ReceiveGI.LightProbes;
        }
        sb.AppendLine("props placed: " + pi);
        EditorSceneManager.MarkSceneDirty(sc); EditorSceneManager.SaveScene(sc); AssetDatabase.SaveAssets();
        return sb.ToString();
    }

    public static string ShaderMessages()
    {
        var sb = new StringBuilder();
        foreach (var n in new[] { "VF/WorldOverlayLit", "VF/WorldMultiply" }) { var s = Shader.Find(n); sb.AppendLine(n + ": " + (s == null ? "NOT FOUND" : "found") + (s != null ? " supported=" + s.isSupported + " errors=" + ShaderUtil.GetShaderMessageCount(s) : ""));
            if (s != null) for (int i = 0; i < ShaderUtil.GetShaderMessageCount(s); i++) { var m = ShaderUtil.GetShaderMessages(s)[i]; sb.AppendLine("   " + m.severity + " " + m.message + " line " + m.line); } }
        return sb.ToString();
    }
}
