// Iteration 3: art-test COPIES of the Player/Enemy Paladin materials (originals untouched) for the character-separation tests.
using UnityEditor;
using UnityEngine;
public static class VF3Builder
{
    const string Root = "Assets/ArtTest/VisualFoundation/Materials/";
    static readonly string[] Src = { "Assets/Characters/Player/Materials/Paladin_MAT.mat", "Assets/Characters/Enemy/Materials/Paladin_Enemy_MAT.mat" };
    static readonly string[] Tag = { "Player", "Enemy" };
    public static string Make()
    {
        var sb = new System.Text.StringBuilder(); var rimShader = Shader.Find("VF/CharacterLitRim"); if (rimShader == null) return "rim shader missing";
        for (int i = 0; i < 2; i++)
        {
            var src = AssetDatabase.LoadAssetAtPath<Material>(Src[i]);
            foreach (var (name, lift, rim) in new[] { ("lift12", 1.2f, 0f), ("lift14", 1.4f, 0f), ("rimA", 1f, 0.8f), ("rimB", 1f, 1.6f), ("rimC", 1f, 0.4f), ("combo12A", 1.2f, 0.8f), ("combo12C", 1.2f, 0.4f), ("combo14C", 1.4f, 0.4f) })
            {
                string p = Root + "VF3_" + Tag[i] + "_" + name + ".mat"; AssetDatabase.DeleteAsset(p);
                var m = new Material(src); m.name = "VF3_" + Tag[i] + "_" + name;
                if (rim > 0f) { m.shader = rimShader; m.SetColor("_VFRimColor", new Color(1.0f, 0.72f, 0.45f, 1f)); m.SetFloat("_VFRimPower", 3f); m.SetFloat("_VFRimStrength", rim); }
                var bc = src.GetColor("_BaseColor"); m.SetColor("_BaseColor", new Color(bc.r * lift, bc.g * lift, bc.b * lift, bc.a));
                AssetDatabase.CreateAsset(m, p); sb.AppendLine(p + " shader=" + m.shader.name + " base=" + m.GetColor("_BaseColor") + " keywords=" + string.Join(",", m.shaderKeywords));
            }
        }
        AssetDatabase.SaveAssets(); return sb.ToString() + ShaderInfo(rimShader);
    }
    // Assign the named copy set to the actor instances in the VF scene (SkinnedMeshRenderers only); "orig" restores the original shared materials. Scene-only change.
    public static string AssignScene(string set)
    {
        var sc = UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene(); if (sc.path != "Assets/Scenes/ArtTest_VisualFoundation.unity") return "WRONG SCENE " + sc.path;
        var sb = new System.Text.StringBuilder();
        for (int i = 0; i < 2; i++)
        {
            var g = GameObject.Find(i == 0 ? "Player" : "ArenaEnemy");
            var m = set == "orig" ? AssetDatabase.LoadAssetAtPath<Material>(Src[i]) : AssetDatabase.LoadAssetAtPath<Material>(Root + "VF3_" + Tag[i] + "_" + set + ".mat");
            foreach (var r in g.GetComponentsInChildren<SkinnedMeshRenderer>(true)) { r.sharedMaterial = m; sb.AppendLine(g.name + "/" + r.name + " -> " + AssetDatabase.GetAssetPath(m)); }
        }
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(sc); UnityEditor.SceneManagement.EditorSceneManager.SaveScene(sc); return sb.ToString();
    }
    static string ShaderInfo(Shader s) { var sb = new System.Text.StringBuilder(); sb.AppendLine("rim shader errors=" + ShaderUtil.GetShaderMessageCount(s)); for (int i = 0; i < ShaderUtil.GetShaderMessageCount(s); i++) { var m = ShaderUtil.GetShaderMessages(s)[i]; sb.AppendLine("  " + m.severity + " " + m.message + " line " + m.line); } return sb.ToString(); }
}
