// Art-test only. Lighting / GI configuration for Assets/Scenes/ArtTest_TempleCourtyard.unity.
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

public static class ArtTestLighting
{
    const string ScenePath = ArtTestCourtyardBuilder.ScenePath;
    const string LightDir = "Assets/ArtTest/Lighting";

    // Warm key / restrained cool fill. Values chosen by A/B captures (see report).
    public static Color KeyColor = new Color(1.00f, 0.89f, 0.74f);
    public static float KeyIntensity = 1.3f;
    public static Vector3 KeyEuler = new Vector3(46f, 318f, 0f);
    public static Color AmbSky = new Color(0.42f, 0.52f, 0.66f);
    public static Color AmbEquator = new Color(0.34f, 0.38f, 0.45f);
    public static Color AmbGround = new Color(0.17f, 0.15f, 0.14f);

    static bool Guard(out Scene s, out string msg)
    {
        s = SceneManager.GetActiveScene(); msg = null;
        if (s.path != ScenePath) { msg = "WRONG SCENE " + s.path; return false; }
        if (EditorApplication.isPlaying) { msg = "playing"; return false; }
        return true;
    }

    public static string ConfigureStatics()
    {
        if (!Guard(out var scene, out var msg)) return msg;
        Directory.CreateDirectory(LightDir);

        // 1. Mortar underlay: the 2 cm tile joints currently show the clear colour (dark lines). Fill them.
        var old = GameObject.Find("Floor_MortarUnderlay"); if (old != null) Object.DestroyImmediate(old);
        var mortar = GameObject.CreatePrimitive(PrimitiveType.Cube); mortar.name = "Floor_MortarUnderlay";
        Object.DestroyImmediate(mortar.GetComponent<BoxCollider>());
        mortar.transform.position = new Vector3(0f, -0.17f, 0f); mortar.transform.localScale = new Vector3(40f, 0.30f, 40f); // top = -0.02
        string mm = LightDir + "/MI_Mortar.mat";
        var mortarMat = AssetDatabase.LoadAssetAtPath<Material>(mm);
        if (mortarMat == null) { mortarMat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mortarMat, mm); }
        mortarMat.SetColor("_BaseColor", new Color(0.46f, 0.40f, 0.32f)); mortarMat.SetFloat("_Smoothness", 0.1f); mortarMat.SetFloat("_Metallic", 0f);
        EditorUtility.SetDirty(mortarMat);
        mortar.GetComponent<MeshRenderer>().sharedMaterial = mortarMat;
        GameObjectUtility.SetStaticEditorFlags(mortar, StaticEditorFlags.ContributeGI | StaticEditorFlags.BatchingStatic | StaticEditorFlags.ReflectionProbeStatic);
        mortar.transform.SetParent(GameObject.Find("Environment_Courtyard").transform, true);

        // 2. Key light: warm, Mixed (baked indirect + realtime direct shadow).
        var lgo = GameObject.Find("Directional Light"); var l = lgo.GetComponent<Light>();
        l.type = LightType.Directional; l.lightmapBakeType = LightmapBakeType.Mixed;
        l.color = KeyColor; l.intensity = KeyIntensity; l.transform.rotation = Quaternion.Euler(KeyEuler);
        l.shadows = LightShadows.Soft; l.shadowStrength = 0.82f; l.shadowBias = 0.04f; l.shadowNormalBias = 0.5f;
        l.bounceIntensity = 1f;

        // 3. Ambient: restrained cool tri-light (also what the bake sees as environment light).
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = AmbSky; RenderSettings.ambientEquatorColor = AmbEquator; RenderSettings.ambientGroundColor = AmbGround;
        RenderSettings.ambientIntensity = 1f;
        RenderSettings.defaultReflectionMode = DefaultReflectionMode.Skybox;
        RenderSettings.reflectionIntensity = 0.6f;

        // 4. Camera: neutral warm-dark background, post-processing on (tonemap + gentle bloom).
        var cam = Camera.main; cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(0.075f, 0.062f, 0.058f);
        var cd = cam.GetComponent<UniversalAdditionalCameraData>(); cd.renderPostProcessing = true;

        // 5. Global volume.
        var vgo = GameObject.Find("ArtTest_Volume"); if (vgo == null) vgo = new GameObject("ArtTest_Volume");
        var vol = vgo.GetComponent<Volume>(); if (vol == null) vol = vgo.AddComponent<Volume>();
        vol.isGlobal = true; vol.priority = 10f;
        string vp = LightDir + "/ArtTest_VolumeProfile.asset";
        AssetDatabase.DeleteAsset(vp); // rebuild so components are real sub-assets
        var prof = AssetDatabase.LoadAssetAtPath<VolumeProfile>(vp);
        if (prof == null) { prof = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(prof, vp); }
        void Ensure<T>(System.Action<T> cfg) where T : VolumeComponent
        { if (!prof.TryGet<T>(out var c) || c == null) { c = prof.Add<T>(true); c.name = typeof(T).Name; AssetDatabase.AddObjectToAsset(c, prof); } cfg(c); EditorUtility.SetDirty(c); }
        Ensure<Tonemapping>(t => { t.active = true; t.mode.overrideState = true; t.mode.value = TonemappingMode.Neutral; });
        Ensure<Bloom>(b => { b.active = true; b.threshold.overrideState = true; b.threshold.value = 1.0f; b.intensity.overrideState = true; b.intensity.value = 0.18f; b.scatter.overrideState = true; b.scatter.value = 0.55f; });
        Ensure<ColorAdjustments>(c => { c.active = true; c.postExposure.overrideState = true; c.postExposure.value = 0f; c.saturation.overrideState = true; c.saturation.value = -12f; c.contrast.overrideState = true; c.contrast.value = 8f; });
        EditorUtility.SetDirty(prof);
        vol.sharedProfile = prof;

