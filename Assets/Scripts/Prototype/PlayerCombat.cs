using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Melee swing. Every swing - whether triggered by a press, a hold or a direct PerformAttack() call -
/// goes through the same gate: attack cooldown, then a flat-plane range + facing-cone test per target.
/// </summary>
[DefaultExecutionOrder(10)] // after PlayerMotor so the swing uses this frame's facing
public class PlayerCombat : MonoBehaviour
{
    [SerializeField] InputActionAsset actions;

    [Header("Reach (measured horizontally, player pivot -> target pivot)")]
    [SerializeField] float attackRange = 1.8f;
    [SerializeField, Range(0f, 90f)] float attackHalfAngle = 58f;
    [Tooltip("Extra radius used only to gather candidate colliders; never extends the real reach.")]
    [SerializeField] float targetPadding = 0.75f;

    [Header("Timing")]
    [SerializeField] float attackCooldown = 0.35f;
    [Tooltip("ON: holding the attack button swings again every time the cooldown ends (deliberate auto-repeat). OFF: one swing per press.")]
    [SerializeField] bool holdToRepeat = true;

    [Header("Damage")]
    [SerializeField] float damage = 25f;
    [SerializeField] float hitKnockback = 4.5f;

    [Header("Feedback")]
    [SerializeField] float slashDuration = 0.18f;
    [SerializeField] Color slashColor = new Color(1f, 0.66f, 0.16f);
    [SerializeField] Color hitSparkColor = new Color(1f, 0.95f, 0.6f);

    InputActionMap _playerMap;
    InputAction _attack;
    Health _self;
    PlayerMotor _motor;
    float _readyAt;
    float _slashStartedAt = -10f;
    bool _wasHeld;
    Vector3 _slashFacing = Vector3.forward;
    Transform _blade;
    Material _bladeMaterial;
    readonly HashSet<Health> _alreadyHit = new HashSet<Health>();

    public bool HoldToRepeat => holdToRepeat;
    public float AttackRange => attackRange;
    public float AttackHalfAngle => attackHalfAngle;
    public float AttackCooldownDuration => attackCooldown;
    public bool IsAttackReady => Time.time >= _readyAt;
    public float AttackCooldownRemaining => Mathf.Max(0f, _readyAt - Time.time);
    public int LastHitCount { get; private set; }
    public int SuccessfulSwings { get; private set; }
    public int TotalHits { get; private set; }
    public float LastAttackTime { get; private set; }
    public Vector3 LastAttackFacing { get; private set; } = Vector3.forward;

    void Awake()
    {
        _self = GetComponent<Health>();
        _motor = GetComponent<PlayerMotor>();
    }

    void OnEnable()
    {
        ResolveActions();
        _playerMap?.Enable();
    }

    void OnDestroy()
    {
        if (_blade != null)
            Destroy(_blade.gameObject);
        if (_bladeMaterial != null)
            Destroy(_bladeMaterial);
    }

    void Start()
    {
        if (_attack == null)
            ResolveActions();
    }

    void Update()
    {
        if (_attack == null)
            ResolveActions();
        UpdateBlade();

        bool held = PrototypeInput.IsHeld(_attack);
        bool pressedThisFrame = held && !_wasHeld;
        _wasHeld = held;
        if (_self != null && _self.IsDead)
            return;

        bool wantsSwing = holdToRepeat ? held : pressedThisFrame;
        if (wantsSwing && IsAttackReady)
            PerformAttack();
    }

    /// <summary>Starts one swing if the cooldown allows it. Returns false (and does nothing) otherwise.</summary>
    public bool PerformAttack()
    {
        if (!IsAttackReady || (_self != null && _self.IsDead))
            return false;

        _readyAt = Time.time + attackCooldown;
        LastAttackTime = Time.time;
        LastHitCount = 0;
        SuccessfulSwings++;

        Vector3 facing = GetFacing();
        LastAttackFacing = facing;
        Vector3 origin = transform.position + Vector3.up;
        float minimumFacingDot = Mathf.Cos(attackHalfAngle * Mathf.Deg2Rad);

        Collider[] candidates = Physics.OverlapSphere(origin, attackRange + targetPadding, ~0, QueryTriggerInteraction.Ignore);
        _alreadyHit.Clear();
        for (int i = 0; i < candidates.Length; i++)
        {
            Health target = candidates[i].GetComponentInParent<Health>();
            if (target == null || target == _self || target.IsDead || !_alreadyHit.Add(target))
                continue;

            Vector3 toTarget = target.transform.position - transform.position;
            toTarget.y = 0f;
            float distance = toTarget.magnitude;
            Vector3 direction = distance > 0.0001f ? toTarget / distance : facing;
            if (distance > attackRange)
                continue;
            if (distance > 0.0001f && Vector3.Dot(facing, direction) < minimumFacingDot)
                continue;
            if (!HasLineOfSight(origin, target, distance))
                continue;

            if (!target.TakeDamage(damage))
                continue;

            LastHitCount++;
            TotalHits++;
            TrainingDummy enemy = target.GetComponentInParent<TrainingDummy>();
            if (enemy != null)
                enemy.ApplyHitReaction(direction, hitKnockback);
            // Hit confirmation: a spark on the side of the target that faces the player.
            CombatFx.SpawnBurst(target.transform.position + Vector3.up * 1.1f - direction * 0.35f, hitSparkColor, 0.7f, 0.2f);
        }

        StartSlashEffect(facing);
        return true;
    }

