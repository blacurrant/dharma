// Visual Foundation Batch 1: GRAYBOX proxies (VF_Proxy_*) built from the Environment Artist's placement table, then (later) the real models.
// Art-test scene only; everything is removable (RemoveProxies) and the whole batch can be toggled (SetBatch) for before/after captures.
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class VF4Builder
{
    const string Root = "Assets/ArtTest/VisualFoundation";
    const string TablePath = "Art/Blender/Revisions/batch1/handoff/Batch1_Placement.json";
    [System.Serializable] class Row { public string instance, group, mesh, part, role; public float unity_x, unity_y, unity_z, yaw_front_to_plusZ, yaw_front_to_minusZ, scale; }
    [System.Serializable] class Table { public Row[] instances; }

    static Material Mat(string name, Color c, float smooth = 0.05f)
    {
        string p = Root + "/Materials/" + name + ".mat"; var ex = AssetDatabase.LoadAssetAtPath<Material>(p); if (ex != null) { ex.SetColor("_BaseColor", c); return ex; }
        var m = new Material(Shader.Find("Universal Render Pipeline/Lit")); m.name = name; m.SetColor("_BaseColor", c); m.SetFloat("_Smoothness", smooth); m.SetFloat("_Metallic", 0f); m.enableInstancing = true;
        AssetDatabase.CreateAsset(m, p); return m;
    }

    static GameObject Box(string name, Transform parent, Vector3 pos, Vector3 size, Quaternion rot, Material m, bool cast, bool collider)
    {
        var g = GameObject.CreatePrimitive(PrimitiveType.Cube); g.name = name; Object.DestroyImmediate(g.GetComponent<Collider>()); g.transform.SetParent(parent, false);
        g.transform.position = pos; g.transform.rotation = rot; g.transform.localScale = size;
        var r = g.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = cast ? ShadowCastingMode.On : ShadowCastingMode.Off; r.receiveShadows = true; r.receiveGI = ReceiveGI.LightProbes;
        if (collider) g.AddComponent<BoxCollider>();
        return g;
    }
    static GameObject Cyl(string name, Transform parent, Vector3 pos, float radius, float height, Quaternion rot, Material m, bool collider)
    {
        var g = GameObject.CreatePrimitive(PrimitiveType.Cylinder); g.name = name; Object.DestroyImmediate(g.GetComponent<Collider>()); g.transform.SetParent(parent, false);
        g.transform.position = pos; g.transform.rotation = rot; g.transform.localScale = new Vector3(radius * 2f, height * 0.5f, radius * 2f); // cylinder primitive is 2 m tall
        var r = g.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; r.receiveGI = ReceiveGI.LightProbes;
        if (collider) { var c = g.AddComponent<CapsuleCollider>(); c.direction = 1; }
        return g;
    }

    public static string RemoveProxies()
    {
        int n = 0; foreach (var t in Object.FindObjectsByType<Transform>(FindObjectsInactive.Include).Where(t => t.name.StartsWith("VF_Proxy_") || t.name == "VF_Batch1_Proxies").Select(t => t.gameObject).Distinct().ToList()) { if (t != null) { Object.DestroyImmediate(t); n++; } }
        SetSwapped(false); return "removed " + n;
    }

    static readonly string[] Swapped = { "VFProp_1_Brazier_A", "VFProp_2_Brazier_A" }; // the EA approach braziers that the pylon pair replaces (Part 7.3)
    static void SetSwapped(bool batchOn)
    {
        foreach (var n in Swapped) { var g = FindIncl(n); if (g != null) g.SetActive(!batchOn); }
        var l11 = FindIncl("L11_BrazierLights"); if (l11 != null) l11.SetActive(!batchOn);
    }
    public static GameObject FindIncl(string name) => Object.FindObjectsByType<Transform>(FindObjectsInactive.Include).Select(t => t.gameObject).FirstOrDefault(g => g.name == name);

    // Toggle the whole batch (graybox or real): VF_Batch1_Proxies / VF_Batch1 root on/off, and the replaced braziers inverse.
    public static string SetBatch(bool on)
    {
        foreach (var n in new[] { "VF_Batch1_Proxies", "VF_Batch1" }) { var g = FindIncl(n); if (g != null) g.SetActive(on); }
        SetSwapped(on); return "batch " + (on ? "ON" : "OFF");
    }

    public static string BuildProxies(bool save = true)
    {
        var sc = EditorSceneManager.GetActiveScene(); if (sc.path != "Assets/Scenes/ArtTest_VisualFoundation.unity") return "WRONG SCENE " + sc.path;
        RemoveProxies();
        var tbl = JsonUtility.FromJson<Table>(File.ReadAllText(TablePath)); var sb = new StringBuilder("table rows: " + tbl.instances.Length + "\n");
        var root = new GameObject("VF_Batch1_Proxies").transform;
        Transform Grp(string n, bool on = true) { var g = new GameObject("VF_Proxy_" + n); g.transform.SetParent(root, false); g.SetActive(on); return g.transform; }
        var gWalls = Grp("Walls"); var gBackD = Grp("Backdrop_directive_28_55m"); var gBackN = Grp("Backdrop_recommended_visible_band", false); var gPyl = Grp("Pylons"); var gRuin = Grp("Ruins"); var gLights = Grp("PylonLights");
        var mWall = Mat("VF4_Proxy_Wall", new Color(0.40f, 0.36f, 0.31f)); var mBack = Mat("VF4_Proxy_Backdrop", new Color(0.13f, 0.12f, 0.13f), 0f); var mPyl = Mat("VF4_Proxy_Pylon", new Color(0.42f, 0.38f, 0.33f)); var mFire = Mat("VF4_Proxy_Fire", new Color(0.9f, 0.55f, 0.2f), 0f); var mRuin = Mat("VF4_Proxy_Ruin", new Color(0.38f, 0.35f, 0.30f));
        int walls = 0, pyl = 0, ruins = 0, back = 0;
        foreach (var r in tbl.instances)
        {
            var pos = new Vector3(r.unity_x, r.unity_y, r.unity_z); var yaw = Quaternion.Euler(0, r.yaw_front_to_minusZ, 0); // scene convention = the minusZ column
            if (r.group == "BATCH1_Walls")
            {   // 4 m wide, 5.5 m tall, 1.3 m deep box; local z = depth, origin at the bay's floor-level front plane centre
                Box("VF_Proxy_Bay_" + r.instance, gWalls, pos + Vector3.up * 2.75f, new Vector3(4f, 5.5f, 1.3f), yaw, mWall, true, false); walls++;
            }
            else if (r.group.StartsWith("BATCH1_Backdrop"))
            {
                bool dir = r.group.Contains("directive"); var parent = dir ? gBackD : gBackN; bool west = r.mesh.EndsWith("_C");
                float w = r.mesh.EndsWith("_A") ? 30f : r.mesh.EndsWith("_B") ? 26f : 30f; float hBase = 7f, hTop = r.mesh.EndsWith("_C") ? 7f : 5f; float d = 19.3f;
                var fwd = west ? Vector3.right : Vector3.forward; Quaternion q = west ? Quaternion.Euler(0, 90, 0) : Quaternion.identity;
                Box("VF_Proxy_Backdrop_" + r.instance + "_base", parent, pos + Vector3.up * hBase * 0.5f, new Vector3(w, hBase, d), q, mBack, false, false);
                Box("VF_Proxy_Backdrop_" + r.instance + "_top", parent, pos + Vector3.up * (hBase + hTop * 0.5f), new Vector3(w * 0.62f, hTop, d * 0.62f), q, mBack, false, false); back++;
            }
            else if (r.group == "BATCH1_Pylons")
            {
                var g = new GameObject("VF_Proxy_Pylon_" + r.instance); g.transform.SetParent(gPyl, false); g.transform.position = pos; g.transform.rotation = yaw;
                Cyl("shaft", g.transform, pos + Vector3.up * 1.1f, 0.30f, 2.2f, Quaternion.identity, mPyl, false); Cyl("bowl", g.transform, pos + Vector3.up * 2.5f, 0.42f, 0.6f, Quaternion.identity, mPyl, false); Cyl("flame", g.transform, pos + Vector3.up * 2.85f, 0.25f, 0.2f, Quaternion.identity, mFire, false);
                var cc = g.AddComponent<CapsuleCollider>(); cc.radius = 0.4f; cc.height = 2.8f; cc.center = new Vector3(0, 1.4f, 0);   // primitive collider on pylons only
                foreach (var rr in g.GetComponentsInChildren<MeshRenderer>()) rr.gameObject.isStatic = false;
                var lo = new GameObject("VF_Proxy_PylonLight_" + r.instance); lo.transform.SetParent(gLights, false); lo.transform.position = pos + Vector3.up * 2.95f; var lt = lo.AddComponent<Light>(); lt.type = LightType.Point; lt.color = new Color(1f, 0.62f, 0.30f); lt.intensity = 3f; lt.range = 6f; lt.shadows = LightShadows.None; lt.lightmapBakeType = LightmapBakeType.Realtime;
                pyl++;
            }
            else if (r.group == "BATCH1_Ruins")
            {   // ruin-sized graybox: ~3 m broken pillar at the tall end (toward -x,+z), two toppled drums and a fallen slab toward +x,-z
                var g = new GameObject("VF_Proxy_Ruin_" + r.instance); g.transform.SetParent(gRuin, false); g.transform.position = pos; g.transform.rotation = yaw;
                var tall = new Vector3(-1f, 0, 1f).normalized; var low = -tall; var side = Vector3.Cross(Vector3.up, tall);
                Cyl("pillar", g.transform, pos + tall * 1.1f + Vector3.up * 1.5f, 0.55f, 3.0f, Quaternion.identity, mRuin, false);
                Cyl("drum1", g.transform, pos + low * 0.2f + side * 0.9f + Vector3.up * 0.45f, 0.45f, 0.9f, Quaternion.LookRotation(side) * Quaternion.Euler(90, 0, 0), mRuin, false);
                Cyl("drum2", g.transform, pos + low * 1.1f - side * 0.4f + Vector3.up * 0.4f, 0.4f, 0.8f, Quaternion.LookRotation(tall) * Quaternion.Euler(90, 0, 0), mRuin, false);
                Box("slab", g.transform, pos + low * 0.6f + Vector3.up * 0.2f, new Vector3(2.4f, 0.4f, 0.9f), Quaternion.LookRotation(tall), mRuin, true, false);
                var pc = g.AddComponent<CapsuleCollider>(); pc.radius = 0.6f; pc.height = 3f; pc.center = g.transform.InverseTransformPoint(pos + tall * 1.1f + Vector3.up * 1.5f);   // primitive colliders on ruins only
                var sc2 = g.AddComponent<BoxCollider>(); sc2.size = new Vector3(2.4f, 0.8f, 1.6f); sc2.center = g.transform.InverseTransformPoint(pos + low * 0.6f + Vector3.up * 0.4f);
                ruins++;
            }
        }
        sb.AppendLine("proxies: wall bays " + walls + ", backdrop masses " + back + " (both groups), pylons " + pyl + ", ruins " + ruins);
        SetSwapped(true);
        // objects named VF_Proxy_* are removable with RemoveProxies; the batch can be toggled with SetBatch
        if (save) { EditorSceneManager.MarkSceneDirty(sc); EditorSceneManager.SaveScene(sc); AssetDatabase.SaveAssets(); }
        return sb.ToString();
    }
}
