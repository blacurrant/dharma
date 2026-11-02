using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

/// Art-test only (Play Mode, added at runtime, never saved to the scene).
/// Drives REAL keyboard input through the Input System (WASD / Space / Enter) while the real gameplay scripts run,
/// and records per-frame camera metrics at a fixed 1920x1080 / 16:9 reference frame.
[DefaultExecutionOrder(1000)]
public class ArtTestSequenceRunner : MonoBehaviour
{
    public static ArtTestSequenceRunner I;
    public const int W = 1920, H = 1080;

    public bool done; public string status = "idle"; public string outDir;
    Camera cam; IsoCameraFollow iso; PlayerMotor motor; Transform player; Transform enemyT; TrainingDummy enemy;
    Health pHealth; Keyboard kb; ArenaEncounter enc; ArtTestCameraFocus focus; ArtTestCyanTelegraphPreview preview;
    SkinnedMeshRenderer body;
    string cfg, fpsMode, seq, label; bool recording; int skipDt; int shotIdx; public bool noShots; readonly StringBuilder pfl = new StringBuilder("config,fps_mode,sequence,label,unity_frame,min_margin_ring_px,player_offset_px,player_enemy_m,dashing,dt_ms\n");

    class Agg { public int dtFrames, frames, telFrames, telInFrame, notAllInFrame; public double sumDt; public float minMarginPlayer = 1e9f, minMarginFixed = 1e9f, minChar = 1e9f, maxChar = 0f, maxOffset = 0f; public float minPlayerEdge = 1e9f; public float minFps = 1e9f; public float maxDt = 0; }
    readonly Dictionary<string, Agg> aggs = new Dictionary<string, Agg>();
    readonly List<string> shots = new List<string>();

    // ---------------------------------------------------------------- setup

    public static void ForceInput()
    {   // runtime-only clone of the Input System settings: ignore app/Game-view focus so injected keyboard events always reach the game (no asset or ProjectSettings change)
        var cur = InputSystem.settings; var cl = ScriptableObject.CreateInstance<InputSettings>(); JsonUtility.FromJsonOverwrite(JsonUtility.ToJson(cur), cl);
        cl.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus; cl.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView; InputSystem.settings = cl; InputSystem.EnableDevice(Keyboard.current);
    }
    void Resolve()
    {
        ForceInput();
        cam = Camera.main; iso = cam.GetComponent<IsoCameraFollow>();
        var p = GameObject.Find("Player"); player = p.transform; motor = p.GetComponent<PlayerMotor>(); pHealth = p.GetComponent<Health>();
        var e = GameObject.Find("ArenaEnemy"); enemyT = e.transform; enemy = e.GetComponent<TrainingDummy>();
        enc = FindFirstObjectByType<ArenaEncounter>(); focus = FindFirstObjectByType<ArtTestCameraFocus>(); preview = FindFirstObjectByType<ArtTestCyanTelegraphPreview>();
        kb = Keyboard.current;
        foreach (var r in p.GetComponentsInChildren<SkinnedMeshRenderer>()) if (r.name == "Paladin_J_Nordstrom") body = r;
        if (body == null) body = p.GetComponentInChildren<SkinnedMeshRenderer>();
        typeof(Health).GetField("maxHealth", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance).SetValue(pHealth, 1e6f);
    }

    public static ArtTestSequenceRunner Create() { var go = new GameObject("ArtTestSequenceRunner"); I = go.AddComponent<ArtTestSequenceRunner>(); I.Resolve(); return I; }

