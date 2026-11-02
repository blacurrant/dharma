using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

/// Art-test only. Visual-only cyan-teal telegraph (Art Bible 4.3 / Q18) that mirrors the enemy's real windup
/// (position, direction, range, half-angle, progress). TrainingDummy is NOT modified; the original orange
/// telegraph renderers are merely hidden in this scene while this component is enabled.
[DefaultExecutionOrder(60)]
public class ArtTestCyanTelegraphPreview : MonoBehaviour
{
    public TrainingDummy enemy;
    public bool hideOriginalTelegraph = true;
    public Color fillColor = new Color(0x27 / 255f, 0xDC / 255f, 0xD1 / 255f, 1f);   // #27DCD1
    public Color edgeColor = new Color(0x9B / 255f, 0xFF / 255f, 0xF6 / 255f, 1f);   // #9BFFF6
    [Range(0.15f, 0.35f)] public float startAlpha = 0.26f;   // spec: ~22-28 % initially
    [Range(0.25f, 0.7f)] public float endAlpha = 0.46f;      // intensity rises toward the strike
    public float edgeWidth = 0.10f;
    [Range(0f, 0.4f)] public float areaAlpha = 0.10f;        // faint full-area tint so the whole hazard is shown from frame 1

    Transform _root, _fill, _front, _area, _edge;
    Material _fillMat, _areaMat, _edgeMat, _frontMat;
    float _range, _half;
    Renderer[] _orange;

    void Start()
    {
        if (enemy == null) enemy = GetComponent<TrainingDummy>();
        if (enemy == null) { enabled = false; return; }
        _range = enemy.AttackRange;
        var f = typeof(TrainingDummy).GetField("attackHalfAngle", BindingFlags.NonPublic | BindingFlags.Instance);
        _half = f != null ? (float)f.GetValue(enemy) : 58f;

        _fillMat = Mat(fillColor, startAlpha); _areaMat = Mat(fillColor, areaAlpha);
        _edgeMat = Mat(edgeColor, 0.95f); _frontMat = Mat(edgeColor, 0.8f);

        _root = new GameObject("CyanTelegraphPreview").transform;
        _area = Make("Area", Sector(1f, _half, 28), _areaMat, 0.04f);
        _fill = Make("Fill", Sector(1f, _half, 28), _fillMat, 0.05f);
        _edge = Make("Edge", Outline(_range, _half, edgeWidth), _edgeMat, 0.07f);
        _front = Make("Front", Arc(1f, _half, 0.05f), _frontMat, 0.06f);
        _area.localScale = new Vector3(_range, 1f, _range);
        _root.gameObject.SetActive(false);
    }

    Transform Make(string n, Mesh m, Material mat, float y)
    {
        var g = new GameObject(n); g.transform.SetParent(_root, false); g.transform.localPosition = Vector3.up * y;
        g.AddComponent<MeshFilter>().sharedMesh = m;
        var r = g.AddComponent<MeshRenderer>(); r.sharedMaterial = mat;
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
        return g.transform;
    }

    static Material Mat(Color c, float a)
    {
        var m = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
        m.SetFloat("_Surface", 1f); m.SetFloat("_Blend", 0f);
        m.SetOverrideTag("RenderType", "Transparent");
        m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        m.SetInt("_ZWrite", 0); m.SetFloat("_Cull", 0f); m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT"); m.renderQueue = 3100; // two-sided: winding-proof
        m.SetColor("_BaseColor", new Color(c.r, c.g, c.b, a));
        return m;
    }

    static void SetAlpha(Material m, float a) { var c = m.GetColor("_BaseColor"); c.a = a; m.SetColor("_BaseColor", c); }

