// Environment Artist Batch 2 integration (run through `unity command script run --file <this> --entry EA2Builder.<Method>`; compiled in memory, NOT part of the Unity project).
// Copies (never moves) FBX + textures from Art/Blender/Revisions/batch2 into Assets/ArtTest/VisualFoundation/Art2, builds URP Lit material instances,
// and (re)builds the VF_EA_* roots in the active scene. Never edits original assets; the only change to non-EA objects is SetActive(false) on the
// Wall_Tall bays that a lamp bay replaces (logged, reversible: RestoreBays()).
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class EA2Builder
{
    const string Src = "/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/batch2";
    const string Dst = "Assets/ArtTest/VisualFoundation/Art2";
    static readonly string[] Kit = { "Wall_Tall_Lamp_A", "Shrine_Backdrop_A", "Column_Tall_A", "Flagstone_A", "Flagstone_B", "Flagstone_C", "Flagstone_D", "Kerb_A", "Wall_Low_Broken_A", "Wall_Low_Broken_B" };
    static readonly string[] Drapes = { "Drape_A", "Drape_B", "Drape_C" };

    // ------------------------------------------------------------------ import
    public static string Import()
    {
        var sb = new StringBuilder();
        foreach (var d in new[] { "", "/Models", "/Textures", "/Materials" }) if (!AssetDatabase.IsValidFolder(Dst + d)) { if (d == "") Directory.CreateDirectory(Dst); else Directory.CreateDirectory(Dst + d); }
        int n = 0;
        foreach (var kind in new[] { "Models", "Textures" })
            foreach (var f in Directory.GetFiles(Src + "/" + kind))
            {
                if (f.EndsWith(".meta")) continue;
                string dst = Dst + "/" + kind + "/" + Path.GetFileName(f);
                if (!File.Exists(dst) || new FileInfo(f).Length != new FileInfo(dst).Length || File.GetLastWriteTimeUtc(f) > File.GetLastWriteTimeUtc(dst)) { File.Copy(f, dst, true); n++; }
            }
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        sb.AppendLine("copied " + n + " files");
        foreach (var f in Directory.GetFiles(Dst + "/Textures", "*.png"))
        {
            string p = f.Replace('\\', '/'); var ti = (TextureImporter)AssetImporter.GetAtPath(p); if (ti == null) continue; string nm = Path.GetFileNameWithoutExtension(p);
            bool normal = nm.EndsWith("_Normal"), mask = nm.EndsWith("_Mask");
            ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default; ti.sRGBTexture = !(normal || mask); ti.alphaIsTransparency = false; ti.mipmapEnabled = true;
            ti.filterMode = FilterMode.Bilinear; ti.anisoLevel = 4; ti.maxTextureSize = 2048; ti.textureCompression = TextureImporterCompression.Compressed; ti.wrapMode = TextureWrapMode.Repeat;
            ti.SaveAndReimport();
        }
        var shader = Shader.Find("Universal Render Pipeline/Lit");
        foreach (var part in Kit) { var m = KitMaterial(part, shader); RemapFbx(part, m); sb.AppendLine("material " + m.name); }
        foreach (var dr in Drapes) RemapFbx(dr, DrapeMaterial("Ochre", new Color(0.62f, 0.44f, 0.16f), shader));
        DrapeMaterial("Crimson", new Color(0.42f, 0.09f, 0.11f), shader); DrapeMaterial("Indigo", new Color(0.17f, 0.20f, 0.38f), shader);
        AssetDatabase.SaveAssets(); return sb.ToString();
    }

    static Texture2D Tex(string part, string suffix) => AssetDatabase.LoadAssetAtPath<Texture2D>(Dst + "/Textures/ENV_Temple_" + part + "_" + suffix + ".png");

    static Material KitMaterial(string part, Shader shader)
    {
        string mp = Dst + "/Materials/MI_Temple_" + part + ".mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(mp);
        if (m == null) { m = new Material(shader) { name = "MI_Temple_" + part }; AssetDatabase.CreateAsset(m, mp); }
        m.shader = shader; m.SetTexture("_BaseMap", Tex(part, "BaseColor")); m.SetColor("_BaseColor", Color.white);
        var n = Tex(part, "Normal"); m.SetTexture("_BumpMap", n); m.SetFloat("_BumpScale", 1f); if (n != null) m.EnableKeyword("_NORMALMAP");
        var mask = Tex(part, "Mask"); m.SetTexture("_MetallicGlossMap", mask); m.SetTexture("_OcclusionMap", mask); m.SetFloat("_Metallic", 1f); m.SetFloat("_Smoothness", 1f); m.SetFloat("_SmoothnessTextureChannel", 0f); m.SetFloat("_OcclusionStrength", 1f);
        if (mask != null) { m.EnableKeyword("_METALLICSPECGLOSSMAP"); m.EnableKeyword("_OCCLUSIONMAP"); }
        var em = Tex(part, "Emission");
        if (em != null) { m.SetTexture("_EmissionMap", em); m.SetColor("_EmissionColor", Color.white * 1.6f); m.EnableKeyword("_EMISSION"); m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.BakedEmissive; }
        else { m.SetColor("_EmissionColor", Color.black); m.DisableKeyword("_EMISSION"); }
        m.SetFloat("_Surface", 0f); m.SetFloat("_Cull", 2f); m.enableInstancing = true; EditorUtility.SetDirty(m); return m;
    }

    static Material DrapeMaterial(string nm, Color c, Shader shader)
    {
        string mp = Dst + "/Materials/MI_Drape_" + nm + ".mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(mp);
        if (m == null) { m = new Material(shader) { name = "MI_Drape_" + nm }; AssetDatabase.CreateAsset(m, mp); }
        m.shader = shader; m.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(Dst + "/Textures/ENV_Temple_Drape_Weave.png")); m.SetColor("_BaseColor", c);
        m.SetFloat("_Metallic", 0f); m.SetFloat("_Smoothness", 0.18f); m.SetFloat("_Cull", 0f); m.enableInstancing = true; EditorUtility.SetDirty(m); return m;   // Cull Off = double sided cloth
    }

    static void RemapFbx(string part, Material m)
    {
        string fbx = Dst + "/Models/ENV_Temple_" + part + ".fbx"; var model = AssetDatabase.LoadAssetAtPath<GameObject>(fbx); var imp = (ModelImporter)AssetImporter.GetAtPath(fbx); if (model == null || imp == null) return;
        var src = model.GetComponentsInChildren<Renderer>().SelectMany(r => r.sharedMaterials).Where(x => x != null).Select(x => x.name).Distinct().ToList();
        foreach (var sn in src) imp.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), sn), m);
        imp.SaveAndReimport();
    }

    static GameObject Prefab(string part, string dir = null) => AssetDatabase.LoadAssetAtPath<GameObject>((dir ?? Dst) + "/Models/ENV_Temple_" + part + ".fbx");
    const string B1Dir = "Assets/ArtTest/VisualFoundation/Batch1";

    static Material Tint(string baseName, string tintName, Color tint)
    {
        string mp = Dst + "/Materials/" + baseName + "_" + tintName + ".mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(mp);
        if (m == null) { var b = AssetDatabase.LoadAssetAtPath<Material>(Dst + "/Materials/" + baseName + ".mat"); m = new Material(b) { name = baseName + "_" + tintName }; AssetDatabase.CreateAsset(m, mp); }
        m.SetColor("_BaseColor", tint); m.enableInstancing = true; EditorUtility.SetDirty(m); return m;
    }

    // ------------------------------------------------------------------ geometry helpers
    struct Obb { public Vector2 c; public Vector2 ax, az; public float hx, hz; }   // ax/az unit axes in world (x,z); half extents
    static bool Overlap(Obb a, Obb b, float margin)
    {
        foreach (var axis in new[] { a.ax, a.az, b.ax, b.az })
        {
            float ra = a.hx * Mathf.Abs(Vector2.Dot(a.ax, axis)) + a.hz * Mathf.Abs(Vector2.Dot(a.az, axis));
            float rb = b.hx * Mathf.Abs(Vector2.Dot(b.ax, axis)) + b.hz * Mathf.Abs(Vector2.Dot(b.az, axis));
            if (Mathf.Abs(Vector2.Dot(b.c - a.c, axis)) > ra + rb + margin) return false;
        }
        return true;
    }
    static Obb MakeObb(Vector2 c, float yawDeg, float hx, float hz)
    {
        float r = yawDeg * Mathf.Deg2Rad; return new Obb { c = c, ax = new Vector2(Mathf.Cos(r), -Mathf.Sin(r)), az = new Vector2(Mathf.Sin(r), Mathf.Cos(r)), hx = hx, hz = hz };
    }

    static readonly Dictionary<string, Vector2> Dim = new Dictionary<string, Vector2> { { "Flagstone_A", new Vector2(1.15f, 2.04f) }, { "Flagstone_B", new Vector2(2.03f, 3.03f) }, { "Flagstone_C", new Vector2(3.06f, 3.03f) }, { "Flagstone_D", new Vector2(1.50f, 1.53f) } };

    static Transform Root(string name, Scene_ s) { var old = GameObject.Find(name); if (old != null) Object.DestroyImmediate(old); var g = new GameObject(name); return g.transform; }
    class Scene_ { }

    static GameObject Spawn(string part, Transform parent, string nm, Vector3 pos, float yaw, Vector3 scale, Material mat = null, bool cast = true, bool isStatic = true, string dir = null)
    {
        var g = (GameObject)PrefabUtility.InstantiatePrefab(Prefab(part, dir)); g.name = nm; g.transform.SetParent(parent, false); g.transform.position = pos; g.transform.rotation = Quaternion.Euler(0, yaw, 0); g.transform.localScale = scale;
        foreach (var mr in g.GetComponentsInChildren<MeshRenderer>()) { if (mat != null) mr.sharedMaterial = mat; mr.shadowCastingMode = cast ? ShadowCastingMode.On : ShadowCastingMode.Off; mr.receiveShadows = true; mr.receiveGI = ReceiveGI.LightProbes; }
        if (isStatic) GameObjectUtility.SetStaticEditorFlags(g, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccluderStatic | StaticEditorFlags.OccludeeStatic);
        return g;
    }

    static List<Bounds> Obstacles()
    {
        var res = new List<Bounds>();
        foreach (var root in new[] { "LAY_Landmarks", "LAY_Props", "VF_Props", "VF_Batch1_Pylons", "VF_Batch1_Ruins", "VF_EA_Columns", "VF_EA_Shrine", "VF_EA_East" })
        {
            var go = GameObject.Find(root); if (go == null) continue;
            foreach (var r in go.GetComponentsInChildren<Renderer>()) res.Add(r.bounds);
        }
        return res;
    }
    static bool BlockedObb(List<Bounds> obs, Obb ob, float margin)
    {
        foreach (var b in obs)
        {
            var o2 = new Obb { c = new Vector2(b.center.x, b.center.z), ax = Vector2.right, az = Vector2.up, hx = b.extents.x, hz = b.extents.z };
            if (Overlap(ob, o2, margin)) return true;
        }
        return false;
    }
    static bool Blocked(List<Bounds> obs, Vector2 c, float rad)
    {
        foreach (var b in obs) { float dx = Mathf.Max(b.min.x - c.x, 0, c.x - b.max.x), dz = Mathf.Max(b.min.z - c.y, 0, c.y - b.max.z); if (dx * dx + dz * dz < rad * rad) return true; }
        return false;
    }

    // ------------------------------------------------------------------ paving
    public static string Paving() { return PlacePaving(7); }
    public static string Shrine() { return PlaceShrine(24.2f, 0.9f); }
    public static string Arch() { return PlaceArchitecture(); }
    public static string PlacePaving(int seed)
    {
        var sb = new StringBuilder(); var rnd = new System.Random(seed); var root = Root("VF_EA_Paving", null); var obs = Obstacles();
        var placed = new List<Obb>(); int nFlag = 0, nKerb = 0, skipped = 0, skipObs = 0, skipOv = 0;
        var tintsFull = new[] { ("warm", new Color(1.10f, 1.04f, 0.94f)), ("neutral", new Color(1.06f, 1.04f, 1.00f)), ("cool", new Color(0.96f, 1.00f, 1.08f)), ("grey", new Color(1.02f, 1.02f, 1.03f)), ("dark", new Color(0.90f, 0.88f, 0.84f)), ("warm2", new Color(1.13f, 1.06f, 0.96f)) };
        var tintsLow = new[] { ("lowA", new Color(1.03f, 1.02f, 1.00f)), ("lowB", new Color(1.00f, 1.01f, 1.03f)) };
        var kerbMat = Tint("MI_Temple_Kerb_A", "worn", new Color(1.05f, 1.00f, 0.95f));
        bool PlaceFlag(string type, Vector2 c, float yaw, float sc, float ysc, (string, Color) tint, Transform parent, bool checkObs = true)
        {
            var d = Dim[type]; var ob = MakeObb(c, yaw, d.x * 0.5f * sc, d.y * 0.5f * sc);
            if (checkObs && BlockedObb(obs, ob, 0.2f)) { skipped++; skipObs++; return false; }
            if (Mathf.Abs(c.x) > 19.0f || Mathf.Abs(c.y) > 19.0f) { skipped++; return false; }
            foreach (var p in placed) { if ((p.c - c).sqrMagnitude < 36f && Overlap(ob, p, -0.02f)) { skipped++; skipOv++; return false; } }
            placed.Add(ob);
            var mat = Tint("MI_Temple_" + type, tint.Item1, tint.Item2);
            Spawn(type, parent, "Flag_" + type + "_" + nFlag, new Vector3(c.x, 0f, c.y), yaw, new Vector3(sc, ysc * 1.5f, sc), mat, false); nFlag++; return true;
        }
        // --- 1. processional way: arch (4,20) -> dais stairs foot
        var way = new[] { new Vector2(4f, 19.4f), new Vector2(4f, 13.4f), new Vector2(-1.6f, 11.6f), new Vector2(-7.4f, 10.4f), new Vector2(-9.6f, 9.4f) };
        var gWay = new GameObject("Way").transform; gWay.SetParent(root, false); float W = 4.6f;
        for (int sidx = 0; sidx + 1 < way.Length; sidx++)
        {
            var a = way[sidx]; var b = way[sidx + 1]; float L = (b - a).magnitude; var u = (b - a).normalized; var v = new Vector2(-u.y, u.x); float yawU = Mathf.Atan2(u.x, u.y) * Mathf.Rad2Deg;   // local z along u
            float s = 0f; int row = 0;
            while (s < L - 0.3f)
            {
                string t = new[] { "Flagstone_A", "Flagstone_B", "Flagstone_C", "Flagstone_D", "Flagstone_B", "Flagstone_A" }[rnd.Next(6)]; var d = Dim[t];
                bool alongZ = rnd.Next(2) == 0; float depth = alongZ ? d.y : d.x, lat = alongZ ? d.x : d.y; float yaw = yawU + (alongZ ? 0f : 90f) + (float)(rnd.NextDouble() - 0.5) * 2f;
                float c = -W * 0.5f + (float)(rnd.NextDouble() * 0.12);
                var tint = tintsFull[rnd.Next(tintsFull.Length)];
                while (c < W * 0.5f - 0.7f)
                {
                    float rem = W * 0.5f - c; float scl = 1f; string tt = t; float lw = lat;
                    if (rem < lat + 0.1f) { tt = "Flagstone_D"; var dd = Dim[tt]; lw = dd.x; scl = Mathf.Clamp((rem - 0.05f) / lw, 0.6f, 1.25f); lw *= scl; }
                    float cl = c + lw * 0.5f + (float)(rnd.NextDouble() - 0.5) * 0.06f; float cu = s + depth * 0.5f + (float)(rnd.NextDouble() - 0.5) * 0.06f;
                    if (c < -W * 0.5f + 0.4f || c > W * 0.5f - 1.0f) cl += (rnd.NextDouble() < 0.5 ? 1 : -1) * (float)rnd.NextDouble() * 0.12f;
                    var pos = a + u * cu + v * cl; if (rnd.NextDouble() > 0.05) PlaceFlag(tt, pos, yaw + (tt == "Flagstone_D" ? (float)rnd.NextDouble() * 90f : 0f), scl, 1f, tint, gWay);
                    c += lw + 0.07f; if (rnd.NextDouble() < 0.5) tint = tintsFull[rnd.Next(tintsFull.Length)];
                }
                s += depth + 0.07f; row++;
            }
            // kerb strips on both sides (3 m pieces, local x along the path)
            float yawK = Mathf.Atan2(-u.y, u.x) * Mathf.Rad2Deg;
            foreach (float side in new[] { -1f, 1f })
                for (float k = 0.9f; k < L - 2.2f && false; k += 3.02f)
                {
                    float len = Mathf.Min(3f, L - 0.9f - k); var pos = a + u * (k + 1.5f) + v * side * (W * 0.5f + 0.26f);
                    if (Blocked(obs, pos, 0.9f)) continue; if (Mathf.Abs(pos.x) > 19.3f || Mathf.Abs(pos.y) > 19.3f) continue;
                    Spawn("Kerb_A", gWay, "Kerb_" + nKerb++, new Vector3(pos.x, 0f, pos.y), yawK + (rnd.NextDouble() < 0.5 ? 0f : 180f), new Vector3(len / 3f, 1.8f, 2.0f), kerbMat, false);
                }
        }
        // --- 2. outer ring patches (r 12.5..18.6): clusters of 3-5 stones
        var gPatch = new GameObject("OuterPatches").transform; gPatch.SetParent(root, false); int patches = 0;
        for (int tries = 0; tries < 400 && patches < 14; tries++)
        {
            float ang = (float)(rnd.NextDouble() * 360f) * Mathf.Deg2Rad; float rr = 12.5f + (float)rnd.NextDouble() * 6.0f; var c0 = new Vector2(Mathf.Cos(ang) * rr, Mathf.Sin(ang) * rr);
            if (Mathf.Abs(c0.x) > 17f || Mathf.Abs(c0.y) > 17f) continue; if (c0.x > 0 && c0.y > 8 ) { if (Mathf.Abs(c0.x - 4f) < 5f) continue; }
            if (placed.Any(p => (p.c - c0).sqrMagnitude < 9f)) continue; if (Blocked(obs, c0, 2.0f)) continue;
            int cnt = 3 + rnd.Next(3), got = 0; float yaw0 = (float)rnd.NextDouble() * 180f; var tint = tintsFull[rnd.Next(tintsFull.Length)];
            for (int q = 0; q < cnt; q++)
            {
                string t = new[] { "Flagstone_A", "Flagstone_B", "Flagstone_C", "Flagstone_D", "Flagstone_B" }[rnd.Next(5)]; float ang2 = (float)rnd.NextDouble() * 6.28f, off = q == 0 ? 0f : 1.4f + (float)rnd.NextDouble() * 1.4f;
                if (PlaceFlag(t, c0 + new Vector2(Mathf.Cos(ang2), Mathf.Sin(ang2)) * off, yaw0 + (float)(rnd.NextDouble() - 0.5) * 24f + (rnd.Next(2) == 0 ? 0f : 90f), 0.9f + (float)rnd.NextDouble() * 0.2f, 1f, tint, gPatch)) got++;
            }
            if (got > 1) patches++;
        }
        // --- 3. inside the 10 m clear circle: LOW relief (top ~0.018 m, under the 0.03 telegraph), near-neutral tint, low contrast
        var gLow = new GameObject("CentreLowContrast").transform; gLow.SetParent(root, false); int low = 0;
        for (int tries = 0; tries < 300 && low < 0; tries++)
        {
            float ang = (float)(rnd.NextDouble() * 6.283f), rr = 1.6f + (float)rnd.NextDouble() * 7.4f; var c0 = new Vector2(Mathf.Cos(ang) * rr, Mathf.Sin(ang) * rr);
            string t = new[] { "Flagstone_B", "Flagstone_C", "Flagstone_B" }[rnd.Next(3)]; var d = Dim[t]; if (c0.magnitude + Mathf.Max(d.x, d.y) * 0.5f > 10.0f) continue;
            if (PlaceFlag(t, c0, (float)rnd.NextDouble() * 180f, 1f, 0.3f, tintsLow[rnd.Next(2)], gLow, false)) low++;
        }
        sb.AppendLine("flags=" + nFlag + " kerbs=" + nKerb + " skipped=" + skipped + " (obstacle " + skipObs + ", overlap " + skipOv + ")" + " patches=" + patches + " centreLow=" + low); return sb.ToString();
    }

    // ------------------------------------------------------------------ lamp bays + drapes + shrine + columns
    static GameObject Bay(string name) => GameObject.Find(name);

    public static string PlaceArchitecture()
    {
        var sb = new StringBuilder(); var sc = EditorSceneManager.GetActiveScene();
        // --- lamp bays replace selected Wall_Tall bays (the original instance is only deactivated; RestoreBays reverses it)
        var rootW = Root("VF_EA_Walls", null); var rootL = Root("VF_EA_LampLights", null); var rootD = Root("VF_EA_Drapes", null);
        var rep = new[] { "VF_B1_B1_WallTall_A_N-14", "VF_B1_B1_WallTall_A_N-10", "VF_B1_B1_WallTall_B_W+06", "VF_B1_B1_WallTall_A_W+10", "VF_B1_B1_WallTall_A_W+02", "VF_B1_B1_WallTall_A_W-06" };
        // names in the scene are VF_B1_<instance>; instance = B1_WallTall_<v>_<N|W><nn>
        var all = Object.FindObjectsByType<Transform>(FindObjectsInactive.Include).Where(t => t.name.StartsWith("VF_B1_B1_WallTall_")).ToList();
        sb.AppendLine("existing bay instances: " + string.Join(",", all.Select(t => t.name.Replace("VF_B1_B1_WallTall_", "")).OrderBy(x => x)));
        var lampSet = new HashSet<string> { "N-14", "N-10", "W+06", "W+10", "W+02", "W-06" }; int lamps = 0;
        foreach (var t in all)
        {
            string key = t.name.Substring("VF_B1_B1_WallTall_".Length + 2);
            bool lamp = lampSet.Contains(key);
            if (lamp)
            {
                t.gameObject.SetActive(false);
                var g = Spawn("Wall_Tall_Lamp_A", rootW, "VF_EA_LampBay_" + key, t.position, t.eulerAngles.y, Vector3.one, null, true);
                lamps++;
                // warm lamp light in front of the row of niches (arena side), no shadows
                Vector3 inward = key[0] == 'N' ? new Vector3(0, 0, -1) : new Vector3(1, 0, 0);
                var lo = new GameObject("VF_EA_LampLight_" + key); lo.transform.SetParent(rootL, false); lo.transform.position = t.position + inward * 0.9f + Vector3.up * 3.1f;
                var lt = lo.AddComponent<Light>(); lt.type = LightType.Point; lt.color = new Color(1f, 0.58f, 0.24f); lt.intensity = 3.2f; lt.range = 6.5f; lt.shadows = LightShadows.None;
            }
        }
        sb.AppendLine("lamp bays=" + lamps);
        // --- drapes: hang from bay tops. For every remaining (non-lamp) bay choose a pattern; lamp bays get a narrow Drape_B on the pier joint.
        var rnd = new System.Random(11); var cols = new[] { "Ochre", "Crimson", "Indigo" }; int nd = 0; int ci = 0;
        foreach (var t in all.OrderBy(x => x.name))
        {
            string key = t.name.Substring("VF_B1_B1_WallTall_".Length + 2); bool north = key[0] == 'N'; bool lamp = lampSet.Contains(key); bool tallB = t.name.Contains("WallTall_B");
            Vector3 inward = north ? new Vector3(0, 0, -1) : new Vector3(1, 0, 0); Vector3 along = north ? new Vector3(1, 0, 0) : new Vector3(0, 0, 1);
            float yaw = north ? 0f : 270f;                      // drape front (+Y in Blender = -Z in Unity at yaw 0) must face the arena: north arena = -Z (yaw 0), west arena = +X (yaw 90 maps -Z to +X)
            float hang = tallB ? 5.1f : 4.5f;                  // below the ragged top
            float face = 0.75f;                                // pier front plane is ~0.6 m from the bay axis toward the arena
            int pat = lamp ? 1 : (nd % 3 == 0 ? 0 : nd % 3 == 1 ? 2 : 1);
            string colName = cols[ci++ % 3]; var mat = AssetDatabase.LoadAssetAtPath<Material>(Dst + "/Materials/MI_Drape_" + colName + ".mat");
            if (pat == 2 && !lamp && !tallB) { Spawn("Drape_C", rootD, "VF_EA_Drape_C_" + key, t.position + inward * 0.36f + Vector3.up * (hang - 0.05f), yaw, new Vector3(0.82f, 1f, 1f), mat, false, false); nd++; }
            else if (pat == 0 && !lamp) { Spawn("Drape_A", rootD, "VF_EA_Drape_A_" + key, t.position + inward * 0.30f + along * (rnd.Next(2) == 0 ? -1.05f : 1.05f) + Vector3.up * (hang - 0.1f), yaw, new Vector3(0.75f, 1f, 1f), mat, false, false); nd++; }
            else { Spawn("Drape_B", rootD, "VF_EA_Drape_B_" + key, t.position + inward * face + along * 2.0f + Vector3.up * (hang + (tallB ? 0.25f : 0.35f)), yaw, Vector3.one, mat, false, false); nd++; }
        }
        sb.AppendLine("drapes=" + nd);
        return sb.ToString();
    }

    public static string PlaceShrine(float s, float scaleXZ)
    {
        var sb = new StringBuilder(); var rootS = Root("VF_EA_Shrine", null); var rootC = Root("VF_EA_Columns", null);
        Vector2 diag = new Vector2(-0.70711f, 0.70711f); var p = diag * s;
        var g = Spawn("Shrine_Backdrop_A", rootS, "VF_EA_Shrine_A", new Vector3(p.x, 0f, p.y), 135f, new Vector3(scaleXZ, 1f, scaleXZ), null, true);
        var bc = g.AddComponent<BoxCollider>(); bc.center = new Vector3(0, 4.3f, 2.5f); bc.size = new Vector3(11f, 8.6f, 5f);   // keeps the player out of the mass (local space, unscaled mesh coords)
        // two flanking tall columns beside the dais (perpendicular to the corner diagonal)
        Vector2 perp = new Vector2(0.70711f, 0.70711f); float sc = 20.8f;
        foreach (float side in new[] { -1f, 1f })
        {
            var q = diag * sc + perp * side * 4.9f;
            var c = Spawn("Column_Tall_A", rootC, "VF_EA_Column_" + (side < 0 ? "S" : "N"), new Vector3(q.x, 0f, q.y), side < 0 ? 20f : -35f, Vector3.one, null, true);
            var cc = c.AddComponent<CapsuleCollider>(); cc.direction = 1; cc.radius = 0.5f; cc.height = 6.8f; cc.center = new Vector3(0, 3.4f, 0);
        }
        sb.AppendLine("shrine at s=" + s + " pos " + p + ", columns at s=" + sc);
        return sb.ToString();
    }

    public static string RestoreBays()
    {
        int n = 0; foreach (var t in Object.FindObjectsByType<Transform>(FindObjectsInactive.Include).Where(x => x.name.StartsWith("VF_B1_B1_WallTall_"))) { if (!t.gameObject.activeSelf) { t.gameObject.SetActive(true); n++; } }
        foreach (var r in new[] { "VF_EA_East", "VF_EA_Walls", "VF_EA_LampLights", "VF_EA_Drapes", "VF_EA_Shrine", "VF_EA_Columns", "VF_EA_Paving" }) { var g = GameObject.Find(r); if (g != null) Object.DestroyImmediate(g); }
        return "restored " + n + " bays; removed VF_EA roots";
    }

    // ------------------------------------------------------------------ east / south-east counterweight (near sides: nothing above ~2 m)
    public static string East()
    {
        var sb = new StringBuilder(); var root = Root("VF_EA_East", null); var rnd = new System.Random(23);
        var gW = new GameObject("LowWalls").transform; gW.SetParent(root, false);
        var gP = new GameObject("Pylons").transform; gP.SetParent(root, false); var gR = new GameObject("Ruins").transform; gR.SetParent(root, false);
        var gD = new GameObject("Drapes").transform; gD.SetParent(root, false); var gL = new GameObject("Lights").transform; gL.SetParent(root, false);
        var obs = Obstacles(); int nW = 0, nP = 0, nR = 0, nD = 0;
        // 1. low broken bays just inside the east and south parapets (max 1.9 m). Front (outward) faces the parapet, detailed arena side faces the arena.
        var slots = new List<(Vector2 p, float yaw, string tag)>();
        foreach (float z in new[] { -13f, -9f, -5f, -1f, 3f, 7f, 11f }) slots.Add((new Vector2(15.3f + (float)rnd.NextDouble() * 0.6f, z + (float)(rnd.NextDouble() - 0.5) * 1.2f), 270f + (float)(rnd.NextDouble() - 0.5) * 14f, "E" + z));
        foreach (float x in new[] { -9f, -5f, -1f, 3f, 7f, 11f }) slots.Add((new Vector2(x + (float)(rnd.NextDouble() - 0.5) * 1.2f, -15.3f - (float)rnd.NextDouble() * 0.6f), 0f + (float)(rnd.NextDouble() - 0.5) * 14f, "S" + x));
        int ai = 0, slotIdx = 0;
        foreach (var sl in slots)
        {
            if (slotIdx++ % 3 == 2) { sb.AppendLine("gap " + sl.tag); continue; }                                                                      // leave irregular gaps
            var ob = MakeObb(sl.p + new Vector2(Mathf.Sin(sl.yaw * Mathf.Deg2Rad), Mathf.Cos(sl.yaw * Mathf.Deg2Rad)) * 0.4f, sl.yaw, 2.0f, 1.0f);
            if (BlockedObb(obs, ob, 0.25f)) { sb.AppendLine("skip low bay " + sl.tag + " obb c=" + ob.c); continue; }
            string t = (ai++ % 2 == 0) ? "Wall_Low_Broken_A" : "Wall_Low_Broken_B";
            var g = Spawn(t, gW, "VF_EA_LowBay_" + sl.tag, new Vector3(sl.p.x, 0f, sl.p.y), sl.yaw, Vector3.one, null, true);
            var bc = g.AddComponent<BoxCollider>(); bc.center = new Vector3(0f, 0.8f, 0f); bc.size = new Vector3(3.9f, 1.6f, 1.15f); nW++;
            foreach (var r in g.GetComponentsInChildren<Renderer>()) obs.Add(r.bounds);
            if (nW % 2 == 1)
            {
                var ad = new Vector3(Mathf.Sin(sl.yaw * Mathf.Deg2Rad), 0f, Mathf.Cos(sl.yaw * Mathf.Deg2Rad)) * -1f;   // arena side = opposite of outward
                var dm = AssetDatabase.LoadAssetAtPath<Material>(Dst + "/Materials/MI_Drape_" + new[] { "Crimson", "Ochre", "Indigo" }[nW % 3] + ".mat");
                Spawn("Drape_A", gW, "VF_EA_LowDrape_" + sl.tag, new Vector3(sl.p.x, 1.35f, sl.p.y) + ad * 0.42f, sl.yaw + 180f, new Vector3(0.75f, 0.44f, 1f), dm, false, false);
            }
        }
        // 2. lantern pylons (scaled 0.7 -> 2.1 m) near the east/south walls
        foreach (var pp in new[] { new Vector2(16.0f, 9.0f), new Vector2(16.4f, -6.5f), new Vector2(3.0f, -16.0f), new Vector2(8.0f, -16.4f) })
        {
            if (Blocked(obs, pp, 0.9f)) { sb.AppendLine("skip pylon " + pp); continue; }
            var g = Spawn("Lantern_Pylon_A", gP, "VF_EA_Pylon_" + nP, new Vector3(pp.x, 0, pp.y), 90f * nP, Vector3.one * 0.7f, null, true, true, B1Dir);
            var cc = g.AddComponent<CapsuleCollider>(); cc.direction = 1; cc.radius = 0.45f; cc.height = 2.97f; cc.center = new Vector3(0, 1.485f, 0);
            var lo = new GameObject("VF_EA_PylonLight_" + nP); lo.transform.SetParent(gL, false); lo.transform.position = new Vector3(pp.x, 2.72f * 0.7f, pp.y);
            var lt = lo.AddComponent<Light>(); lt.type = LightType.Point; lt.color = new Color(1f, 0.62f, 0.30f); lt.intensity = 2.6f; lt.range = 5.5f; lt.shadows = LightShadows.None;
            nP++; obs.Add(g.GetComponentInChildren<Renderer>().bounds);
        }
        // 3. ruin clusters (scaled 0.62 -> pillar ~2 m) at r 15..19 on the east / south-east
        var picks = new List<Vector2>();
        for (int k = 0; k < 3; k++)
        {
            float bestScore = -1; Vector2 best = Vector2.zero;
            float[] angs = { -8f, -32f, -58f }; float a0 = angs[k] * Mathf.Deg2Rad;
            for (float rr = 14.6f; rr <= 17.4f; rr += 0.4f) for (float da = -14f; da <= 14f; da += 2f)
                {
                    float a = a0 + da * Mathf.Deg2Rad; var c = new Vector2(Mathf.Cos(a) * rr, Mathf.Sin(a) * rr);
                    if (Mathf.Abs(c.x) > 16.4f || Mathf.Abs(c.y) > 16.4f) continue; if (Blocked(obs, c, 2.1f)) continue; if (picks.Any(q => (q - c).magnitude < 5.5f)) continue;
                    float sc = 1f - Mathf.Abs(da) / 20f; if (sc > bestScore) { bestScore = sc; best = c; }
                }
            if (bestScore < 0) { sb.AppendLine("no spot for ruin " + k); continue; }
            picks.Add(best); string t = k == 1 ? "Ruin_Cluster_B" : "Ruin_Cluster_A";
            var g = Spawn(t, gR, "VF_EA_Ruin_" + k, new Vector3(best.x, 0, best.y), 180f + (k - 1) * 22f, Vector3.one * 0.62f, null, true, true, B1Dir);
            var cap = g.AddComponent<CapsuleCollider>(); cap.direction = 1;
            if (t.EndsWith("_A")) { cap.center = new Vector3(0.92f, 1.60f, -0.95f); cap.radius = 0.60f; cap.height = 3.19f; var b1 = g.AddComponent<BoxCollider>(); b1.center = new Vector3(-1.25f, 0.5f, -0.75f); b1.size = new Vector3(2f, 1f, 1f); }
            else { cap.center = new Vector3(1.10f, 1.43f, -0.71f); cap.radius = 0.56f; cap.height = 2.87f; var b1 = g.AddComponent<BoxCollider>(); b1.center = new Vector3(-0.5f, 0.6f, -0.0f); b1.size = new Vector3(2f, 1.2f, 1.5f); }
            nR++; foreach (var r in g.GetComponentsInChildren<Renderer>()) obs.Add(r.bounds);
            sb.AppendLine("ruin " + t + " at " + best + " r=" + best.magnitude.ToString("F1"));
        }
        // 4. drapes hung from the parapet top down its inner face (not rising above 3 m), arena-facing
        var cols = new[] { "Crimson", "Ochre", "Indigo" }; int ci = 0;
        var dpos = new List<(Vector3 p, float yaw)>();
        foreach (float z in new float[] { }) dpos.Add((new Vector3(19.30f, 2.95f, z), 90f));
        foreach (float x in new float[] { }) dpos.Add((new Vector3(x, 2.95f, -19.30f), 180f));
        foreach (var d in dpos)
        {
            if (Blocked(obs.Where(b => b.max.y > 2.5f && false).ToList(), new Vector2(d.p.x, d.p.z), 0.5f)) continue;
            var mat = AssetDatabase.LoadAssetAtPath<Material>(Dst + "/Materials/MI_Drape_" + cols[ci++ % 3] + ".mat");
            Spawn("Drape_B", gD, "VF_EA_EDrape_" + nD++, d.p, d.yaw, new Vector3(1f, 0.56f, 1f), mat, false, false);
        }
        sb.AppendLine("lowBays=" + nW + " pylons=" + nP + " ruins=" + nR + " drapes=" + nD); return sb.ToString();
    }

    public static string SaveScene() { var sc = EditorSceneManager.GetActiveScene(); EditorSceneManager.MarkSceneDirty(sc); EditorSceneManager.SaveScene(sc); AssetDatabase.SaveAssets(); return "saved " + sc.path; }
}