    public string ApplyConfig(float size, Vector3 offset, bool biased, int targetFps)
    {
#if UNITY_EDITOR
        var so = new UnityEditor.SerializedObject(iso);
        so.FindProperty("orthographicSize").floatValue = size; so.FindProperty("offset").vector3Value = offset;
        so.ApplyModifiedProperties();
#endif
        cam.orthographicSize = size; cam.aspect = 16f / 9f; cam.transform.rotation = Quaternion.LookRotation(-offset.normalized);
        focus.enabled = biased;
        if (!biased) { focus.worldBias = Vector3.zero; iso.Target = player; }
        else { focus.worldBias = new Vector3(-1f, 0f, 1f); focus.enemyWeight = 0.35f; focus.maxEnemyPull = 3f; }
        Application.targetFrameRate = targetFps;
        iso.Snap();
        return "size=" + cam.orthographicSize + " offset=" + offset + " biased=" + biased + " targetFps=" + targetFps + " target=" + (iso.Target != null ? iso.Target.name : "null");
    }

    // ---------------------------------------------------------------- input
    void Keys(params Key[] k) { InputSystem.QueueStateEvent(kb, new KeyboardState(k)); }
    static readonly Key[][] DirKeys = {
        new[]{Key.W}, new[]{Key.W,Key.D}, new[]{Key.D}, new[]{Key.S,Key.D}, new[]{Key.S}, new[]{Key.S,Key.A}, new[]{Key.A}, new[]{Key.W,Key.A} };
    static readonly string[] DirName = { "W(up)", "WD", "D(right)", "SD", "S(down)", "SA", "A(left)", "WA" };
    static Vector2 DirInput(int i) { var k = DirKeys[i]; float x = 0, y = 0; foreach (var q in k) { if (q == Key.W) y += 1; if (q == Key.S) y -= 1; if (q == Key.D) x += 1; if (q == Key.A) x -= 1; } return new Vector2(x, y).normalized; }
    Vector3 CamFwd() { var f = cam.transform.forward; f.y = 0; return f.normalized; }
    Vector3 CamRight() { var r = cam.transform.right; r.y = 0; return r.normalized; }
    Vector3 DirWorld(int i) { var v = DirInput(i); return (CamRight() * v.x + CamFwd() * v.y).normalized; }
    Key[] SteerKeys(Vector3 worldDir, bool attack = false, bool dash = false)
    {
        var l = new List<Key>(); float x = Vector3.Dot(worldDir, CamRight()), y = Vector3.Dot(worldDir, CamFwd());
        if (y > 0.38f) l.Add(Key.W); if (y < -0.38f) l.Add(Key.S); if (x > 0.38f) l.Add(Key.D); if (x < -0.38f) l.Add(Key.A);
        if (attack) l.Add(Key.Enter); if (dash) l.Add(Key.Space);
        return l.ToArray();
    }

    // ---------------------------------------------------------------- world helpers
    void Teleport(Vector3 p)
    {
        skipDt = 3;
        var cc = player.GetComponent<CharacterController>(); cc.enabled = false; player.position = new Vector3(p.x, 0.02f, p.z); cc.enabled = true;
        if (focus.enabled) focus.transform.position = new Vector3(p.x, 0, p.z);
        iso.Snap();
    }
    void PlaceEnemy(Vector3 p, Vector3 faceDir)
    {
        var cc = enemyT.GetComponent<CharacterController>(); cc.enabled = false; enemyT.position = new Vector3(p.x, 0f, p.z); enemyT.rotation = Quaternion.LookRotation(faceDir.sqrMagnitude < 0.01f ? Vector3.back : faceDir.normalized); cc.enabled = true;
    }
    void Fresh(bool enemyActive)
    {
        enc.Restart(); pHealth.Revive(); Keys();
        enemy.enabled = enemyActive;
        if (!enemyActive) { var t = enemyT.Find("EnemyAttackTelegraph"); }
        iso.Snap();
    }
    IEnumerator Wait(float s) { float t = Time.time + s; while (Time.time < t) yield return null; }

    // ---------------------------------------------------------------- measurement
    Vector2 Px(Vector3 w) { var v = cam.WorldToViewportPoint(w); return new Vector2(v.x * W, v.y * H); }
    static float EdgeMargin(Vector2 p) { return Mathf.Min(Mathf.Min(p.x, W - p.x), Mathf.Min(p.y, H - p.y)); }
    float RingMargin(Vector3 c, float R)
    {
        float m = 1e9f; for (int i = 0; i < 180; i++) { float a = i * Mathf.PI * 2f / 180f; m = Mathf.Min(m, EdgeMargin(Px(c + new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * R))); }
        return m;
    }
    bool InFrame(Vector2 p) { return p.x >= 0 && p.x <= W && p.y >= 0 && p.y <= H; }
    Agg A(string key) { if (!aggs.TryGetValue(key, out var a)) { a = new Agg(); aggs[key] = a; } return a; }