    void LateUpdate()
    {
        if (enemy == null || _root == null) return;
        bool on = enemy.IsTelegraphing;
        if (hideOriginalTelegraph)
        {
            if (_orange == null || _orange.Length == 0)
            {
                var t = enemy.transform.Find("EnemyAttackTelegraph");
                if (t != null) _orange = t.GetComponentsInChildren<Renderer>(true);
            }
            if (_orange != null) foreach (var r in _orange) if (r != null) r.enabled = false;
        }
        if (_root.gameObject.activeSelf != on) _root.gameObject.SetActive(on);
        if (!on) return;

        float p = enemy.WindupProgress;
        _root.position = enemy.transform.position;
        _root.rotation = Quaternion.LookRotation(enemy.transform.forward, Vector3.up);
        float rad = Mathf.Max(0.02f, _range * p);
        _fill.localScale = new Vector3(rad, 1f, rad);
        _front.localScale = new Vector3(rad, 1f, rad);
        SetAlpha(_fillMat, Mathf.Lerp(startAlpha, endAlpha, p * p));
    }

    void OnDestroy() { if (_root != null) Destroy(_root.gameObject); }

    // ---- meshes ----
    static Mesh Sector(float r, float halfDeg, int n)
    {
        var v = new List<Vector3> { Vector3.zero }; var t = new List<int>();
        for (int i = 0; i <= n; i++) { float a = Mathf.Deg2Rad * Mathf.Lerp(-halfDeg, halfDeg, i / (float)n); v.Add(new Vector3(Mathf.Sin(a) * r, 0, Mathf.Cos(a) * r)); }
        for (int i = 1; i <= n; i++) { t.Add(0); t.Add(i); t.Add(i + 1); }
        var m = new Mesh { name = "CyanSector" }; m.SetVertices(v); m.SetTriangles(t, 0); m.RecalculateNormals(); return m;
    }

    static Mesh Arc(float r, float halfDeg, float w)
    {
        var v = new List<Vector3>(); var t = new List<int>(); const int n = 28;
        for (int i = 0; i <= n; i++)
        {
            float a = Mathf.Deg2Rad * Mathf.Lerp(-halfDeg, halfDeg, i / (float)n);
            v.Add(new Vector3(Mathf.Sin(a) * (r - w), 0, Mathf.Cos(a) * (r - w))); v.Add(new Vector3(Mathf.Sin(a) * r, 0, Mathf.Cos(a) * r));
        }
        for (int i = 0; i < n; i++) { int s = i * 2; t.AddRange(new[] { s, s + 2, s + 1, s + 1, s + 2, s + 3 }); }
        var m = new Mesh { name = "CyanFront" }; m.SetVertices(v); m.SetTriangles(t, 0); m.RecalculateNormals(); return m;
    }

    static Mesh Outline(float r, float halfDeg, float w)
    {
        var v = new List<Vector3>(); var t = new List<int>(); const int n = 28;
        void Strip(Vector3 a, Vector3 b)
        {
            Vector3 d = (b - a).normalized; Vector3 nrm = Vector3.Cross(Vector3.up, d) * (w * 0.5f);
            int s = v.Count; v.Add(a - nrm); v.Add(a + nrm); v.Add(b - nrm); v.Add(b + nrm);
            t.AddRange(new[] { s, s + 2, s + 1, s + 1, s + 2, s + 3 });
        }
        Vector3 P(float deg, float rad) { float a = Mathf.Deg2Rad * deg; return new Vector3(Mathf.Sin(a) * rad, 0, Mathf.Cos(a) * rad); }
        for (int i = 0; i < n; i++) Strip(P(Mathf.Lerp(-halfDeg, halfDeg, i / (float)n), r), P(Mathf.Lerp(-halfDeg, halfDeg, (i + 1) / (float)n), r));
        Strip(Vector3.zero, P(-halfDeg, r)); Strip(Vector3.zero, P(halfDeg, r));
        var m = new Mesh { name = "CyanEdge" }; m.SetVertices(v); m.SetTriangles(t, 0); m.RecalculateNormals(); return m;
    }
}
