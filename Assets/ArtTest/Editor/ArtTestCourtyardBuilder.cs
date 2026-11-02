// Art-test only. Builds materials + the courtyard test scene from Art placement data.
// Does not touch PrototypeArena, SampleScene or CharacterRigTest.
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class ArtTestCourtyardBuilder
{
    const string Root = "Assets/ArtTest/Environment";
    const string ModelDir = Root + "/Models";
    const string TexDir = Root + "/Textures";
    const string MatDir = Root + "/Materials";
    public const string ScenePath = "Assets/Scenes/ArtTest_TempleCourtyard.unity";
    const string SourceScene = "Assets/Scenes/PrototypeArena.unity";
    const string PlacementPath = Root + "/TempleCourtyard_Placement.json";

    [Serializable] class Inst { public string instance, group, part; public float unity_x, unity_y, unity_z, yaw_front_to_plusZ, yaw_front_to_minusZ, scale; }
    [Serializable] class Table { public Inst[] instances; }

    // Verified in Unity: FBX local front (Blender +Y) lands on Unity -Z at yaw 0, so the "minusZ" yaw column is used.
    static float Yaw(Inst i) => i.yaw_front_to_minusZ;

    static readonly string[] EmissivePrefixes = { "ENV_Temple_Altar_A", "ENV_Temple_Brazier_A" };

    public static string BuildMaterials()
    {
        Directory.CreateDirectory(MatDir);
        var shader = Shader.Find("Universal Render Pipeline/Lit");
        int count = 0;
        var log = new System.Text.StringBuilder();
        foreach (var fbx in Directory.GetFiles(ModelDir, "*.fbx"))
        {
            string fbxPath = fbx.Replace('\\', '/');
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
            var importer = (ModelImporter)AssetImporter.GetAtPath(fbxPath);
            foreach (var r in model.GetComponentsInChildren<Renderer>())
            {
                string part = r.name;
                string matName = "MI_Temple_" + part.Replace("ENV_Temple_", "");
                string matPath = MatDir + "/" + matName + ".mat";
                var mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
                if (mat == null) { mat = new Material(shader) { name = matName }; AssetDatabase.CreateAsset(mat, matPath); }
                mat.shader = shader;
                ConfigureMaterial(mat, part);
                EditorUtility.SetDirty(mat);
                importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), matName), mat);
                count++;
            }
            importer.SaveAndReimport();
        }
        AssetDatabase.SaveAssets();
        log.Append("materials configured: " + count);
        return log.ToString();
    }

    static Texture2D Tex(string part, string suffix) => AssetDatabase.LoadAssetAtPath<Texture2D>(TexDir + "/" + part + "_" + suffix + ".png");

    static void ConfigureMaterial(Material m, string part)
    {
        m.SetTexture("_BaseMap", Tex(part, "BaseColor"));
        m.SetColor("_BaseColor", Color.white);
        var n = Tex(part, "Normal");
        m.SetTexture("_BumpMap", n); m.SetFloat("_BumpScale", 1f);
        if (n != null) m.EnableKeyword("_NORMALMAP"); else m.DisableKeyword("_NORMALMAP");
        var mask = Tex(part, "Mask");
        // Packed mask: R metallic, G occlusion, A smoothness. Same texture in both slots.
        m.SetTexture("_MetallicGlossMap", mask);
        m.SetTexture("_OcclusionMap", mask);
        m.SetFloat("_Metallic", 1f);
        m.SetFloat("_Smoothness", 1f);
        m.SetFloat("_SmoothnessTextureChannel", 0f); // 0 = Metallic alpha
        m.SetFloat("_OcclusionStrength", 1f);
        m.SetFloat("_WorkflowMode", 1f);
        if (mask != null) { m.EnableKeyword("_METALLICSPECGLOSSMAP"); m.EnableKeyword("_OCCLUSIONMAP"); }
        m.SetFloat("_Surface", 0f); m.SetFloat("_Cull", 2f);
        m.enableInstancing = true;

        var em = Tex(part, "Emission");
        bool emissive = Array.Exists(EmissivePrefixes, p => part.StartsWith(p));
        if (emissive && em != null)
        {
            m.SetTexture("_EmissionMap", em);
            m.SetColor("_EmissionColor", Color.white * 1.5f);
            m.EnableKeyword("_EMISSION");
            m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.BakedEmissive;
        }
        else
        {
            m.SetColor("_EmissionColor", Color.black);
            m.DisableKeyword("_EMISSION");
        }
    }

    public static string BuildScene()
    {
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) == null)
            AssetDatabase.CopyAsset(SourceScene, ScenePath); // file copy only; the source scene is not opened for writing
        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        if (scene.path != ScenePath) return "FAILED: wrong scene opened " + scene.path;

        // Remove the greybox arena shell (art-test copy only).
        foreach (var go in scene.GetRootGameObjects())
            if (go.name == "Arena" || go.name == "Environment_Courtyard" || go.name == "CollisionProxies" || go.name == "TelegraphDemo")
                UnityEngine.Object.DestroyImmediate(go);

        var table = JsonUtility.FromJson<Table>(File.ReadAllText(PlacementPath));
        var env = new GameObject("Environment_Courtyard");
        var groups = new Dictionary<string, Transform>();
        var prox = new GameObject("CollisionProxies");
        int placed = 0, skippedArch = 0;
        bool archDone = false;
        var report = new System.Text.StringBuilder();

        foreach (var i in table.instances)
        {
            string fbxName = i.part;
            if (i.part.StartsWith("ENV_Temple_Arch_A_")) // 3 parts share one FBX/origin
            {
                if (archDone) { skippedArch++; continue; }
                archDone = true; fbxName = "ENV_Temple_Arch_A";
            }
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(ModelDir + "/" + fbxName + ".fbx");
            if (model == null) { report.AppendLine("MISSING model " + fbxName); continue; }
            if (!groups.TryGetValue(i.group, out var gt))
            {
                gt = new GameObject(i.group).transform; gt.SetParent(env.transform, false); groups[i.group] = gt;
            }
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(model, scene);
            inst.name = i.instance;
            inst.transform.SetParent(gt, false);
            inst.transform.position = new Vector3(i.unity_x, i.unity_y, i.unity_z);
            inst.transform.rotation = Quaternion.Euler(0f, Yaw(i), 0f);
            inst.transform.localScale = Vector3.one * (i.scale <= 0f ? 1f : i.scale);
            GameObjectUtility.SetStaticEditorFlags(inst, StaticEditorFlags.BatchingStatic | StaticEditorFlags.ContributeGI | StaticEditorFlags.OccluderStatic | StaticEditorFlags.OccludeeStatic | StaticEditorFlags.ReflectionProbeStatic);
            AddProxy(i, fbxName, inst, prox.transform);
            placed++;
        }

        // Single ground slab (walking surface y = 0) instead of 400 floor colliders.
        var ground = new GameObject("Proxy_Ground");
        ground.transform.SetParent(prox.transform, false);
        var gb = ground.AddComponent<BoxCollider>();
        gb.center = new Vector3(0, -0.5f, 0); gb.size = new Vector3(42f, 1f, 42f);

        // Reposition spawns for the new room (keeps combat in the cleared zone).
        MarkDirtyAndSave(scene);
        report.Append("placed=" + placed + " archPartsMerged=" + skippedArch);
        return report.ToString();
    }

    // ---- Visual-only telegraph demo (Art Bible 4.3, Q18). Gameplay telegraph scripts are NOT touched. ----
    public static string AddTelegraphDemo()
    {
        var scene = SceneManager.GetActiveScene();
        if (scene.path != ScenePath) return "FAILED: active scene is " + scene.path;
        foreach (var go in scene.GetRootGameObjects()) if (go.name == "TelegraphDemo") UnityEngine.Object.DestroyImmediate(go);
        var root = new GameObject("TelegraphDemo");
        Directory.CreateDirectory(Root + "/Telegraph");
        var fill = MakeUnlit("MI_TelegraphDemo_Fill", new Color(0x27 / 255f, 0xDC / 255f, 0xD1 / 255f, 0.25f));
        var edge = MakeUnlit("MI_TelegraphDemo_Edge", new Color(0x9B / 255f, 0xFF / 255f, 0xF6 / 255f, 0.95f));
        // (position, yaw, revealed fraction): full danger area, half-revealed windup, and one on the near-field floor.
        Spawn(root.transform, "Demo_Full", new Vector3(5f, 0, 3f), 200f, 1.0f, fill, edge);
        Spawn(root.transform, "Demo_Half", new Vector3(-5f, 0, 2f), 160f, 0.5f, fill, edge);
        Spawn(root.transform, "Demo_Full_FarFloor", new Vector3(-7f, 0, -7f), 45f, 1.0f, fill, edge);
        Spawn(root.transform, "Demo_Full_Mid", new Vector3(7f, 0, -6f), 300f, 1.0f, fill, edge);
        AssetDatabase.SaveAssets();
        MarkDirtyAndSave(scene);
        return "telegraph demo added";
    }

    static Material MakeUnlit(string name, Color c)
    {
        string path = Root + "/Telegraph/" + name + ".mat";
        var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null) { m = new Material(Shader.Find("Universal Render Pipeline/Unlit")); AssetDatabase.CreateAsset(m, path); }
        m.SetFloat("_Surface", 1f); m.SetFloat("_Blend", 0f);
        m.SetOverrideTag("RenderType", "Transparent");
        m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        m.SetInt("_ZWrite", 0); m.SetFloat("_Cull", 0f);
        m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        m.renderQueue = 3000;
        m.SetColor("_BaseColor", c);
        EditorUtility.SetDirty(m);
        return m;
    }

    static void Spawn(Transform parent, string name, Vector3 pos, float yaw, float reveal, Material fill, Material edge)
    {
        var g = new GameObject(name); g.transform.SetParent(parent, false);
        g.transform.position = pos + Vector3.up * 0.03f; g.transform.rotation = Quaternion.Euler(0, yaw, 0);
        const float R = 4f, half = 45f;
        var f = new GameObject("Fill"); f.transform.SetParent(g.transform, false);
        f.AddComponent<MeshFilter>().sharedMesh = Sector(R * reveal, half, 0f);
        f.AddComponent<MeshRenderer>().sharedMaterial = fill;
        var e = new GameObject("Edge"); e.transform.SetParent(g.transform, false); e.transform.localPosition = Vector3.up * 0.01f;
        e.AddComponent<MeshFilter>().sharedMesh = Outline(R, half, 0.09f);
        e.AddComponent<MeshRenderer>().sharedMaterial = edge;
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) { r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false; }
    }

    static Mesh Sector(float r, float halfDeg, float _)
    {
        const int N = 28; var v = new List<Vector3> { Vector3.zero }; var t = new List<int>();
        for (int i = 0; i <= N; i++) { float a = Mathf.Deg2Rad * Mathf.Lerp(-halfDeg, halfDeg, i / (float)N); v.Add(new Vector3(Mathf.Sin(a) * r, 0, Mathf.Cos(a) * r)); }
        for (int i = 1; i <= N; i++) { t.Add(0); t.Add(i); t.Add(i + 1); }
        var m = new Mesh { name = "SectorFill" }; m.SetVertices(v); m.SetTriangles(t, 0); m.RecalculateNormals(); return m;
    }

    static Mesh Outline(float r, float halfDeg, float w)
    {
        const int N = 28; var v = new List<Vector3>(); var t = new List<int>();
        void Strip(Vector3 a, Vector3 b)
        {
            Vector3 d = (b - a).normalized; Vector3 n = Vector3.Cross(Vector3.up, d) * (w * 0.5f);
            int s = v.Count; v.Add(a - n); v.Add(a + n); v.Add(b - n); v.Add(b + n);
            t.AddRange(new[] { s, s + 2, s + 1, s + 1, s + 2, s + 3 });
        }
        Vector3 P(float deg, float rad) { float a = Mathf.Deg2Rad * deg; return new Vector3(Mathf.Sin(a) * rad, 0, Mathf.Cos(a) * rad); }
        for (int i = 0; i < N; i++) Strip(P(Mathf.Lerp(-halfDeg, halfDeg, i / (float)N), r), P(Mathf.Lerp(-halfDeg, halfDeg, (i + 1) / (float)N), r));
        Strip(Vector3.zero, P(-halfDeg, r)); Strip(Vector3.zero, P(halfDeg, r));
        var m = new Mesh { name = "SectorEdge" }; m.SetVertices(v); m.SetTriangles(t, 0); m.RecalculateNormals(); return m;
    }

    static void MarkDirtyAndSave(Scene s)
    {
        EditorSceneManager.MarkSceneDirty(s);
        EditorSceneManager.SaveScene(s, ScenePath);
    }

    static Bounds LocalBounds(GameObject inst)
    {
        // Bounds of the instance's renderers in world space.
        var rs = inst.GetComponentsInChildren<Renderer>();
        Bounds b = rs[0].bounds;
        foreach (var r in rs) b.Encapsulate(r.bounds);
        return b;
    }

    static void AddProxy(Inst i, string fbxName, GameObject inst, Transform parent)
    {
        string k = fbxName.Replace("ENV_Temple_", "");
        if (k.StartsWith("Floor") || k.StartsWith("Banner") || k.StartsWith("Rubble")) return; // ground slab / no collision
        var p = new GameObject("Proxy_" + i.instance);
        p.transform.SetParent(parent, false);
        p.transform.position = inst.transform.position;
        p.transform.rotation = inst.transform.rotation;
        var wb = LocalBounds(inst);
        float height = wb.size.y;
        if (k.StartsWith("Wall"))
        {
            var b = p.AddComponent<BoxCollider>(); b.center = new Vector3(0, 1.5f, 0); b.size = new Vector3(4f, 3f, 1f);
        }
        else if (k.StartsWith("Platform"))
        {
            var b = p.AddComponent<BoxCollider>(); b.center = new Vector3(0, 0.4f, 0); b.size = new Vector3(4f, 0.8f, 6f);
        }
        else if (k.StartsWith("Stairs"))
        {
            // 4 steps, low end local +Z, high end local -Z (verified axis).
            for (int s = 0; s < 4; s++)
            {
                float h = 0.2f * (s + 1);
                var step = new GameObject("Step" + s); step.transform.SetParent(p.transform, false);
                var b = step.AddComponent<BoxCollider>();
                b.center = new Vector3(0, h * 0.5f, 0.75f - 0.5f * s); b.size = new Vector3(4f, h, 0.5f);
            }
        }
        else if (k.StartsWith("Pillar"))
        {
            var c = p.AddComponent<CapsuleCollider>(); c.radius = 0.85f; c.height = height; c.center = new Vector3(0, height * 0.5f, 0);
        }
        else if (k.StartsWith("Arch"))
        {
            // piers only; the span is >4.7 m up. Pier bounds measured from the FBX (x = +/-(2.1..4.15), z = +/-1.15).
            foreach (var sx in new[] { -1f, 1f })
            {
                var pier = new GameObject(sx < 0 ? "PierR" : "PierL"); pier.transform.SetParent(p.transform, false);
                var b = pier.AddComponent<BoxCollider>(); b.center = new Vector3(sx * 3.12f, 2.35f, 0); b.size = new Vector3(2.05f, 4.7f, 2.3f);
            }
        }
        else if (k.StartsWith("Brazier"))
        {
            var c = p.AddComponent<CapsuleCollider>(); c.radius = 0.5f; c.height = height; c.center = new Vector3(0, height * 0.5f, 0);
        }
        else if (k.StartsWith("Altar"))
        {
            var b = p.AddComponent<BoxCollider>(); b.center = new Vector3(0, 1.0f, 0); b.size = new Vector3(3.2f, 2.0f, 2.4f);
        }
        else if (k.StartsWith("ColumnDrum"))
        {
            var c = p.AddComponent<CapsuleCollider>(); c.radius = 0.8f; c.height = Mathf.Max(height, 1.6f); c.center = new Vector3(0, height * 0.5f, 0);
        }
    }
}