    void LateUpdate()
    {
        if (!recording || cam == null) return;
        var a = A(cfg + "|" + fpsMode + "|" + seq + "|" + label); var all = A(cfg + "|" + fpsMode + "|" + seq + "|ALL");
        float dt = Time.unscaledDeltaTime; bool skip = skipDt > 0; if (skipDt > 0) skipDt--;
        Vector3 pp = player.position; Vector3 flat = new Vector3(pp.x, 0, pp.z);
        float mPl = RingMargin(flat, 10f), mFx = RingMargin(Vector3.zero, 10f);
        float top = body != null ? body.bounds.max.y : pp.y + 2f;
        var feet = Px(flat); var head = Px(new Vector3(pp.x, top, pp.z));
        float charPct = Mathf.Abs(head.y - feet.y) / H * 100f;
        bool pOk = InFrame(feet) && InFrame(head);
        float eDist = new Vector2(enemyT.position.x - pp.x, enemyT.position.z - pp.z).magnitude;
        bool eOk = enemy.IsDead || eDist > 10f || (InFrame(Px(enemyT.position)) && InFrame(Px(enemyT.position + Vector3.up * 2f))); // enemy only required in frame when engaged (<10 m)
        bool tele = enemy.IsTelegraphing; bool tOk = true;
        if (tele)
        {
            Vector3 fwd = enemyT.forward; float r = enemy.AttackRange;
            foreach (var d in new[] { Quaternion.Euler(0, -58, 0) * fwd, fwd, Quaternion.Euler(0, 58, 0) * fwd }) if (!InFrame(Px(enemyT.position + d * r))) tOk = false;
        }
        float off = (feet - new Vector2(W / 2f, H / 2f)).magnitude;
        pfl.AppendLine(cfg + "," + fpsMode + "," + seq + "," + label + "," + Time.frameCount + "," + mPl.ToString("F0") + "," + off.ToString("F0") + "," + eDist.ToString("F2", CultureInfo.InvariantCulture) + "," + (motor.IsDashing ? 1 : 0) + "," + (dt * 1000f).ToString("F2", CultureInfo.InvariantCulture));
        foreach (var g in new[] { a, all })
        {
            g.frames++; if (!skip) { g.dtFrames++; g.sumDt += dt; g.maxDt = Mathf.Max(g.maxDt, dt); }
            g.minMarginPlayer = Mathf.Min(g.minMarginPlayer, mPl); g.minMarginFixed = Mathf.Min(g.minMarginFixed, mFx);
            g.minChar = Mathf.Min(g.minChar, charPct); g.maxChar = Mathf.Max(g.maxChar, charPct); g.maxOffset = Mathf.Max(g.maxOffset, off);
            g.minPlayerEdge = Mathf.Min(g.minPlayerEdge, Mathf.Min(EdgeMargin(feet), EdgeMargin(head)));
            if (!(pOk && eOk)) g.notAllInFrame++;
            if (tele) { g.telFrames++; if (tOk && pOk && eOk) g.telInFrame++; }
        }
    }

