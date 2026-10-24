using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Placeholder combat effects built from runtime geometry (no external assets).
/// Uses the always-included Sprites/Default shader: unlit, alpha-blended, double-sided.
/// </summary>
public static class CombatFx
{
    static Shader _shader;
    static readonly Dictionary<int, Mesh> WedgeMeshes = new Dictionary<int, Mesh>();

    public static Material CreateMaterial(Color color)
    {
        if (_shader == null)
            _shader = Shader.Find("Sprites/Default");
        if (_shader == null)
            _shader = Shader.Find("Universal Render Pipeline/Unlit");
        var material = new Material(_shader);
        material.color = color;
        return material;
    }

    /// <summary>Flat pie slice on the XZ plane, radius 1, pointing along +Z.</summary>
    public static Mesh GetWedgeMesh(float halfAngleDegrees)
    {
        int key = Mathf.RoundToInt(halfAngleDegrees * 10f);
        if (WedgeMeshes.TryGetValue(key, out Mesh cached) && cached != null)
            return cached;

        const int segments = 28;
        var vertices = new Vector3[segments + 2];
        var normals = new Vector3[segments + 2];
        var triangles = new int[segments * 3];
        vertices[0] = Vector3.zero;
        for (int i = 0; i <= segments; i++)
        {
            float angle = Mathf.Lerp(-halfAngleDegrees, halfAngleDegrees, i / (float)segments) * Mathf.Deg2Rad;
            vertices[i + 1] = new Vector3(Mathf.Sin(angle), 0f, Mathf.Cos(angle));
        }
        for (int i = 0; i < normals.Length; i++)
            normals[i] = Vector3.up;
        for (int i = 0; i < segments; i++)
        {
            triangles[i * 3] = 0;
            triangles[i * 3 + 1] = i + 1;
            triangles[i * 3 + 2] = i + 2;
        }

        var mesh = new Mesh { name = "Wedge_" + key };
        mesh.vertices = vertices;
        mesh.normals = normals;
        mesh.triangles = triangles;
        mesh.RecalculateBounds();
        WedgeMeshes[key] = mesh;
        return mesh;
    }

    public static Transform CreateWedge(string name, Transform parent, float range, float halfAngleDegrees, Color color, float height)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = new Vector3(0f, height, 0f);
        go.transform.localRotation = Quaternion.identity;
        go.transform.localScale = new Vector3(range, 1f, range);
        go.AddComponent<MeshFilter>().sharedMesh = GetWedgeMesh(halfAngleDegrees);
        var renderer = go.AddComponent<MeshRenderer>();
        renderer.sharedMaterial = CreateMaterial(color);
        renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        return go.transform;
    }

    public static GameObject CreatePrimitive(PrimitiveType type, string name, Color color)
    {
        GameObject go = GameObject.CreatePrimitive(type);
        go.name = name;
        Collider collider = go.GetComponent<Collider>();
        if (collider != null)
            Object.DestroyImmediate(collider);
        var renderer = go.GetComponent<Renderer>();
        renderer.sharedMaterial = CreateMaterial(color);
        renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        return go;
    }

    public static void SetColor(Transform effect, Color color)
    {
        if (effect == null)
            return;
        var renderer = effect.GetComponent<Renderer>();
        if (renderer != null && renderer.sharedMaterial != null)
            renderer.sharedMaterial.color = color;
    }

    /// <summary>Ground-level pie slice that fades out; shows the exact area a swing/strike covers.</summary>
    public static void SpawnWedgeFlash(Vector3 origin, Vector3 direction, float range, float halfAngleDegrees, Color color, float duration)
    {
        direction.y = 0f;
        if (direction.sqrMagnitude < 0.0001f)
            direction = Vector3.forward;
        Transform wedge = CreateWedge("FX_Wedge", null, range, halfAngleDegrees, color, 0f);
        wedge.SetPositionAndRotation(origin, Quaternion.LookRotation(direction.normalized, Vector3.up));
        wedge.gameObject.AddComponent<FxLifetime>().Init(duration, 0.9f, 1f);
    }

    /// <summary>Expanding, fading sphere used as hit confirmation.</summary>
    public static void SpawnBurst(Vector3 position, Color color, float size, float duration)
    {
        GameObject burst = CreatePrimitive(PrimitiveType.Sphere, "FX_Burst", color);
        burst.transform.position = position;
        burst.transform.localScale = Vector3.one * size;
        burst.AddComponent<FxLifetime>().Init(duration, 0.5f, 1.8f);
    }
}

/// <summary>Fades and scales a transient effect, then destroys it and its material.</summary>
public class FxLifetime : MonoBehaviour
{
    static readonly List<FxLifetime> Active = new List<FxLifetime>();

    float _duration;
    float _startedAt;
    float _scaleFrom;
    float _scaleTo;
    Vector3 _baseScale;
    Color _baseColor;
    Material _material;

    public void Init(float duration, float scaleFrom, float scaleTo)
    {
        _duration = Mathf.Max(0.01f, duration);
        _startedAt = Time.time;
        _scaleFrom = scaleFrom;
        _scaleTo = scaleTo;
        _baseScale = transform.localScale;
        var renderer = GetComponent<Renderer>();
        _material = renderer != null ? renderer.sharedMaterial : null;
        _baseColor = _material != null ? _material.color : Color.white;
        Active.Add(this);
        Apply(0f);
    }

    void Update()
    {
        float t = (Time.time - _startedAt) / _duration;
        if (t >= 1f)
        {
            Destroy(gameObject);
            return;
        }
        Apply(t);
    }

    void Apply(float t)
    {
        transform.localScale = _baseScale * Mathf.Lerp(_scaleFrom, _scaleTo, 1f - (1f - t) * (1f - t));
        if (_material != null)
        {
            Color c = _baseColor;
            c.a = _baseColor.a * (1f - t);
            _material.color = c;
        }
    }

    void OnDestroy()
    {
        Active.Remove(this);
        if (_material != null)
            Destroy(_material);
    }

    public static void ClearAll()
    {
        for (int i = Active.Count - 1; i >= 0; i--)
        {
            if (Active[i] != null)
                Destroy(Active[i].gameObject);
        }
        Active.Clear();
    }
}
