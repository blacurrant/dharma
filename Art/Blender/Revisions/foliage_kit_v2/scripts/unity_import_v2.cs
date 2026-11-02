// script run --file ... --entry FoliageV2.Import   (kept outside Assets/ so it can never block the project compile)
using UnityEngine; using UnityEditor; using System.Linq;
public static class FoliageV2 {
  const string M = "Assets/ArtTest/VisualFoundation/Art2/";
  static readonly string[] Names = {"Shrub_A","Shrub_B","Vine_A","Vine_B","Tuft_A","Tuft_B"};
  public static string Import() {
    AssetDatabase.Refresh();
    var tp = M+"Textures/ENV_Temple_Foliage2_BaseColor.png";
    var ti = (TextureImporter)AssetImporter.GetAtPath(tp);
    ti.sRGBTexture = true; ti.wrapMode = TextureWrapMode.Repeat; ti.anisoLevel = 4; ti.mipmapEnabled = true; ti.alphaSource = TextureImporterAlphaSource.None; ti.SaveAndReimport();
    var mp = M+"Materials/MI_Temple_Foliage2.mat";
    var mat = AssetDatabase.LoadAssetAtPath<Material>(mp);
    if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, mp); }
    mat.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(tp)); mat.SetColor("_BaseColor", Color.white);
    mat.SetFloat("_Cull", 0f); mat.SetFloat("_Smoothness", 0.06f); mat.SetFloat("_Metallic", 0f); mat.SetFloat("_Surface", 0f); mat.SetFloat("_AlphaClip", 0f);
    mat.DisableKeyword("_ALPHATEST_ON"); mat.enableInstancing = true; EditorUtility.SetDirty(mat);
    var sb = new System.Text.StringBuilder();
    foreach (var n in Names) {
      var p = M+"Models/ENV_Temple_Foliage_"+n+"_v2.fbx";
      var mi = (ModelImporter)AssetImporter.GetAtPath(p);
      mi.importNormals = ModelImporterNormals.Import; mi.importTangents = ModelImporterTangents.None; mi.importBlendShapes = false; mi.importCameras = false; mi.importLights = false;
      mi.meshCompression = ModelImporterMeshCompression.Off; mi.isReadable = false; mi.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
      foreach (var o in AssetDatabase.LoadAllAssetsAtPath(p).OfType<Material>()) mi.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), o.name), mat);
      mi.SaveAndReimport();
    }
    AssetDatabase.SaveAssets();
    foreach (var n in Names) {
      var go = AssetDatabase.LoadAssetAtPath<GameObject>(M+"Models/ENV_Temple_Foliage_"+n+"_v2.fbx");
      var mf = go.GetComponentInChildren<MeshFilter>(); var mr = go.GetComponentInChildren<MeshRenderer>();
      sb.AppendLine(n+" tris="+(mf.sharedMesh.triangles.Length/3)+" bounds="+mf.sharedMesh.bounds.min.ToString("F2")+".."+mf.sharedMesh.bounds.max.ToString("F2")+" mat="+(mr.sharedMaterial!=null?mr.sharedMaterial.name:"NULL")+" normals="+(mf.sharedMesh.normals.Length)+" rot="+go.transform.localEulerAngles+" renderers="+go.GetComponentsInChildren<MeshRenderer>().Length);
    }
    return sb.ToString();
  }
}