    // ---------------------------------------------------------------- captures
    public Texture2D Grab()
    {
        var rt = RenderTexture.GetTemporary(W, H, 24, RenderTextureFormat.ARGB32); var prev = cam.targetTexture; cam.targetTexture = rt; cam.Render(); cam.targetTexture = prev;
        var old = RenderTexture.active; RenderTexture.active = rt; var t = new Texture2D(W, H, TextureFormat.RGB24, false); t.ReadPixels(new Rect(0, 0, W, H), 0, 0); t.Apply(); RenderTexture.active = old; RenderTexture.ReleaseTemporary(rt); return t;
    }
    SkinnedMeshRenderer[] PlayerRenderers() { return player.GetComponentsInChildren<SkinnedMeshRenderer>(); }
    // Direct pixel measurement: render the frame with the player's shadow-only vs normally; the pixel diff is the character silhouette.
    Vector4 MeasureChar()
    {
        var rs = PlayerRenderers();
        foreach (var r in rs) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly;
        var a = Grab();
        foreach (var r in rs) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
        var b = Grab();
        var pa = a.GetPixels32(); var pb = b.GetPixels32(); int minY = H, maxY = -1, minX = W, maxX = -1;
        for (int y = 0; y < H; y++) for (int x = 0; x < W; x++)
        {
            int i = y * W + x; int d = Mathf.Abs(pa[i].r - pb[i].r) + Mathf.Abs(pa[i].g - pb[i].g) + Mathf.Abs(pa[i].b - pb[i].b);
            if (d > 24) { if (y < minY) minY = y; if (y > maxY) maxY = y; if (x < minX) minX = x; if (x > maxX) maxX = x; }
        }
        Destroy(a); Destroy(b);
        return maxY < 0 ? new Vector4(0, 0, 0, 0) : new Vector4(maxY - minY + 1, maxX - minX + 1, minY, maxY);
    }
    void Dot(Color32[] px, Vector2 p, Color32 c) { for (int dy = -2; dy <= 2; dy++) for (int dx = -2; dx <= 2; dx++) { int x = (int)p.x + dx, y = (int)p.y + dy; if (x >= 0 && x < W && y >= 0 && y < H) px[y * W + x] = c; } }
    public string Shot(string tag)
    {
        if (noShots) { skipDt = 3; return ""; }
        var t = Grab(); var px = t.GetPixels32();
        Vector3 pf = new Vector3(player.position.x, 0, player.position.z);
        for (int i = 0; i < 360; i++) { float a = i * Mathf.PI / 180f; var v = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * 10f; Dot(px, Px(pf + v), new Color32(255, 40, 40, 255)); Dot(px, Px(v), new Color32(60, 120, 255, 255)); }
        t.SetPixels32(px); t.Apply();
        string n = cfg + "_" + fpsMode + "_" + seq + "_" + tag + ".png"; Directory.CreateDirectory(outDir + "/shots"); File.WriteAllBytes(outDir + "/shots/" + n, t.EncodeToPNG()); Destroy(t);
        var m = MeasureChar(); float modelH = body != null ? body.bounds.size.y : 0f;
        File.AppendAllText(outDir + "/char_height.csv", cfg + "," + fpsMode + "," + seq + "," + tag + "," + m.x + "," + (m.x / H * 100f).ToString("F2", CultureInfo.InvariantCulture) + "," + m.y + "," + modelH.ToString("F3", CultureInfo.InvariantCulture) + "\n");
        shots.Add(n); skipDt = 3; return n;
    }

    // ---------------------------------------------------------------- sequences
    public void RunMatrix(string config, string fps, string[] seqs)
    {
        cfg = config; fpsMode = fps; done = false; StartCoroutine(RunAll(seqs));
    }

    IEnumerator RunAll(string[] seqs)
    {
        yield return null; yield return null; // settle: let IsoCameraFollow.LateUpdate re-aim after the config change before any frame is logged
        foreach (var s in seqs)
        {
            seq = s; status = cfg + "/" + fpsMode + "/" + s; shotIdx = 0;
            switch (s)
            {
                case "idle": yield return Idle(); break;
                case "run": yield return Run(); break;
                case "dash_rest": yield return Dash(false); break;
                case "dash_run": yield return Dash(true); break;
                case "attack": yield return Attack(); break;
                case "dodge": yield return Dodge(); break;
                case "chain": yield return Chain(); break;
                case "edge_up": yield return Edge(0); break;
                case "edge_down": yield return Edge(4); break;
                case "far_chase_up": yield return FarChase(0); break;
                case "far_chase_down": yield return FarChase(4); break;
            }
            Keys(); recording = false;
        }
        status = "done " + cfg + "/" + fpsMode; done = true;
    }