    Vector3 GetFacing()
    {
        Vector3 facing = _motor != null ? _motor.Facing : transform.forward;
        facing.y = 0f;
        return facing.sqrMagnitude > 0.0001f ? facing.normalized : transform.forward;
    }

    bool HasLineOfSight(Vector3 origin, Health target, float distance)
    {
        Vector3 toTarget = target.transform.position + Vector3.up - origin;
        toTarget.y = 0f;
        if (toTarget.sqrMagnitude < 0.0001f)
            return true;
        if (!Physics.Raycast(origin, toTarget.normalized, out RaycastHit hit, distance, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
            return true;
        return hit.transform == target.transform || hit.transform.IsChildOf(target.transform);
    }

    // ---- feedback -------------------------------------------------------------------------------

    void StartSlashEffect(Vector3 facing)
    {
        _slashFacing = facing;
        _slashStartedAt = Time.time;

        // Ground wedge = the exact area this swing tests.
        Color area = slashColor;
        area.a = 0.38f;
        CombatFx.SpawnWedgeFlash(transform.position + Vector3.up * 0.06f, facing, attackRange, attackHalfAngle, area, slashDuration * 1.4f);

        // Bright blade sweeping across that area.
        if (_blade == null)
        {
            GameObject blade = CombatFx.CreatePrimitive(PrimitiveType.Cube, "AttackSlashEffect", slashColor);
            _blade = blade.transform;
            _bladeMaterial = blade.GetComponent<Renderer>().sharedMaterial;
        }
        _blade.gameObject.SetActive(true);
        UpdateBlade();
    }

    void UpdateBlade()
    {
        if (_blade == null)
            return;
        float t = slashDuration <= 0f ? 1f : (Time.time - _slashStartedAt) / slashDuration;
        if (t >= 1f)
        {
            _blade.gameObject.SetActive(false);
            return;
        }

        const float inner = 0.35f;
        float length = Mathf.Max(0.1f, attackRange - inner);
        Vector3 direction = Quaternion.AngleAxis(Mathf.Lerp(-attackHalfAngle, attackHalfAngle, t), Vector3.up) * _slashFacing;
        Vector3 origin = transform.position + Vector3.up * 0.9f;
        _blade.SetPositionAndRotation(origin + direction * (inner + length * 0.5f), Quaternion.LookRotation(direction, Vector3.up));
        _blade.localScale = new Vector3(0.14f, 0.1f, length);
        if (_bladeMaterial != null)
        {
            Color c = slashColor;
            c.a = Mathf.Clamp01(1.4f - t * 1.4f);
            _bladeMaterial.color = c;
        }
    }

    void ResolveActions()
    {
        var playerInput = GetComponent<PlayerInput>();
        InputActionAsset asset = playerInput != null && playerInput.actions != null
            ? playerInput.actions
            : (actions != null ? actions : InputSystem.actions);
        if (asset == null)
        {
            Debug.LogError("PlayerCombat: no InputActionAsset assigned and InputSystem.actions is null.");
            return;
        }
        _playerMap = asset.FindActionMap("Player", true);
        _playerMap.bindingMask = null;
        _attack = _playerMap.FindAction("Attack", true);
    }

    void OnDrawGizmosSelected()
    {
        Vector3 facing = _motor != null ? _motor.Facing : transform.forward;
        Vector3 origin = transform.position + Vector3.up;
        Gizmos.color = new Color(1f, 0.9f, 0.2f, 0.45f);
        Gizmos.DrawWireSphere(origin, attackRange);
        Gizmos.color = new Color(1f, 0.4f, 0.12f, 0.8f);
        Gizmos.DrawRay(origin, Quaternion.AngleAxis(attackHalfAngle, Vector3.up) * facing * attackRange);
        Gizmos.DrawRay(origin, Quaternion.AngleAxis(-attackHalfAngle, Vector3.up) * facing * attackRange);
    }
}
