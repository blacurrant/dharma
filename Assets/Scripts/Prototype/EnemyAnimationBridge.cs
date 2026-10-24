using UnityEngine;

/// <summary>
/// Drives the enemy Paladin Animator from TrainingDummy's existing state. It only observes the enemy;
/// chase distance, telegraph, damage, stagger, knockback and death stay entirely in TrainingDummy.
///   Speed          float  signed speed along the enemy's facing (m/s): + chase, - back-pedal
///   LocoAnimSpeed  float  |speed| / clip ground speed -> planted feet
///   Attack         trigger  telegraph started; AttackAnimSpeed scrubs the wind-up so the sword peak lands on the strike
///   Hit            trigger  stagger started (armored wind-up hits do not flinch, matching TrainingDummy)
///   Dead           bool     enemy dead; cleared again by ResetEnemy
/// </summary>
[DefaultExecutionOrder(20)]
public class EnemyAnimationBridge : MonoBehaviour
{
    [SerializeField] Animator animator;
    [SerializeField] TrainingDummy enemy;

    [Header("Locomotion")]
    [Tooltip("Planted-foot speed of the forward Run clip at 1x (m/s), measured on the Paladin.")]
    [SerializeField] float runClipGroundSpeed = 3.95f;
    [Tooltip("Planted-foot speed of the backward run clip at 1x (m/s).")]
    [SerializeField] float backClipGroundSpeed = 3.79f;

    [Header("Attack sync")]
    [Tooltip("Normalized time in the Attack clip where the sword reaches its strike peak.")]
    [SerializeField] float strikePeakNormalized = 0.42f;
    [Tooltip("Playback speed after the strike resolves, to play out the follow-through.")]
    [SerializeField] float followThroughSpeed = 1.5f;
    [SerializeField] float attackClipLength = 1.0f;

    [SerializeField] float hitAnimSpeed = 2.5f;

    static readonly int SpeedId = Animator.StringToHash("Speed");
    static readonly int LocoAnimSpeedId = Animator.StringToHash("LocoAnimSpeed");
    static readonly int AttackAnimSpeedId = Animator.StringToHash("AttackAnimSpeed");
    static readonly int HitAnimSpeedId = Animator.StringToHash("HitAnimSpeed");
    static readonly int AttackId = Animator.StringToHash("Attack");
    static readonly int HitId = Animator.StringToHash("Hit");
    static readonly int DeadId = Animator.StringToHash("Dead");

    Vector3 _lastPosition;
    float _forwardSpeed;
    bool _wasTelegraphing;
    bool _wasStaggered;
    bool _wasDead;

    public Animator Animator => animator;
    public float ForwardSpeed => _forwardSpeed;

    void Awake()
    {
        if (enemy == null) enemy = GetComponent<TrainingDummy>();
        if (animator == null) animator = GetComponentInChildren<Animator>();
        _lastPosition = transform.position;
    }

    void Update()
    {
        if (animator == null || enemy == null)
            return;

        float dt = Time.deltaTime;
        Vector3 delta = transform.position - _lastPosition;
        _lastPosition = transform.position;
        delta.y = 0f;
        if (dt > 1e-5f)
        {
            float raw = Vector3.Dot(delta / dt, transform.forward);
            if (Mathf.Abs(raw) > 30f) raw = 0f; // teleport on restart, not movement
            _forwardSpeed = Mathf.Lerp(_forwardSpeed, raw, 1f - Mathf.Exp(-18f * dt));
        }

        bool dead = enemy.IsDead;
        if (dead != _wasDead)
        {
            _wasDead = dead;
            animator.ResetTrigger(AttackId);
            animator.ResetTrigger(HitId);
            _forwardSpeed = 0f;
        }
        animator.SetBool(DeadId, dead);

        float speed = dead ? 0f : _forwardSpeed;
        animator.SetFloat(SpeedId, speed);
        float ground = speed >= 0f ? runClipGroundSpeed : backClipGroundSpeed;
        animator.SetFloat(LocoAnimSpeedId, Mathf.Clamp(Mathf.Abs(speed) / ground, 0.4f, 3f));
        animator.SetFloat(HitAnimSpeedId, hitAnimSpeed);

        bool telegraphing = enemy.IsTelegraphing;
        if (telegraphing)
        {
            // wind-up phase: reach the clip's strike peak exactly when the telegraph ends and the strike resolves
            animator.SetFloat(AttackAnimSpeedId, strikePeakNormalized * attackClipLength / Mathf.Max(0.05f, enemy.AttackWindup));
            if (!_wasTelegraphing)
                animator.SetTrigger(AttackId);
        }
        else
        {
            animator.SetFloat(AttackAnimSpeedId, followThroughSpeed);
        }
        _wasTelegraphing = telegraphing;

        bool staggered = enemy.IsStaggered && !dead;
        if (staggered && !_wasStaggered)
            animator.SetTrigger(HitId);
        _wasStaggered = staggered;
    }
}