    IEnumerator Settle(Vector3 start, bool enemyActive) { Fresh(enemyActive); if (!enemyActive) PlaceEnemy(new Vector3(0, 0, 8), Vector3.back); Teleport(start); yield return Wait(0.5f); Keys(); }

    IEnumerator Idle() { yield return Settle(Vector3.zero, false); label = "idle"; recording = true; yield return Wait(1f); Shot("a"); yield return Wait(1f); recording = false; }

    IEnumerator Run()
    {
        for (int i = 0; i < 8; i++)
        {
            Vector3 d = DirWorld(i); yield return Settle(-d * 8f, false); label = DirName[i]; recording = true;
            Keys(DirKeys[i]); yield return Wait(1.0f); if (i == 0 || i == 4) Shot(DirName[i]); yield return Wait(1.0f); Keys(); recording = false;
        }
    }

    IEnumerator Dash(bool fromRun)
    {
        for (int i = 0; i < 8; i++)
        {
            Vector3 d = DirWorld(i); yield return Settle(-d * 5f, false); label = DirName[i]; recording = true;
            if (fromRun) { Keys(DirKeys[i]); yield return Wait(0.5f); }
            var k = new List<Key>(DirKeys[i]) { Key.Space }; Keys(k.ToArray()); yield return null; yield return null; Keys(DirKeys[i]);
            if (!fromRun) { yield return Wait(0.1f); }
            yield return Wait(0.12f); if (i == 0 || i == 4) Shot(DirName[i]); yield return Wait(fromRun ? 0.35f : 0.1f); Keys(); yield return Wait(0.6f); recording = false;
        }
    }

    IEnumerator Attack()
    {
        yield return Settle(new Vector3(0, 0, 3f), false); label = "attack"; recording = true;
        float t0 = Time.time;
        while (Time.time - t0 < 3f) { Vector3 to = enemyT.position - player.position; to.y = 0; if (to.magnitude < 1.5f) break; Keys(SteerKeys(to.normalized)); yield return null; }
        Keys(); float t1 = Time.time; Shot("a");
        while (Time.time - t1 < 1.8f) { Vector3 to = enemyT.position - player.position; to.y = 0; Keys(SteerKeys(to.magnitude > 1.7f ? to.normalized : Vector3.zero, true)); yield return null; if (Time.time - t1 > 0.6f && shotIdx == 0) { shotIdx = 1; Shot("b"); } }
        Keys(); recording = false;
    }

    IEnumerator Dodge()
    {
        yield return Settle(new Vector3(0, 0, 5.5f), true); label = "dodge"; recording = true;
        float t0 = Time.time; bool dashed = false;
        while (Time.time - t0 < 7f)
        {
            if (!dashed && enemy.IsTelegraphing)
            {
                Shot("telegraph_start");
                Vector3 to = enemyT.position - player.position; to.y = 0; Keys(SteerKeys(to.normalized, false, true)); yield return null; yield return null; Keys(SteerKeys(to.normalized)); dashed = true; yield return Wait(0.16f); Shot("dash_through"); yield return Wait(1.2f); break;
            }
            yield return null;
        }
        Keys(); recording = false; if (!dashed) status += " (NO TELEGRAPH OBSERVED)";
    }

    IEnumerator Chain()
    {
        yield return Settle(new Vector3(0, 0, 0), true); label = "chain"; recording = true;
        float t0 = Time.time;
        while (Time.time - t0 < 1.0f) { Vector3 to = enemyT.position - player.position; to.y = 0; Keys(SteerKeys(to.normalized)); yield return null; }
        { Vector3 to = enemyT.position - player.position; to.y = 0; Keys(SteerKeys(to.normalized, false, true)); yield return null; yield return null; Keys(SteerKeys(to.normalized)); }
        yield return Wait(0.25f); Shot("after_dash");
        float t1 = Time.time;
        while (Time.time - t1 < 2.0f) { Vector3 to = enemyT.position - player.position; to.y = 0; Keys(SteerKeys(to.magnitude > 1.7f ? to.normalized : Vector3.zero, true)); yield return null; }
        Shot("end"); Keys(); recording = false;
    }

