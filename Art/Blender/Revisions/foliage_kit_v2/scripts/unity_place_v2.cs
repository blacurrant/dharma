// script run --file ... --entry FoliageV2Place.Run   (scene edits only in the active isolated art-pass copy)
using UnityEngine; using UnityEditor; using System.Collections.Generic; using System.Linq;
public static class FoliageV2Place {
  const string M = "Assets/ArtTest/VisualFoundation/Art2/Models/ENV_Temple_Foliage_";
  static GameObject Load(string n) { return AssetDatabase.LoadAssetAtPath<GameObject>(M + n + "_v2.fbx"); }
  static Renderer[] Rs(string root) { var g = GameObject.Find(root); return g == null ? new Renderer[0] : g.GetComponentsInChildren<Renderer>(); }
  static float GroundY(Renderer[] floor, float x, float z) { var r = new Ray(new Vector3(x, 6, z), Vector3.down); float best = 0f; bool any = false; foreach (var f in floor) { float d; if (f.bounds.IntersectRay(r, out d)) { float y = 6 - d; if (!any || y > best) { best = y; any = true; } } } return any ? best : 0f; }
  // nearest wall face along dir from (x,y,z); returns distance or -1
  static float Hit(Renderer[] walls, Vector3 o, Vector3 dir) { float best = -1; foreach (var w in walls) { float d; var r = new Ray(o, dir); if (w.bounds.IntersectRay(r, out d) && d > 0.01f && (best < 0 || d < best)) best = d; } return best; }
  public static string Run() {
    var sb = new System.Text.StringBuilder();
    // 1. purge the 25 crossed-card instances
    var old = GameObject.Find("VF_EA_Foliage"); int purged = 0; if (old != null) { purged = old.transform.childCount; Object.DestroyImmediate(old); }
    sb.AppendLine("purged old foliage instances: " + purged);
    // 2. deactivate the floating flagstone wafers (reversible: SetActive(false))
    int wafers = 0; var pav = GameObject.Find("VF_EA_Paving");
    foreach (var t in pav.GetComponentsInChildren<Transform>(true)) if (t != pav.transform && (t.name.StartsWith("Flag_") || t.name.StartsWith("Kerb_")) && t.gameObject.activeSelf) { t.gameObject.SetActive(false); wafers++; }
    sb.AppendLine("flagstone wafers/kerbs deactivated: " + wafers);
    var floor = Rs("LAY_Floor"); var walls = Rs("LAY_Walls").Concat(Rs("VF_Batch1_Walls")).Concat(Rs("VF_EA_Walls")).ToArray();
    var root = new GameObject("VF_EA_Foliage"); var rng = new System.Random(2810);
    var mats = new Dictionary<string, int>(); var rows = new List<string>();
    System.Func<string, Vector3, float, float, float, string, GameObject> put = (kind, pos, yaw, sc, pitch, note) => {
      var go = (GameObject)PrefabUtility.InstantiatePrefab(Load(kind)); go.transform.SetParent(root.transform, false);
      go.transform.position = pos; go.transform.rotation = Quaternion.Euler(0, yaw, 0) * Quaternion.Euler(pitch, 0, 0); go.transform.localScale = Vector3.one * sc;
      go.name = "FOL_" + kind + "_" + (mats.ContainsKey(kind) ? ++mats[kind] : (mats[kind] = 1)).ToString("00") + "_" + note;
      var r = go.GetComponentInChildren<Renderer>(); r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On; r.receiveShadows = true; return go; };
    // ---- ground plants: (kind, x, z, note) ----
    object[][] ground = {
      new object[]{"Shrub_A",-7.5f,18.4f,"northwall"}, new object[]{"Shrub_B",1.6f,18.5f,"northwall"}, new object[]{"Shrub_B",11.3f,18.5f,"northwall"}, new object[]{"Shrub_A",16.8f,18.2f,"northwall"},
      new object[]{"Shrub_A",-18.2f,5.2f,"westwall"}, new object[]{"Shrub_B",-18.2f,-3.4f,"rubbleheap"}, new object[]{"Shrub_B",-18.3f,-9.6f,"westwall"}, new object[]{"Shrub_A",-18.2f,-16.4f,"westwall"},
      new object[]{"Shrub_B",-6.6f,13.4f,"rubbleheap"}, new object[]{"Shrub_B",-10.6f,-8.6f,"ruinbase"}, new object[]{"Shrub_A",-11.8f,-12.6f,"ruinbase"}, new object[]{"Shrub_B",13.4f,16.9f,"rubbleheap"},
      new object[]{"Tuft_A",-16.0f,7.7f,"rubbleheap"}, new object[]{"Tuft_B",-17.4f,-5.4f,"rubbleheap"}, new object[]{"Tuft_A",-15.6f,-2.2f,"rubbleheap"}, new object[]{"Tuft_B",-5.2f,11.4f,"rubbleheap"},
      new object[]{"Tuft_A",-3.4f,13.2f,"columnbase"}, new object[]{"Tuft_B",9.9f,12.8f,"columnbase"}, new object[]{"Tuft_A",-13.9f,2.7f,"columnbase"}, new object[]{"Tuft_B",-0.9f,-11.4f,"columnbase"},
      new object[]{"Tuft_A",-11.4f,-5.0f,"ruinbase"}, new object[]{"Tuft_B",-9.6f,-11.6f,"ruinbase"}, new object[]{"Tuft_A",-17.9f,0.8f,"walljoint"}, new object[]{"Tuft_B",-18.6f,-13.0f,"walljoint"},
      new object[]{"Tuft_A",-12.0f,18.7f,"walljoint"}, new object[]{"Tuft_B",5.4f,18.9f,"walljoint"}, new object[]{"Tuft_A",15.0f,15.0f,"rubbleheap"}, new object[]{"Tuft_B",12.0f,15.0f,"rubbleheap"},
    };
    foreach (var g in ground) { string k = (string)g[0]; float x = (float)g[1], z = (float)g[2]; float y = GroundY(floor, x, z);
      float sc = k.StartsWith("Shrub") ? 0.95f + (float)rng.NextDouble() * 0.3f : 0.95f + (float)rng.NextDouble() * 0.4f;
      put(k, new Vector3(x, y - 0.01f, z), (float)rng.NextDouble() * 360f, sc, 0f, (string)g[3]); }
    // ---- wall vines: attach below the cornice, hang along the wall; (x or z fixed by wall) ----
    // west wall inner normal +X: ray from interior (x=-10) toward -X ; north wall inner normal -Z: ray toward +Z
    object[][] wv = {
      new object[]{"W", 0.2f, "walljoint"}, new object[]{"W", 4.0f, "walljoint"}, new object[]{"W", 8.0f, "walljoint"}, new object[]{"W", -8.1f, "walljoint"}, new object[]{"W", -12.6f, "walljoint"}, new object[]{"W", -16.8f, "walljoint"},
      new object[]{"N", -17.5f, "walljoint"}, new object[]{"N", -12.1f, "baybesides"}, new object[]{"N", -7.9f, "walljoint"}, new object[]{"N", -2.5f, "walljoint"}, new object[]{"N", 9.2f, "pierside"}, new object[]{"N", 14.0f, "walljoint"}, new object[]{"N", 17.8f, "walljoint"},
    };
    foreach (var v in wv) { string side = (string)v[0]; float c = (float)v[1]; float top = 2.95f;
      Vector3 o, dir, nrm; if (side == "W") { o = new Vector3(-10f, 2.5f, c); dir = Vector3.left; nrm = Vector3.right; } else { o = new Vector3(c, 2.5f, 10f); dir = Vector3.forward; nrm = Vector3.back; }
      float d = Hit(walls, o, dir); if (d < 0) { sb.AppendLine("vine skipped (no wall): " + side + c); continue; }
      Vector3 p = o + dir * d; p.y = top; p += nrm * 0.06f;
      float yaw = Quaternion.LookRotation(-nrm, Vector3.up).eulerAngles.y;
      put("Vine_A", p, yaw, 0.95f + (float)rng.NextDouble() * 0.25f, 0f, side + "wall_" + v[2]); }
    // ---- pier / broken column cap drapes (top of the target's bounds) ----
    string[] caps = { "LAY_Pillar_D_001", "VF_B1_B1_Ruin_1", "VF_B1_B1_Ruin_3", "VF_EA_Ruin_0" };
    foreach (var nme in caps) { var t = GameObject.Find(nme); if (t == null) { sb.AppendLine("cap target missing " + nme); continue; }
      var rs = t.GetComponentsInChildren<Renderer>(); var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
      put("Vine_B", new Vector3(b.center.x, b.max.y - 0.08f, b.center.z), (float)rng.NextDouble() * 360f, 0.85f, 0f, "cap_" + nme); }
    // ---- validation ----
    var all = root.GetComponentsInChildren<Renderer>(); float minR = 1e9f; int inside = 0;
    foreach (var r in all) { var p = r.transform.parent.GetComponent<Transform>() == root.transform ? r.transform.position : r.transform.position; float rr = new Vector2(r.transform.position.x, r.transform.position.z).magnitude; var bb = r.bounds; float rb = 1e9f; foreach (var c in new[]{ new Vector2(bb.min.x,bb.min.z), new Vector2(bb.max.x,bb.min.z), new Vector2(bb.min.x,bb.max.z), new Vector2(bb.max.x,bb.max.z)}) rb = Mathf.Min(rb, c.magnitude); minR = Mathf.Min(minR, Mathf.Min(rr, rb)); if (Mathf.Min(rr, rb) < 10f) inside++; }
    sb.AppendLine("instances: " + root.transform.childCount + " | min radius (origin + bounds corners): " + minR.ToString("F2") + " m | instances with any bound corner/origin < 10 m: " + inside);
    UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    return sb.ToString();
  }
}
