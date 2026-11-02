using UnityEngine;

/// Art-test only. Moves a focus point that IsoCameraFollow tracks, so the (unchanged) gameplay camera
/// can be framed slightly toward the enemy / architecture without editing the gameplay script.
[DefaultExecutionOrder(0)]
public class ArtTestCameraFocus : MonoBehaviour
{
    [Tooltip("Constant world-space shift of the focus point (e.g. toward the dais).")]
    public Vector3 worldBias = Vector3.zero;
    [Range(0f, 1f)] public float enemyWeight = 0.35f;
    public float maxEnemyPull = 3f;
    public float smooth = 6f;

    Transform _player, _enemy;
    TrainingDummy _dummy;
    IsoCameraFollow _cam;
    bool _initialised;

    void LateUpdate()
    {
        if (_player == null) { var p = GameObject.Find("Player"); _player = p != null ? p.transform : null; }
        if (_enemy == null) { var e = GameObject.Find("ArenaEnemy"); _enemy = e != null ? e.transform : null; _dummy = e != null ? e.GetComponent<TrainingDummy>() : null; }
        if (_cam == null && Camera.main != null) _cam = Camera.main.GetComponent<IsoCameraFollow>();
        if (_player == null || _cam == null) return;

        Vector3 desired = _player.position;
        if (_enemy != null && (_dummy == null || !_dummy.IsDead))
        {
            Vector3 toEnemy = _enemy.position - _player.position; toEnemy.y = 0f;
            desired += Vector3.ClampMagnitude(toEnemy * enemyWeight, maxEnemyPull);
        }
        desired += worldBias;
        desired.y = 0f;

        if (!_initialised) { transform.position = desired; _initialised = true; }
        else transform.position = Vector3.Lerp(transform.position, desired, 1f - Mathf.Exp(-smooth * Time.deltaTime));

        if (_cam.Target != transform) { _cam.Target = transform; _cam.Snap(); }
    }
}