    IEnumerator FarChase(int dirIdx)
    {
        Vector3 d = DirWorld(dirIdx); yield return Settle(-d * 3f, false); PlaceEnemy(d * 9f, -d); label = "far_chase"; recording = true;
        float t0 = Time.time; bool armed = false; int a0 = enemy.AttackCount;
        while (Time.time - t0 < 5.5f)
        {
            Vector3 to = enemyT.position - player.position; to.y = 0;
            if (!armed && Time.time - t0 > 1.8f) { enemy.enabled = true; armed = true; Shot("mid_chase"); }
            Keys(SteerKeys(to.magnitude > 1.8f ? to.normalized : Vector3.zero, to.magnitude < 2.2f));
            yield return null;
        }
        Shot("end"); Keys(); recording = false;
    }


    // ---------------------------------------------------------------- telegraph luma lift (photometry on a held pose; NOT combat validation)
    public bool lumaDone;
    public void Luma() { lumaDone = false; StartCoroutine(LumaRoutine()); }
    static float Luma709(Color32 c) { return (0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b) / 255f; }
    Vector3 FindShadowPoint()
    {
        var lt = GameObject.Find("Directional Light").transform; Vector3 toLight = -lt.forward; Vector3 best = Vector3.zero; float bestD = 1e9f;
        System.Func<float, float, bool> sh = (x, z) => { RaycastHit h; return Physics.Raycast(new Vector3(x, 0.05f, z), toLight, out h, 60f) && h.collider.name != "Proxy_Ground"; };
        for (float x = -18.5f; x <= 18.5f; x += 0.5f) for (float z = -18.5f; z <= 18.5f; z += 0.5f)
        {
            bool ok = true; foreach (var o in new[] { new Vector2(0, 0), new Vector2(1.5f, 0), new Vector2(-1.5f, 0), new Vector2(0, 1.5f), new Vector2(0, -1.5f) }) ok &= sh(x + o.x, z + o.y);
            float d = new Vector2(x, z).magnitude; if (ok && d < bestD) { bestD = d; best = new Vector3(x, 0, z); }
        }
        return bestD < 1e8f ? best : new Vector3(999, 0, 999);
    }
    GameObject _teleRoot;
    GameObject TeleRoot() { if (_teleRoot == null) { var t = typeof(ArtTestCyanTelegraphPreview).GetField("_root", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance); _teleRoot = ((Transform)t.GetValue(preview)).gameObject; } return _teleRoot; }
    void SetParts(bool area, bool fill, bool edge, bool front)
    {
        var root = TeleRoot(); if (root == null) return;
        root.SetActive(true); foreach (Transform c in root.transform) c.gameObject.SetActive(c.name == "Area" ? area : c.name == "Fill" ? fill : c.name == "Edge" ? edge : front);
    }
    IEnumerator LumaRoutine()
    {
        var tt = typeof(TrainingDummy); var bf = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance;
        var csv = new StringBuilder("surface,alpha_fill,part,pixels_lifted,mean_luma_lift,p10_luma_lift,max_luma_lift\n");
        Vector3 shadowPt = FindShadowPoint();
        var spots = new List<KeyValuePair<string, Vector3>> { new KeyValuePair<string, Vector3>("lit_floor", new Vector3(0, 0, 0)) };
        if (shadowPt.x < 900) spots.Add(new KeyValuePair<string, Vector3>("shadowed_floor", shadowPt));
        status = "luma shadowPt=" + shadowPt;
        foreach (var sp in spots)
        {
            foreach (float alpha in new[] { 0.26f, 0.40f, 0.45f })
            {
                Fresh(false); Keys(); Teleport(sp.Value - new Vector3(0, 0, 2.2f)); PlaceEnemy(sp.Value, Vector3.back);
                preview.startAlpha = alpha; preview.endAlpha = alpha; preview.hideOriginalTelegraph = true;
                tt.GetMethod("BeginTelegraph", bf).Invoke(enemy, new object[] { Vector3.back }); tt.GetField("_windupRemaining", bf).SetValue(enemy, enemy.AttackWindup * 0.01f);
                foreach (var part in new[] { "fill+area", "edge+front" })
                {
                    preview.enabled = true; yield return null; yield return null; yield return null; preview.enabled = false;
                    if (part == "fill+area") SetParts(true, true, false, false); else SetParts(false, false, true, true);
                    yield return null; var with = Grab(); 
                    TeleRoot().SetActive(false); yield return null; var without = Grab();
                    var a = with.GetPixels32(); var b = without.GetPixels32(); var lifts = new List<float>();
                    for (int i = 0; i < a.Length; i++) { float d = Luma709(a[i]) - Luma709(b[i]); if (d > 0.004f) lifts.Add(d); }
                    lifts.Sort(); float mean = 0; foreach (var l in lifts) mean += l; if (lifts.Count > 0) mean /= lifts.Count;
                    csv.AppendLine(sp.Key + "," + alpha.ToString("F2", CultureInfo.InvariantCulture) + "," + part + "," + lifts.Count + "," + mean.ToString("F3", CultureInfo.InvariantCulture) + "," + (lifts.Count > 0 ? lifts[lifts.Count / 10] : 0).ToString("F3", CultureInfo.InvariantCulture) + "," + (lifts.Count > 0 ? lifts[lifts.Count - 1] : 0).ToString("F3", CultureInfo.InvariantCulture));
                    if (alpha == 0.45f && part == "fill+area") { SetParts(true, true, true, true); TeleRoot().SetActive(true); yield return null; cfg = "luma"; fpsMode = "x"; seq = sp.Key; var w2 = Grab(); File.WriteAllBytes(outDir + "/luma_" + sp.Key + "_with_45.png", w2.EncodeToPNG()); File.WriteAllBytes(outDir + "/luma_" + sp.Key + "_without_45.png", without.EncodeToPNG()); Destroy(w2); }
                    Destroy(with); Destroy(without);
                }
            }
        }
        // real model heights (union of all SkinnedMeshRenderer bounds at current pose)
        System.Func<Transform, string> hh = (tr) => { Bounds bb = new Bounds(); bool first = true; foreach (var r in tr.GetComponentsInChildren<SkinnedMeshRenderer>()) { if (first) { bb = r.bounds; first = false; } else bb.Encapsulate(r.bounds); } return bb.size.ToString("F3") + " (y=" + bb.size.y.ToString("F3") + ")"; };
        File.WriteAllText(outDir + "/model_heights.txt", "player union SMR bounds size: " + hh(player) + "\nenemy union SMR bounds size: " + hh(enemyT) + "\nplayer CC height=" + player.GetComponent<CharacterController>().height + "\n");
        File.WriteAllText(outDir + "/luma_lift.csv", csv.ToString()); lumaDone = true; status = "luma done";
    }

