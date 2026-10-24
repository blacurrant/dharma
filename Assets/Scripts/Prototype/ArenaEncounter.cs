using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Win/lose flow for the single-enemy arena fight, plus an in-place restart (R) that does not reload the scene.
/// </summary>
public class ArenaEncounter : MonoBehaviour
{
    public enum EncounterState { Fighting, Cleared, Defeated }

    [SerializeField] Health playerHealth;
    [SerializeField] PlayerMotor playerMotor;
    [SerializeField] TrainingDummy enemy;
    [SerializeField] Transform playerSpawn;
    [SerializeField] Transform enemySpawn;

    Health _enemyHealth;
    Vector3 _fallbackPlayerPosition;
    Quaternion _fallbackPlayerRotation;
    Vector3 _fallbackEnemyPosition;
    Quaternion _fallbackEnemyRotation;
    float _stateChangedAt;
    float _startedAt;

    public EncounterState State { get; private set; } = EncounterState.Fighting;
    public int RestartCount { get; private set; }
    public float ElapsedSinceStateChange => Time.time - _stateChangedAt;
    public float FightDuration => (State == EncounterState.Fighting ? Time.time : _stateChangedAt) - _startedAt;

    void Awake()
    {
        if (playerMotor == null)
            playerMotor = FindAnyObjectByType<PlayerMotor>();
        if (playerHealth == null && playerMotor != null)
            playerHealth = playerMotor.GetComponent<Health>();
        if (enemy == null)
            enemy = FindAnyObjectByType<TrainingDummy>();
        if (enemy != null)
            _enemyHealth = enemy.GetComponent<Health>();

        if (playerMotor != null)
            playerMotor.transform.GetPositionAndRotation(out _fallbackPlayerPosition, out _fallbackPlayerRotation);
        if (enemy != null)
            enemy.transform.GetPositionAndRotation(out _fallbackEnemyPosition, out _fallbackEnemyRotation);
    }

    void OnEnable()
    {
        if (playerHealth != null)
            playerHealth.Died += OnPlayerDied;
        if (_enemyHealth != null)
            _enemyHealth.Died += OnEnemyDied;
    }

    void OnDisable()
    {
        if (playerHealth != null)
            playerHealth.Died -= OnPlayerDied;
        if (_enemyHealth != null)
            _enemyHealth.Died -= OnEnemyDied;
    }

    void Start()
    {
        _startedAt = _stateChangedAt = Time.time;
    }

    void Update()
    {
        Keyboard keyboard = Keyboard.current;
        if (keyboard != null && keyboard.rKey.wasPressedThisFrame)
            Restart();
    }

    public void Restart()
    {
        FxLifetime.ClearAll();

        if (playerHealth != null)
            playerHealth.Revive();
        if (playerMotor != null)
        {
            Vector3 position = playerSpawn != null ? playerSpawn.position : _fallbackPlayerPosition;
            Quaternion rotation = playerSpawn != null ? playerSpawn.rotation : _fallbackPlayerRotation;
            playerMotor.TeleportTo(position, rotation);
        }
        if (enemy != null)
        {
            Vector3 position = enemySpawn != null ? enemySpawn.position : _fallbackEnemyPosition;
            Quaternion rotation = enemySpawn != null ? enemySpawn.rotation : _fallbackEnemyRotation;
            enemy.ResetEnemy(position, rotation);
        }

        Camera main = Camera.main;
        IsoCameraFollow follow = main != null ? main.GetComponent<IsoCameraFollow>() : null;
        if (follow != null)
            follow.Snap();

        RestartCount++;
        _startedAt = Time.time;
        SetState(EncounterState.Fighting);
    }

    void OnPlayerDied()
    {
        if (State == EncounterState.Fighting)
            SetState(EncounterState.Defeated);
    }

    void OnEnemyDied()
    {
        if (State == EncounterState.Fighting)
            SetState(EncounterState.Cleared);
    }

    void SetState(EncounterState state)
    {
        State = state;
        _stateChangedAt = Time.time;
    }
}
