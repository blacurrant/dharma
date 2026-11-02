using System.Reflection;
using UnityEditor;
using UnityEngine;

/// Editor-only helper to put the art-test scene into a deterministic combat pose for screenshots.
public static class ArtTestHarness
{
    // Same gameplay spawn every time: player at PlayerSpawn (0,0,0), enemy engaged 2.0 m away in +Z, windup frozen at `progress`.
    public static string Stage(float size, float biasX, float biasZ, float enemyWeight, float progress, float enemyDist = 2.0f)
    {
        if (!EditorApplication.isPlaying) return "not playing";
        var enc = Object.FindFirstObjectByType<ArenaEncounter>(); if (enc != null) enc.Restart(); // full HP, same spawn every time
        var cam = Camera.main; cam.orthographicSize = size;
        var focus = Object.FindFirstObjectByType<ArtTestCameraFocus>();
        focus.worldBias = new Vector3(biasX, 0f, biasZ); focus.enemyWeight = enemyWeight;

        var player = GameObject.Find("Player"); var enemyGo = GameObject.Find("ArenaEnemy");
        var dummy = enemyGo.GetComponent<TrainingDummy>();
        dummy.enabled = false; // freeze AI so the pose is identical in every shot
        var pcc = player.GetComponent<CharacterController>(); var ecc = enemyGo.GetComponent<CharacterController>();
        pcc.enabled = false; ecc.enabled = false;
        player.transform.position = new Vector3(0f, 0.02f, 0f);
        enemyGo.transform.position = new Vector3(0f, 0.0f, enemyDist);
        enemyGo.transform.rotation = Quaternion.LookRotation(Vector3.back);
        pcc.enabled = true; ecc.enabled = true;

        var t = typeof(TrainingDummy);
        var begin = t.GetMethod("BeginTelegraph", BindingFlags.NonPublic | BindingFlags.Instance);
        var rem = t.GetField("_windupRemaining", BindingFlags.NonPublic | BindingFlags.Instance);
        if (progress >= 0f)
        {
            begin.Invoke(dummy, new object[] { Vector3.back });
            rem.SetValue(dummy, dummy.AttackWindup * (1f - progress));
        }
        // Snap camera + focus.
        var f = cam.GetComponent<IsoCameraFollow>();
        focus.transform.position = player.transform.position + focus.worldBias + (enemyGo.transform.position - player.transform.position) * enemyWeight;
        f.Target = focus.transform; f.Snap();
        return $"staged size={size} bias=({biasX},{biasZ}) w={enemyWeight} progress={progress} playing={EditorApplication.isPlaying}";
    }
}
