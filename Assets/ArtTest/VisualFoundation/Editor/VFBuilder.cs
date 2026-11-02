// Visual Foundation environment pass: Unity-side only, reversible (everything lives under VF_Environment + one fog setting).
// Works ONLY in Assets/Scenes/ArtTest_VisualFoundation.unity.
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class VFBuilder
{
    const string Scene = "Assets/Scenes/ArtTest_VisualFoundation.unity";
    const string Root = "Assets/ArtTest/VisualFoundation";

    static Texture2D MakeTex(string name, int w, int h, System.Func<float, float, float> alpha, Color rgb, bool linearGradient = false)
    {
        var t = new Texture2D(w, h, TextureFormat.RGBA32, false);
        var px = new Color[w * h];
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { float a = Mathf.Clamp01(alpha(x / (float)w, y / (float)h)); px[y * w + x] = new Color(rgb.r, rgb.g, rgb.b, a); }
        t.SetPixels(px); t.Apply();
        string p = Root + "/Textures/" + name + ".png"; File.WriteAllBytes(p, t.EncodeToPNG()); Object.DestroyImmediate(t);
        AssetDatabase.ImportAsset(p, ImportAssetOptions.ForceSynchronousImport);
        var ti = (TextureImporter)AssetImporter.GetAtPath(p); ti.alphaIsTransparency = true; ti.mipmapEnabled = true; ti.wrapMode = TextureWrapMode.Clamp; ti.SaveAndReimport();
        return AssetDatabase.LoadAssetAtPath<Texture2D>(p);
    }
    static float Fbm(float x, float y, float seed, int oct)
    {
        float v = 0, amp = 0.5f, f = 1f; for (int i = 0; i < oct; i++) { v += amp * Mathf.PerlinNoise(x * f + seed, y * f + seed * 1.7f); f *= 2.03f; amp *= 0.5f; } return v;
    }
    static Material Unlit(string name, Texture2D tex)
    {
        string p = Root + "/Materials/" + name + ".mat"; AssetDatabase.DeleteAsset(p);
        var m = new Material(Shader.Find("Universal Render Pipeline/Unlit")); m.name = name;
        m.SetFloat("_Surface", 1f); m.SetFloat("_Blend", 0f); m.SetFloat("_Cull", 0f); m.SetOverrideTag("RenderType", "Transparent");
        m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha); m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha); m.SetInt("_ZWrite", 0);
        m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT"); m.renderQueue = 2990; m.SetTexture("_BaseMap", tex); m.SetColor("_BaseColor", Color.white);
        AssetDatabase.CreateAsset(m, p); return m;
    }
    static GameObject Quad(string name, Transform parent, Vector3 pos, Vector3 euler, Vector2 size, Material m)
    {
        var g = GameObject.CreatePrimitive(PrimitiveType.Quad); g.name = name; Object.DestroyImmediate(g.GetComponent<Collider>());
        g.transform.SetParent(parent, false); g.transform.position = pos; g.transform.rotation = Quaternion.Euler(euler); g.transform.localScale = new Vector3(size.x, size.y, 1f);
        var r = g.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
        GameObjectUtility.SetStaticEditorFlags(g, 0); return g;
    }

    public static string Build(bool fog)
    {
        var sc = SceneManager.GetActiveScene(); if (sc.path != Scene) return "WRONG SCENE " + sc.path; if (EditorApplication.isPlaying) return "playing";
        var old = GameObject.Find("VF_Environment"); if (old != null) Object.DestroyImmediate(old);
        var root = new GameObject("VF_Environment").transform;
        Directory.CreateDirectory(Root + "/Textures");

        // 1) Floor variation: two low-alpha overlays (dark mottling + chalky lightening), procedural placeholder until the Environment Artist textures land.
        var dark = MakeTex("VF_FloorMottle_Dark", 512, 512, (u, v) => { float n = Fbm(u * 5f, v * 5f, 3.1f, 4); float s = Mathf.SmoothStep(0.35f, 0.75f, n); return s * 0.36f; }, new Color(0.15f, 0.10f, 0.07f));
        var chalk = MakeTex("VF_FloorMottle_Chalk", 512, 512, (u, v) => { float n = Fbm(u * 7f, v * 7f, 11.7f, 4); float s = Mathf.SmoothStep(0.55f, 0.82f, n); return s * 0.13f; }, new Color(0.80f, 0.72f, 0.58f));
        var fo = new GameObject("VF_FloorOverlays").transform; fo.SetParent(root, false);
        Quad("FloorMottle_Dark", fo, new Vector3(0, 0.010f, 0), new Vector3(90, 0, 0), new Vector2(40, 40), Unlit("VF_FloorMottle_Dark", dark));
        Quad("FloorMottle_Chalk", fo, new Vector3(0, 0.011f, 0), new Vector3(90, 0, 0), new Vector2(40, 40), Unlit("VF_FloorMottle_Chalk", chalk));

        // 2) Wall-base darkening (grime) + restrained moss placeholder on the floor inside each wall.
        var grime = MakeTex("VF_WallBase_Grime", 256, 64, (u, v) => { float g = Mathf.Pow(v, 1.6f); float n = 0.65f + 0.35f * Fbm(u * 9f, v * 3f, 5.3f, 3); return g * n * 0.85f; }, new Color(0.04f, 0.03f, 0.025f));
        var moss = MakeTex("VF_WallBase_Moss", 256, 64, (u, v) => { float g = Mathf.SmoothStep(0.55f, 1f, v); float n = Mathf.SmoothStep(0.55f, 0.80f, Fbm(u * 11f, v * 4f, 17.9f, 4)); return g * n * 0.30f; }, new Color(0.26f, 0.30f, 0.15f));
        var gm = Unlit("VF_WallBase_Grime", grime); var mm = Unlit("VF_WallBase_Moss", moss);
        var wb = new GameObject("VF_WallBase").transform; wb.SetParent(root, false);
        foreach (var yaw in new[] { 0f, 90f, 180f, 270f })
        {
            var dir = new Vector3(Mathf.Sin(yaw * Mathf.Deg2Rad), 0, Mathf.Cos(yaw * Mathf.Deg2Rad));
            Quad("Grime_" + yaw, wb, dir * (19.5f - 1.6f) + Vector3.up * 0.013f, new Vector3(90, yaw, 0), new Vector2(39, 3.2f), gm);
            Quad("Moss_" + yaw, wb, dir * (19.5f - 1.0f) + Vector3.up * 0.014f, new Vector3(90, yaw, 0), new Vector2(39, 2.0f), mm);
        }

        // 3) What is beyond the walls / through the arch: dark warm ground plane instead of raw clear colour.
        var og = GameObject.CreatePrimitive(PrimitiveType.Quad); og.name = "VF_OuterGround"; Object.DestroyImmediate(og.GetComponent<Collider>()); og.transform.SetParent(root, false);
        og.transform.position = new Vector3(0, -0.32f, 0); og.transform.rotation = Quaternion.Euler(90, 0, 0); og.transform.localScale = new Vector3(160, 160, 1);
        string op = Root + "/Materials/VF_OuterGround.mat"; AssetDatabase.DeleteAsset(op); var om = new Material(Shader.Find("Universal Render Pipeline/Lit")); om.SetColor("_BaseColor", new Color(0.11f, 0.09f, 0.075f)); om.SetFloat("_Smoothness", 0f); om.SetFloat("_Cull", 0f); AssetDatabase.CreateAsset(om, op);
        og.GetComponent<MeshRenderer>().sharedMaterial = om; og.GetComponent<MeshRenderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;

        // 4) Atmosphere: linear fog (distance-based, dark warm) to push the far side back. Scene-level setting.
        RenderSettings.fog = fog; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 26f; RenderSettings.fogEndDistance = 70f; RenderSettings.fogColor = new Color(0.10f, 0.085f, 0.075f);

        // 5) Focal hierarchy: warm accent light on the altar (amber, never cyan), no shadows.
        var lights = new GameObject("VF_Lights").transform; lights.SetParent(root, false);
        var lg = new GameObject("VF_AltarAccent"); lg.transform.SetParent(lights, false); lg.transform.position = new Vector3(-12.3f, 2.4f, 12.3f);
        var l = lg.AddComponent<Light>(); l.type = LightType.Point; l.color = new Color(1f, 0.62f, 0.30f); l.intensity = 6f; l.range = 10f; l.shadows = LightShadows.None; l.lightmapBakeType = LightmapBakeType.Realtime;

        // 6) Props from EXISTING kit pieces only, all >= 13 m from the arena centre (outside the central combat area).
        var pr = new GameObject("VF_Props").transform; pr.SetParent(root, false);
        var props = new[] { ("ENV_Temple_Rubble_A", -16.5f, -15.5f, 30f), ("ENV_Temple_Rubble_B", 15f, -16f, 200f), ("ENV_Temple_Rubble_A", 17.2f, 6f, 90f), ("ENV_Temple_ColumnDrum_A", -17f, 2f, 40f), ("ENV_Temple_Rubble_B", -6f, -17.4f, 120f), ("ENV_Temple_Rubble_A", 11f, 17f, 250f) };
        int pi = 0; foreach (var p in props)
        {
            var m = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/ArtTest/Environment/Models/" + p.Item1 + ".fbx"); if (m == null) continue;
            var g = (GameObject)PrefabUtility.InstantiatePrefab(m, sc); g.name = "VFProp_" + (pi++) + "_" + p.Item1.Replace("ENV_Temple_", ""); g.transform.SetParent(pr, false);
            g.transform.position = new Vector3(p.Item2, 0f, p.Item3); g.transform.rotation = Quaternion.Euler(0, p.Item4, 0);
            foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.receiveGI = ReceiveGI.LightProbes;
        }
        EditorSceneManager.MarkSceneDirty(sc); EditorSceneManager.SaveScene(sc); AssetDatabase.SaveAssets();
        return "built; props=" + pi + " fog=" + fog;
    }
    public static string Remove() { var o = GameObject.Find("VF_Environment"); if (o != null) Object.DestroyImmediate(o); RenderSettings.fog = false; return "removed"; }
}
