// Visual Foundation Batch 1, real models: copy (never move) the Environment Artist's FBX + textures into Assets/ArtTest/VisualFoundation/Batch1/,
// import like the kit, build URP Lit material instances (Base/Normal/Mask/Emission assigned by name), and place per Batch1_Placement.json.
// Art-test scene only; every instance sits under VF_Batch1 (toggle with VF4Builder.SetBatch).
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class VF5Builder
{
    public static bool RemoveArchBays = true;
    public static float Pylon4EastOffset = 1.0f;
    public static bool ApproachFillLights = true;
    const string Src = "Art/Blender/Revisions/batch1/handoff";
    const string Dst = "Assets/ArtTest/VisualFoundation/Batch1";
    static readonly string[] Parts = { "Wall_Tall_A", "Wall_Tall_B", "Lantern_Pylon_A", "Ruin_Cluster_A", "Ruin_Cluster_B", "Backdrop_Mass_A", "Backdrop_Mass_B", "Backdrop_Mass_C" };
    [System.Serializable] class Row { public string instance, group, mesh, part, role; public float unity_x, unity_y, unity_z, yaw_front_to_plusZ, yaw_front_to_minusZ, scale; }
    [System.Serializable] class Table { public Row[] instances; }

    static string Sha(string p) { using (var s = SHA256.Create()) using (var f = File.OpenRead(p)) return string.Concat(s.ComputeHash(f).Select(b => b.ToString("x2"))); }

    public static string CopyAndImport()
    {
        var sb = new StringBuilder(); Directory.CreateDirectory(Dst + "/Models"); Directory.CreateDirectory(Dst + "/Textures"); Directory.CreateDirectory(Dst + "/Materials");
        var sums = File.ReadAllLines(Src + "/SHA256SUMS.txt").Select(l => l.Split(new[] { "  ", " *" }, System.StringSplitOptions.RemoveEmptyEntries)).Where(a => a.Length == 2).ToDictionary(a => a[1].Trim(), a => a[0]);
        int copied = 0, bad = 0;
        foreach (var kind in new[] { "Models", "Textures" })
            foreach (var f in Directory.GetFiles(Src + "/" + kind))
            {
                string name = Path.GetFileName(f), dst = Dst + "/" + kind + "/" + name;
                if (!File.Exists(dst)) { File.Copy(f, dst); copied++; }
                string key = kind + "/" + name; string have = Sha(dst);
                if (sums.TryGetValue(key, out var exp)) { if (exp != have) { bad++; sb.AppendLine("SHA MISMATCH " + key); } } else sb.AppendLine("no checksum line for " + key);
            }
        sb.AppendLine("copied " + copied + " new files; sha mismatches " + bad);
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        return sb.ToString();
    }

    public static string ConfigureTextures()
    {
        var sb = new StringBuilder();
        foreach (var f in Directory.GetFiles(Dst + "/Textures", "*.png"))
        {
            string p = f.Replace('\\', '/'); var ti = (TextureImporter)AssetImporter.GetAtPath(p); if (ti == null) continue; string n = Path.GetFileNameWithoutExtension(p);
            bool normal = n.EndsWith("_Normal"), mask = n.EndsWith("_Mask"), emis = n.EndsWith("_Emission");
            ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default; ti.sRGBTexture = !(normal || mask); ti.alphaIsTransparency = false; ti.mipmapEnabled = true;
            ti.filterMode = FilterMode.Bilinear; ti.anisoLevel = 4; ti.maxTextureSize = 2048; ti.textureCompression = TextureImporterCompression.Compressed; ti.wrapMode = TextureWrapMode.Repeat; // same as the kit textures
            ti.SaveAndReimport(); var t = AssetDatabase.LoadAssetAtPath<Texture2D>(p); sb.AppendLine(n + ": " + t.width + "x" + t.height + " " + t.format + " sRGB=" + ti.sRGBTexture + (normal ? " normalmap" : ""));
        }
        return sb.ToString();
    }

    static Texture2D Tex(string part, string suffix) => AssetDatabase.LoadAssetAtPath<Texture2D>(Dst + "/Textures/ENV_Temple_" + part + "_" + suffix + ".png");

    // Same setup as ArtTestCourtyardBuilder.ConfigureMaterial (kit): Base, Normal, the packed Mask in both metallic/occlusion slots, Emission on the pylon only.
    public static string BuildMaterials()
    {
        var sb = new StringBuilder(); var shader = Shader.Find("Universal Render Pipeline/Lit");
        foreach (var part in Parts)
        {
            string fbx = Dst + "/Models/ENV_Temple_" + part + ".fbx"; var model = AssetDatabase.LoadAssetAtPath<GameObject>(fbx); var imp = (ModelImporter)AssetImporter.GetAtPath(fbx);
            string matName = "MI_Temple_" + part; string mp = Dst + "/Materials/" + matName + ".mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(mp);
            if (m == null) { m = new Material(shader) { name = matName }; AssetDatabase.CreateAsset(m, mp); }
            m.shader = shader; m.SetTexture("_BaseMap", Tex(part, "BaseColor")); m.SetColor("_BaseColor", Color.white);
            var n = Tex(part, "Normal"); m.SetTexture("_BumpMap", n); m.SetFloat("_BumpScale", 1f); if (n != null) m.EnableKeyword("_NORMALMAP");
            var mask = Tex(part, "Mask"); m.SetTexture("_MetallicGlossMap", mask); m.SetTexture("_OcclusionMap", mask); m.SetFloat("_Metallic", 1f); m.SetFloat("_Smoothness", 1f); m.SetFloat("_SmoothnessTextureChannel", 0f); m.SetFloat("_OcclusionStrength", 1f); m.SetFloat("_WorkflowMode", 1f);
            if (mask != null) { m.EnableKeyword("_METALLICSPECGLOSSMAP"); m.EnableKeyword("_OCCLUSIONMAP"); }
            var em = Tex(part, "Emission");
            if (em != null) { m.SetTexture("_EmissionMap", em); m.SetColor("_EmissionColor", Color.white * 1.5f); m.EnableKeyword("_EMISSION"); m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.BakedEmissive; }
            else { m.SetColor("_EmissionColor", Color.black); m.DisableKeyword("_EMISSION"); }
            m.SetFloat("_Surface", 0f); m.SetFloat("_Cull", 2f); m.enableInstancing = true; EditorUtility.SetDirty(m);
            // remap every material slot the FBX carries to this instance (FBX does not link Mask/Emission, so everything is assigned by name here)
            var srcMats = model.GetComponentsInChildren<Renderer>().SelectMany(r => r.sharedMaterials).Where(x => x != null).Select(x => x.name).Distinct().ToList();
            foreach (var sn in srcMats) imp.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), sn), m);
            imp.SaveAndReimport();
            sb.AppendLine(part + ": material " + matName + " base=" + (Tex(part, "BaseColor") != null) + " normal=" + (n != null) + " mask=" + (mask != null) + " emission=" + (em != null) + " | FBX material slots remapped: " + string.Join(",", srcMats));
        }
        AssetDatabase.SaveAssets(); return sb.ToString();
    }

    public static string Inspect()
    {
        var sb = new StringBuilder();
        foreach (var part in Parts.Concat(new[] { "Wall_B", "Stairs_A" }))
        {
            string fbx = part.StartsWith("Wall_B") || part.StartsWith("Stairs") ? "Assets/ArtTest/Environment/Models/ENV_Temple_" + part + ".fbx" : Dst + "/Models/ENV_Temple_" + part + ".fbx";
            var go = AssetDatabase.LoadAssetAtPath<GameObject>(fbx); var imp = (ModelImporter)AssetImporter.GetAtPath(fbx);
            var rs = go.GetComponentsInChildren<MeshRenderer>(); Bounds b = default; bool f = false; int tris = 0;
            foreach (var r in rs) { var mf = r.GetComponent<MeshFilter>(); tris += mf.sharedMesh.triangles.Length / 3; var lb = mf.sharedMesh.bounds; if (!f) { b = lb; f = true; } else b.Encapsulate(lb); }
            sb.AppendLine(part + ": root '" + go.name + "' children=" + go.transform.childCount + " renderers=" + rs.Length + " tris=" + tris + " meshBounds(min)=" + b.min.ToString("F2") + " (max)=" + b.max.ToString("F2") + " materials=" + string.Join("|", rs.SelectMany(r => r.sharedMaterials).Select(m => m == null ? "null" : m.name + ":" + m.shader.name)) + " scale(useFileScale/globalScale)=" + imp.useFileScale + "/" + imp.globalScale + " rootScale=" + go.transform.localScale + " rootRot=" + go.transform.localEulerAngles);
        }
        return sb.ToString();
    }

    // ---------- placement ----------
    static GameObject Prefab(string part) => AssetDatabase.LoadAssetAtPath<GameObject>(Dst + "/Models/ENV_Temple_" + part + ".fbx");

    // Voxel-cluster primitive colliders for a ruin (tall pillar -> capsule, low mass -> merged boxes). Local space of the FBX instance.
    static string AddRuinColliders(GameObject inst, Mesh mesh, float vox = 0.5f)
    {
        var v = mesh.vertices; var t = mesh.triangles; var cells = new Dictionary<(int, int), (int n, float maxY)>();
        void Add(Vector3 p) { var k = (Mathf.FloorToInt(p.x / vox), Mathf.FloorToInt(p.z / vox)); cells.TryGetValue(k, out var c); cells[k] = (c.n + 1, Mathf.Max(c.maxY, p.y)); }
        for (int i = 0; i < t.Length; i += 3)
        {
            Vector3 a = v[t[i]], b = v[t[i + 1]], c = v[t[i + 2]]; float ar = Vector3.Cross(b - a, c - a).magnitude * 0.5f; int n = Mathf.Clamp(Mathf.CeilToInt(ar / 0.01f), 1, 400); int g = Mathf.CeilToInt(Mathf.Sqrt(n));
            for (int x = 0; x <= g; x++) for (int y = 0; y <= g - x; y++) { float u = x / (float)g, w = y / (float)g; Add(a * (1 - u - w) + b * u + c * w); }
        }
        // tall cells (pillar)
        var tall = cells.Where(kv => kv.Value.maxY > 1.8f && kv.Value.n >= 4).ToList(); var sb = new StringBuilder();
        var tallKeys = new HashSet<(int, int)>();
        if (tall.Count > 0)
        {
            float cx = tall.Average(kv => (kv.Key.Item1 + 0.5f) * vox), cz = tall.Average(kv => (kv.Key.Item2 + 0.5f) * vox); var hv = v.Where(q => q.y > 2.0f).ToList(); if (hv.Count > 8) { cx = hv.Average(q => q.x); cz = hv.Average(q => q.z); } float rad = (hv.Count > 8 ? hv.Max(q => Vector2.Distance(new Vector2(q.x, q.z), new Vector2(cx, cz))) : Mathf.Sqrt(tall.Count * vox * vox / Mathf.PI)) + 0.05f; /* measured from the vertices above 2 m */ float h = tall.Max(kv => kv.Value.maxY);
            foreach (var kv in tall) tallKeys.Add(kv.Key);
            var cap = inst.AddComponent<CapsuleCollider>(); cap.direction = 1; cap.radius = rad; cap.height = h; cap.center = new Vector3(cx, h * 0.5f, cz); sb.Append("tallCells=" + tall.Count + " pillar capsule r=" + cap.radius.ToString("F2") + " h=" + h.ToString("F2") + " at (" + cx.ToString("F2") + "," + cz.ToString("F2") + "); ");
        }
        // low mass: occupied cells (n>=2), merge runs along x
        var low = cells.Where(kv => !tallKeys.Contains(kv.Key) && kv.Value.n >= 2 && kv.Value.maxY > 0.12f).OrderBy(kv => kv.Key.Item2).ThenBy(kv => kv.Key.Item1).ToList(); int boxes = 0;
        var byRow = low.GroupBy(kv => kv.Key.Item2);
        foreach (var row in byRow)
        {
            var cs = row.OrderBy(kv => kv.Key.Item1).ToList(); int i = 0;
            while (i < cs.Count)
            {
                int j = i; float my = cs[i].Value.maxY; while (j + 1 < cs.Count && cs[j + 1].Key.Item1 == cs[j].Key.Item1 + 1) { j++; my = Mathf.Max(my, cs[j].Value.maxY); }
                float x0 = cs[i].Key.Item1 * vox, x1 = (cs[j].Key.Item1 + 1) * vox, z0 = row.Key * vox; var bc = inst.AddComponent<BoxCollider>(); bc.center = new Vector3((x0 + x1) * 0.5f, my * 0.5f, z0 + vox * 0.5f); bc.size = new Vector3(x1 - x0, my, vox); boxes++; i = j + 1;
            }
        }
        if (boxes > 24 && vox < 0.9f) { foreach (var c in inst.GetComponents<Collider>()) Object.DestroyImmediate(c); return AddRuinColliders(inst, mesh, vox * 1.5f); }
        sb.Append("boxes=" + boxes + " (voxel " + vox.ToString("F2") + ")"); return sb.ToString();
    }


    // Hand-placed ruin colliders (local space, from a 0.5 m top-down height map of the FBX; low rubble under about 0.4 m is left walkable).
    static string HandColliders(GameObject g, string mesh)
    {
        bool a = mesh.EndsWith("Cluster_A");
        var cap = g.AddComponent<CapsuleCollider>(); cap.direction = 1;
        if (a) { cap.center = new Vector3(0.92f, 1.60f, -0.95f); cap.radius = 0.60f; cap.height = 3.19f; AddBox(g, -2.5f, 0.0f, -1.5f, 2.0f, 1.0f); AddBox(g, 0.0f, 1.0f, 0.5f, 3.0f, 0.8f); return "pillar capsule + 2 boxes (hand-placed, cluster A)"; }
        cap.center = new Vector3(1.10f, 1.43f, -0.71f); cap.radius = 0.56f; cap.height = 2.87f; AddBox(g, -1.5f, 0.5f, -1.5f, 1.5f, 1.2f); return "pillar capsule + 1 box (hand-placed, cluster B)";
    }
    static void AddBox(GameObject g, float x0, float x1, float z0, float z1, float h) { var b = g.AddComponent<BoxCollider>(); b.center = new Vector3((x0 + x1) * 0.5f, h * 0.5f, (z0 + z1) * 0.5f); b.size = new Vector3(x1 - x0, h, z1 - z0); }

    // Build / rebuild the real batch under VF_Batch1. gapNorth/gapWest = extra metres beyond the 5 m start for each backdrop mass (A, B north; C west). pylonScale 1.0 or 1.25.
    public static string BuildReal(float extraA = 0f, float extraB = 0f, float extraC = 0f, float pylonScale = 1f, bool save = true)
    {
        var sc = EditorSceneManager.GetActiveScene(); if (sc.path != "Assets/Scenes/ArtTest_VisualFoundation.unity") return "WRONG SCENE " + sc.path;
        VF4Builder.RemoveProxies(); var old = VF4Builder.FindIncl("VF_Batch1"); if (old != null) Object.DestroyImmediate(old);
        var tbl = JsonUtility.FromJson<Table>(File.ReadAllText(Src + "/Batch1_Placement.json")); var sb = new StringBuilder("table rows " + tbl.instances.Length + "\n");
        var root = new GameObject("VF_Batch1").transform;
        Transform Grp(string n) { var g = new GameObject("VF_Batch1_" + n); g.transform.SetParent(root, false); return g.transform; }
        var gW = Grp("Walls"); var gP = Grp("Pylons"); var gR = Grp("Ruins"); var gB = Grp("Backdrop"); var gL = Grp("PylonLights");
        int w = 0, p = 0, r = 0, b = 0;
        foreach (var row in tbl.instances)
        {
            if (row.group.Contains("directive")) continue;
            if (RemoveArchBays && (row.instance == "B1_WallTall_B_N-06" || row.instance == "B1_WallTall_B_N+14")) continue; // Director: about 8 m clear at the arch; set RemoveArchBays=false to restore the table (placement table files untouched) // the 28-55 m placement is never on screen (EA measurement); not instantiated
            var pre = Prefab(row.mesh.Replace("ENV_Temple_", "")); if (pre == null) { sb.AppendLine("missing prefab for " + row.mesh); continue; }
            var pos = new Vector3(row.unity_x, row.unity_y, row.unity_z); var yaw = Quaternion.Euler(0, row.yaw_front_to_minusZ, 0);
            if (row.instance == "B1_Pylon_4") pos += new Vector3(Pylon4EastOffset, 0f, 0f); // VF scene only: avoids the pinch with the kit brazier at (9.4,17.6); the Environment Artist table is not edited
            Transform parent = row.group == "BATCH1_Walls" ? gW : row.group == "BATCH1_Pylons" ? gP : row.group == "BATCH1_Ruins" ? gR : gB;
            if (parent == gB) { Vector3 outward = row.mesh.EndsWith("_C") ? Vector3.left : Vector3.forward; float extra = row.mesh.EndsWith("_A") ? extraA : row.mesh.EndsWith("_B") ? extraB : extraC; pos += outward * extra; }
            var g = (GameObject)PrefabUtility.InstantiatePrefab(pre, sc); g.name = "VF_B1_" + row.instance; g.transform.SetParent(parent, false); g.transform.position = pos; g.transform.rotation = yaw;
            float sc2 = row.scale * (parent == gP ? pylonScale : 1f); g.transform.localScale = Vector3.one * sc2;
            var mr = g.GetComponentInChildren<MeshRenderer>(); mr.receiveGI = ReceiveGI.LightProbes;
            mr.shadowCastingMode = (parent == gB || (parent == gW && row.unity_z > 20f)) ? ShadowCastingMode.Off : ShadowCastingMode.On; /* Director plan: north bays receive only; west bays, pylons, ruins cast */ mr.receiveShadows = parent != gB;
            var flags = StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccluderStatic | StaticEditorFlags.OccludeeStatic; GameObjectUtility.SetStaticEditorFlags(g, flags);
            if (parent == gW) w++; else if (parent == gB) b++;
            else if (parent == gP)
            {
                var cc = g.AddComponent<CapsuleCollider>(); cc.direction = 1; cc.radius = 0.45f; cc.height = 2.97f; cc.center = new Vector3(0, 1.485f, 0); p++;   // local space: scales with the instance
                var lo = new GameObject("VF_B1_PylonLight_" + row.instance); lo.transform.SetParent(gL, false); lo.transform.position = pos + Vector3.up * 2.72f * sc2;
                var lt = lo.AddComponent<Light>(); lt.type = LightType.Point; lt.color = new Color(1f, 0.62f, 0.30f); lt.intensity = 3f; lt.range = 6f; lt.shadows = LightShadows.None; lt.lightmapBakeType = LightmapBakeType.Realtime;
            }
            else if (parent == gR) { sb.AppendLine(row.instance + " (" + row.mesh + "): " + HandColliders(g, row.mesh)); r++; }
        }
        if (ApproachFillLights)
        {   // restores what the two switched-off approach-brazier lights (L11_BrazierLights) did at the dais: same warm colour, intensity 3.0, range 5.5, no shadows
            var gF = Grp("ApproachFillLights");
            foreach (var q in new[] { new Vector3(-6.9f, 1.7f, 10.8f), new Vector3(-10.8f, 1.7f, 6.9f) })
            { var lo = new GameObject("VF_B1_ApproachFill_" + q.x.ToString("F1")); lo.transform.SetParent(gF, false); lo.transform.position = q; var lt = lo.AddComponent<Light>(); lt.type = LightType.Point; lt.color = new Color(1f, 0.62f, 0.30f); lt.intensity = 3f; lt.range = 5.5f; lt.shadows = LightShadows.None; }
        }
        sb.AppendLine("placed: bays " + w + ", pylons " + p + " (scale " + pylonScale + "), ruins " + r + ", backdrop masses " + b + " (extra beyond 5 m: A +" + extraA + ", B +" + extraB + ", C +" + extraC + ")");
        VF4Builder.SetBatch(true);
        if (save) { EditorSceneManager.MarkSceneDirty(sc); EditorSceneManager.SaveScene(sc); AssetDatabase.SaveAssets(); }
        return sb.ToString();
    }
}