        // 6. Light probes for moving actors.
        var pg = GameObject.Find("LightProbes_Courtyard"); if (pg != null) Object.DestroyImmediate(pg);
        pg = new GameObject("LightProbes_Courtyard"); var grp = pg.AddComponent<LightProbeGroup>();
        var pts = new System.Collections.Generic.List<Vector3>();
        for (float x = -18f; x <= 18.01f; x += 4f) for (float z = -18f; z <= 18.01f; z += 4f) { pts.Add(new Vector3(x, 0.8f, z)); pts.Add(new Vector3(x, 2.6f, z)); }
        foreach (var d in new[] { new Vector3(-12f, 1.6f, 12f), new Vector3(-14f, 1.6f, 14f), new Vector3(-10f, 1.6f, 14f), new Vector3(-14f, 1.6f, 10f), new Vector3(-11f, 1.2f, 11f), new Vector3(4f, 1.6f, 17f), new Vector3(4f, 3f, 18f) }) pts.Add(d);
        grp.probePositions = pts.ToArray();

        // 7. Lighting settings asset (assigned to the scene only).
        string lp = LightDir + "/TempleCourtyard_Lighting.lighting";
        var ls = AssetDatabase.LoadAssetAtPath<LightingSettings>(lp);
        if (ls == null) { ls = new LightingSettings(); AssetDatabase.CreateAsset(ls, lp); }
        ls.bakedGI = true; ls.realtimeGI = false; ls.autoGenerate = false;
        ls.mixedBakeMode = MixedLightingMode.IndirectOnly;
        ls.lightmapper = LightingSettings.Lightmapper.ProgressiveGPU;
        ls.directionalityMode = LightmapsMode.NonDirectional;
        ls.lightmapResolution = 12f; ls.lightmapPadding = 4; ls.lightmapMaxSize = 1024;
        ls.lightmapCompression = LightmapCompression.NormalQuality;
        ls.directSampleCount = 32; ls.indirectSampleCount = 256; ls.environmentSampleCount = 128; ls.maxBounces = 2;
        ls.filteringMode = LightingSettings.FilterMode.Auto;
        ls.ao = true; ls.aoMaxDistance = 0.9f; ls.aoExponentIndirect = 1f; ls.aoExponentDirect = 0f;
        ls.albedoBoost = 1f; ls.indirectScale = 1f;
        EditorUtility.SetDirty(ls);
        Lightmapping.lightingSettings = ls;
        Lightmapping.giWorkflowMode = Lightmapping.GIWorkflowMode.OnDemand;

        AssetDatabase.SaveAssets();
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
        return "statics configured; probes=" + pts.Count;
    }

    // Floor-grout fix, camera framing and actor readability lights. Idempotent.
    public static string ApplyFinishing()
    {
        if (!Guard(out var scene, out var msg)) return msg;
        foreach (var g in AssetDatabase.FindAssets("t:Material MI_Temple_Floor", new[] { "Assets/ArtTest/Environment/Materials" }))
        {
            var m = AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(g));
            m.SetFloat("_OcclusionStrength", 0.35f); m.SetFloat("_BumpScale", 0.6f); EditorUtility.SetDirty(m);
        }
        // Actor readability lights (realtime, no shadows, not baked).
        AddActorLight("Player", new Color(1f, 0.93f, 0.82f), 2.2f);
        AddActorLight("ArenaEnemy", new Color(1f, 0.80f, 0.66f), 1.4f);

        // Recommended camera: ortho 9, offset unchanged (12,18,-12), focus bias toward the dais + light enemy pull.
        var cam = Camera.main; var follow = cam.GetComponent<IsoCameraFollow>();
        var so = new SerializedObject(follow);
        so.FindProperty("orthographicSize").floatValue = 9f;
        so.FindProperty("offset").vector3Value = new Vector3(12f, 18f, -12f);
        var focus = Object.FindFirstObjectByType<ArtTestCameraFocus>();
        so.FindProperty("target").objectReferenceValue = focus.transform;
        so.ApplyModifiedPropertiesWithoutUndo();
        cam.orthographicSize = 9f;
        focus.worldBias = new Vector3(-1f, 0f, 1f); focus.enemyWeight = 0.35f; focus.maxEnemyPull = 3f;
        EditorUtility.SetDirty(focus);
        AssetDatabase.SaveAssets();
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
        return "finishing applied";
    }

    static void AddActorLight(string parentName, Color c, float intensity)
    {
        var p = GameObject.Find(parentName); if (p == null) return;
        var t = p.transform.Find("ActorLight"); GameObject lg = t != null ? t.gameObject : null;
        if (lg == null) { lg = new GameObject("ActorLight"); lg.transform.SetParent(p.transform, false); }
        lg.transform.localPosition = new Vector3(0.4f, 2.8f, -0.6f);
        var l = lg.GetComponent<Light>(); if (l == null) l = lg.AddComponent<Light>();
        l.type = LightType.Point; l.color = c; l.intensity = intensity; l.range = 5.5f; l.shadows = LightShadows.None; l.lightmapBakeType = LightmapBakeType.Realtime;
    }
}