    // ---------------------------------------------------------------- performance (raw samples)
    public bool perfDone;
    public void Perf(string label, int frames) { perfDone = false; StartCoroutine(PerfRoutine(label, frames)); }
    IEnumerator PerfRoutine(string label, int frames)
    {
        enemy.enabled = false; Keys(); enc.Restart(); pHealth.Revive(); enemy.enabled = false;
        Teleport(Vector3.zero); PlaceEnemy(new Vector3(0, 0, 2f), Vector3.back);
        var t = typeof(TrainingDummy); t.GetMethod("BeginTelegraph", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance).Invoke(enemy, new object[] { Vector3.back });
        t.GetField("_windupRemaining", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance).SetValue(enemy, enemy.AttackWindup * 0.3f);
        var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32); cam.targetTexture = rt; // identical 1920x1080 render cost for every row
        var ft = new FrameTiming[1]; var sb = new StringBuilder("frame,dt_ms,cpuFrame_ms,cpuMain_ms,gpu_ms,drawCalls,setPass,triangles,shadowCasters\n");
        for (int i = 0; i < 60; i++) yield return null; // warm-up (shader compile / caches)
        for (int i = 0; i < frames; i++)
        {
            yield return null; FrameTimingManager.CaptureFrameTimings(); uint n = FrameTimingManager.GetLatestTimings(1, ft);
#if UNITY_EDITOR
            int dc = UnityEditor.UnityStats.drawCalls, sp = UnityEditor.UnityStats.setPassCalls, tr = UnityEditor.UnityStats.triangles, sc = UnityEditor.UnityStats.shadowCasters;
#else
            int dc = 0, sp = 0, tr = 0, sc = 0;
#endif
            sb.AppendLine(i + "," + (Time.unscaledDeltaTime * 1000f).ToString("F3", CultureInfo.InvariantCulture) + "," + (n > 0 ? ft[0].cpuFrameTime : 0).ToString("F3", CultureInfo.InvariantCulture) + "," + (n > 0 ? ft[0].cpuMainThreadFrameTime : 0).ToString("F3", CultureInfo.InvariantCulture) + "," + (n > 0 ? ft[0].gpuFrameTime : 0).ToString("F3", CultureInfo.InvariantCulture) + "," + dc + "," + sp + "," + tr + "," + sc);
        }
        cam.targetTexture = null; rt.Release(); Destroy(rt);
        Directory.CreateDirectory(outDir + "/perf"); File.WriteAllText(outDir + "/perf/perf_" + label + ".csv", sb.ToString()); perfDone = true; status = "perf done " + label;
    }

    IEnumerator Edge(int dirIdx)
    {
        Vector3 d = DirWorld(dirIdx); Vector3 p = d * 10f; yield return Settle(p, true);
        PlaceEnemy(p + d * 2f, -d); label = "edge"; recording = true; int a0 = enemy.AttackCount; float t0 = Time.time; bool shot1 = false;
        while (Time.time - t0 < 6f && enemy.AttackCount == a0) { if (!shot1 && enemy.IsTelegraphing && enemy.WindupProgress > 0.5f) { shot1 = true; Shot("telegraph_mid"); } yield return null; }
        Shot("end"); yield return Wait(0.3f); Keys(); recording = false;
    }

    // ---------------------------------------------------------------- output
    public string Dump(string file)
    {
        var sb = new StringBuilder("config,fps_mode,sequence,label,frames,avg_fps,min_fps,max_dt_ms,min_margin_player_ring_px,min_margin_fixed_ring_px,char_pct_min,char_pct_max,player_min_edge_px,max_player_offset_px,not_all_in_frame_frames,telegraph_frames,telegraph_all_in_frame\n");
        foreach (var kv in aggs)
        {
            var p = kv.Key.Split('|'); var g = kv.Value; float fpsAvg = (float)(g.dtFrames / System.Math.Max(1e-6, g.sumDt)); if (g.maxDt <= 0) g.maxDt = 1e-6f;
            sb.AppendLine(string.Join(",", p[0], p[1], p[2], p[3], g.frames, fpsAvg.ToString("F1", CultureInfo.InvariantCulture), (1f / g.maxDt).ToString("F1", CultureInfo.InvariantCulture), (g.maxDt * 1000f).ToString("F1", CultureInfo.InvariantCulture),
                g.minMarginPlayer.ToString("F0"), g.minMarginFixed.ToString("F0"), g.minChar.ToString("F2", CultureInfo.InvariantCulture), g.maxChar.ToString("F2", CultureInfo.InvariantCulture), g.minPlayerEdge.ToString("F0"), g.maxOffset.ToString("F0"), g.notAllInFrame, g.telFrames, g.telInFrame));
        }
        File.WriteAllText(file, sb.ToString()); File.WriteAllText(file.Replace(".csv", "_perframe.csv"), pfl.ToString()); return file;
    }
    public void Clear() { aggs.Clear(); }
}
