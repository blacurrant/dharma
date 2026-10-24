using UnityEngine;

/// <summary>
/// Drives the Protagonist Animator from the existing gameplay state. Read-only with respect to gameplay:
/// it never changes movement, dash, attack or health, it only observes them.
///   Speed          float  horizontal speed / move speed (0..1)        -> Idle / Run
///   RunAnimSpeed   float  horizontal speed / Run-clip ground speed    -> keeps the feet planted
///   Dash           trigger  PlayerMotor.DashCount changed             -> Dash roll
///   Attack         PlayerCombat accepted a swing (SuccessfulSwings)   -> crossfade into Attack
///   Hit            trigger  Health.Damaged                            -> HitReaction
///   Dead           bool     Health.IsDead                             -> Death (cleared again by Revive)
/// </summary>
[DefaultExecutionOrder(20)] // after PlayerMotor and PlayerCombat
public class PlayerAnimationBridge : MonoBehaviour
{
    [SerializeField] Animator animator;
    [SerializeField] PlayerMotor motor;
    [SerializeField] PlayerCombat combat;
    [SerializeField] Health health;

    [Header("Locomotion")]
    [Tooltip("PlayerMotor.moveSpeed. Speed parameter = horizontal speed / this.")]
    [SerializeField] float moveReferenceSpeed = 8f;
    [Tooltip("Measured: planted-foot speed of the Run clip at 1x playback (m/s).")]
    [SerializeField] float runClipGroundSpeed = 3.95f;

    [Header("Action playback")]
    [Tooltip("The Dash clip is a 1.3 s roll; gameplay dash lasts 0.14 s. Playback multiplier for the roll.")]
    [SerializeField] float dashAnimSpeed = 4.5f;
    [Tooltip("Attack clip is 1.0 s with its strike near 0.4 s; gameplay cooldown is 0.35 s.")]
    [SerializeField] float attackAnimSpeed = 2.2f;
    [Tooltip("Seconds of the Attack clip skipped on entry so the visible strike lands with the (instant) hit.")]
    [SerializeField] float attackStartOffset = 0.2f;
    [SerializeField] float attackBlend = 0.05f;
    [SerializeField] float hitAnimSpeed = 2.2f;

    static readonly int SpeedId = Animator.StringToHash("Speed");
    static readonly int RunAnimSpeedId = Animator.StringToHash("RunAnimSpeed");
    static readonly int DashAnimSpeedId = Animator.StringToHash("DashAnimSpeed");
    static readonly int AttackAnimSpeedId = Animator.StringToHash("AttackAnimSpeed");
    static readonly int HitAnimSpeedId = Animator.StringToHash("HitAnimSpeed");
    static readonly int DashId = Animator.StringToHash("Dash");
    static readonly int AttackId = Animator.StringToHash("Attack");
    static readonly int HitId = Animator.StringToHash("Hit");
    static readonly int DeadId = Animator.StringToHash("Dead");
    static readonly int AttackStateId = Animator.StringToHash("Attack");

    int _lastDashCount;
    int _lastSwings;
    bool _wasDead;

    public Animator Animator => animator;

    void Awake()
    {
        if (motor == null) motor = GetComponent<PlayerMotor>();
        if (combat == null) combat = GetComponent<PlayerCombat>();
        if (health == null) health = GetComponent<Health>();
        if (animator == null) animator = GetComponentInChildren<Animator>();
    }

    void OnEnable()
    {
        if (health != null)
            health.Damaged += OnDamaged;
        if (motor != null) _lastDashCount = motor.DashCount;
        if (combat != null) _lastSwings = combat.SuccessfulSwings;
    }

    void OnDisable()
    {
        if (health != null)
            health.Damaged -= OnDamaged;
    }

    void OnDamaged(float amount, float remaining)
    {
        if (animator == null || health.IsDead)
            return; // death owns the Animator once health reaches zero
        animator.SetTrigger(HitId);
    }

    void Update()
    {
        if (animator == null || motor == null || health == null)
            return;

        bool dead = health.IsDead;
        if (dead != _wasDead)
        {
            _wasDead = dead;
            animator.ResetTrigger(DashId);
            animator.ResetTrigger(AttackId);
            animator.ResetTrigger(HitId);
        }
        animator.SetBool(DeadId, dead);

        Vector3 v = motor.Velocity;
        v.y = 0f;
        float speed = dead ? 0f : v.magnitude;
        animator.SetFloat(SpeedId, Mathf.Clamp01(speed / Mathf.Max(0.01f, moveReferenceSpeed)));
        animator.SetFloat(RunAnimSpeedId, speed > 0.5f ? Mathf.Clamp(speed / runClipGroundSpeed, 0.5f, 4f) : 1f);
        animator.SetFloat(DashAnimSpeedId, dashAnimSpeed);
        animator.SetFloat(AttackAnimSpeedId, attackAnimSpeed);
        animator.SetFloat(HitAnimSpeedId, hitAnimSpeed);

        if (dead)
        {
            _lastDashCount = motor.DashCount;
            _lastSwings = combat != null ? combat.SuccessfulSwings : 0;
            return;
        }

        if (motor.DashCount != _lastDashCount)
        {
            _lastDashCount = motor.DashCount;
            animator.SetTrigger(DashId);
        }

        if (combat != null && combat.SuccessfulSwings != _lastSwings)
        {
            _lastSwings = combat.SuccessfulSwings;
            animator.ResetTrigger(AttackId);
            // Every swing PlayerCombat accepts restarts the animation, so holding attack looks like repeated swings.
            animator.CrossFadeInFixedTime(AttackStateId, attackBlend, 0, attackStartOffset);
        }
    }
}
