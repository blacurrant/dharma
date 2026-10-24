using UnityEngine;

/// <summary>
/// The arena enemy (class keeps its original name so existing scene references stay valid).
/// Loop: chase to a combat distance -> telegraph a cone strike (direction locked) -> strike -> recover.
/// The telegraph wedge is the exact area the strike tests, so what you see is what can hit you.
/// </summary>
public class TrainingDummy : MonoBehaviour
{
    [Header("Movement")]
    [SerializeField] float approachSpeed = 3.2f;
    [SerializeField] float preferredRange = 1.65f;
    [SerializeField] float rangeSlack = 0.22f;

    [Header("Attack")]
    [SerializeField] float attackRange = 2.15f;
    [SerializeField, Range(0f, 90f)] float attackHalfAngle = 58f;
    [SerializeField] float attackWindup = 0.78f;
    [SerializeField] float attackCooldown = 1.9f;
    [Tooltip("Time the enemy stands still after a strike (the player's opening).")]
    [SerializeField] float attackRecovery = 0.4f;
    [SerializeField] float attackDamage = 12f;
    [SerializeField] float playerKnockback = 6f;

    [Header("Reaction")]
    [SerializeField] float hitKnockback = 5f;
    [SerializeField] float staggerDuration = 0.2f;
    [Tooltip("ON: hits during the windup still hurt and flash the enemy but do not cancel the strike.")]
    [SerializeField] bool windupArmor = true;
    [SerializeField] Color aliveColor = new Color(0.55f, 0.28f, 0.28f);
    [SerializeField] Color windupColor = new Color(1f, 0.42f, 0.08f);
    [SerializeField] Color flashColor = Color.white;
    [SerializeField] Color deadColor = new Color(0.18f, 0.16f, 0.16f);

    const float FlashDuration = 0.14f;
    const float PunchDuration = 0.16f;
    const float StartDelay = 0.65f;

    CharacterController _controller;
    Health _health;
    Health _targetHealth;
    PlayerMotor _targetMotor;
    Renderer _renderer;
    Material _material;
    Transform _visualRoot;
    Transform _telegraph;
    Transform _telegraphArea;
    Transform _telegraphFill;
    Vector3 _bodyHomePosition;
    Quaternion _bodyHomeRotation = Quaternion.identity;
    Vector3 _bodyHomeScale = Vector3.one;
    Vector3 _attackDirection = Vector3.forward;
    Vector3 _knockbackVelocity;
    float _windupRemaining;
    float _attackReadyAt;
    float _recoverUntil;
    float _staggerUntil;
    float _flashUntil;
    float _punchUntil;
    Color _shownColor;
    bool _dead;

    public bool IsDead => _dead || (_health != null && _health.IsDead);
    public bool IsTelegraphing => !IsDead && _windupRemaining > 0f;
    public float WindupRemaining => Mathf.Max(0f, _windupRemaining);
    public float WindupProgress => IsTelegraphing ? 1f - Mathf.Clamp01(_windupRemaining / attackWindup) : 0f;
    public bool IsStaggered => Time.time < _staggerUntil;
    public bool IsRecovering => Time.time < _recoverUntil;
    public int AttackCount { get; private set; }
    public int HitCount { get; private set; }
    public int DodgedAttackCount { get; private set; }
    public int MissedAttackCount { get; private set; }
    public float LastResolvedAt { get; private set; } = -10f;
    /// <summary>HIT, DODGED (dash i-frames), MISSED (player outside cone/range at strike time) or NONE.</summary>
    public string LastOutcome { get; private set; } = "NONE";
    public float AttackRange => attackRange;
    public float AttackHalfAngle => attackHalfAngle;
    public float AttackWindup => attackWindup;
    public float AttackDamage => attackDamage;
    public Vector3 AttackDirection => _attackDirection;
    public string StateLabel
    {
        get
        {
            if (IsDead) return "DOWN";
            if (IsTelegraphing) return "WINDUP";
            if (IsStaggered) return "STAGGERED";
            if (IsRecovering) return "RECOVERING";
            return "HUNTING";
        }
    }

    void Awake()
    {
        _controller = GetComponent<CharacterController>();
        _health = GetComponent<Health>();
        _visualRoot = transform.Find("Body");
        _renderer = _visualRoot != null ? _visualRoot.GetComponent<Renderer>() : GetComponentInChildren<Renderer>();
        if (_visualRoot != null)
        {
            _bodyHomePosition = _visualRoot.localPosition;
            _bodyHomeRotation = _visualRoot.localRotation;
            _bodyHomeScale = _visualRoot.localScale;
        }
        if (_renderer != null)
        {
            _material = _renderer.material;
            if (_material.HasProperty("_BaseColor"))
                _shownColor = _material.GetColor("_BaseColor");
            else if (_material.HasProperty("_Color"))
                _shownColor = _material.color;
        }
        CreateTelegraphVisual();
    }

    void OnEnable()
    {
        if (_health != null)
        {
            _health.Damaged += OnDamaged;
            _health.Died += OnDied;
        }
    }

    void OnDisable()
    {
        if (_health != null)
        {
            _health.Damaged -= OnDamaged;
            _health.Died -= OnDied;
        }
    }

    void OnDestroy()
    {
        if (_material != null)
            Destroy(_material);
        if (_telegraph != null)
        {
            DestroyMaterial(_telegraphArea);
            DestroyMaterial(_telegraphFill);
        }
    }

    void Start()
    {
        GameObject player = GameObject.Find("Player");
        if (player != null)
        {
            _targetHealth = player.GetComponent<Health>();
            _targetMotor = player.GetComponent<PlayerMotor>();
        }
        _attackReadyAt = Time.time + StartDelay;
    }

    void Update()
    {
        UpdateVisuals();
        if (IsDead)
            return;
        if (_targetHealth == null || _targetHealth.IsDead)
        {
            CancelWindup();
            return;
        }

        if (Time.time < _staggerUntil)
        {
            Move(_knockbackVelocity);
            _knockbackVelocity = Vector3.MoveTowards(_knockbackVelocity, Vector3.zero, 22f * Time.deltaTime);
            return;
        }
        _knockbackVelocity = Vector3.zero;

        if (_windupRemaining > 0f)
        {
            _windupRemaining -= Time.deltaTime;
            if (_windupRemaining <= 0f)
                ResolveAttack();
            return;
        }

        if (Time.time < _recoverUntil)
            return;

        Vector3 toPlayer = _targetHealth.transform.position - transform.position;
        toPlayer.y = 0f;
        float distance = toPlayer.magnitude;
        if (distance <= 0.0001f)
            return;

        Vector3 direction = toPlayer / distance;
        transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), 1f - Mathf.Exp(-12f * Time.deltaTime));

        // Keep a combat distance: close in when far, back off when crowded, hold otherwise.
        Vector3 move = Vector3.zero;
        if (distance > preferredRange + rangeSlack)
            move = direction * approachSpeed;
        else if (distance < preferredRange - rangeSlack)
            move = -direction * (approachSpeed * 0.7f);
        Move(move);

        if (distance <= attackRange && Time.time >= _attackReadyAt)
            BeginTelegraph(direction);
    }

    /// <summary>Called by the player's swing after damage was applied.</summary>
    public void ApplyHitReaction(Vector3 direction, float strength)
    {
        if (IsDead)
            return;

        _punchUntil = Time.time + PunchDuration;
        if (IsTelegraphing && windupArmor)
            return; // armored: hurt and flashing, but the strike is committed

        direction.y = 0f;
        if (direction.sqrMagnitude < 0.0001f)
            direction = -transform.forward;
        _knockbackVelocity = direction.normalized * Mathf.Max(hitKnockback, strength);
        _staggerUntil = Time.time + staggerDuration;
        CancelWindup();
    }

    /// <summary>Puts the enemy back at a spawn point at full health (encounter restart).</summary>
    public void ResetEnemy(Vector3 position, Quaternion rotation)
    {
        CancelWindup();
        if (_controller != null)
            _controller.enabled = false;
        transform.SetPositionAndRotation(position, rotation);
        if (_controller != null)
            _controller.enabled = true;

        _health?.Revive();
        _dead = false;
        _knockbackVelocity = Vector3.zero;
        _staggerUntil = 0f;
        _recoverUntil = 0f;
        _flashUntil = 0f;
        _punchUntil = 0f;
        _attackReadyAt = Time.time + StartDelay;
        AttackCount = HitCount = DodgedAttackCount = MissedAttackCount = 0;
        LastOutcome = "NONE";
        if (_visualRoot != null)
        {
            _visualRoot.localPosition = _bodyHomePosition;
            _visualRoot.localRotation = _bodyHomeRotation;
            _visualRoot.localScale = _bodyHomeScale;
        }
        ApplyColor(aliveColor);
    }

    // ---- attack ---------------------------------------------------------------------------------

    void BeginTelegraph(Vector3 direction)
    {
        _attackDirection = direction.normalized;
        transform.rotation = Quaternion.LookRotation(_attackDirection);
        _windupRemaining = attackWindup;
        if (_telegraph != null)
            _telegraph.gameObject.SetActive(true);
        UpdateTelegraph();
    }

    void CancelWindup()
    {
        _windupRemaining = 0f;
        if (_telegraph != null)
            _telegraph.gameObject.SetActive(false);
    }

    void ResolveAttack()
    {
        CancelWindup();
        _attackReadyAt = Time.time + attackCooldown;
        _recoverUntil = Time.time + attackRecovery;
        AttackCount++;
        LastResolvedAt = Time.time;

        // Show the strike area for a moment so a hit/miss is readable.
        CombatFx.SpawnWedgeFlash(transform.position + Vector3.up * 0.07f, _attackDirection, attackRange, attackHalfAngle, new Color(1f, 0.25f, 0.1f, 0.7f), 0.2f);

        if (_targetHealth == null || _targetHealth.IsDead)
            return;
        Vector3 toPlayer = _targetHealth.transform.position - transform.position;
        toPlayer.y = 0f;
        float distance = toPlayer.magnitude;
        bool inRange = distance <= attackRange;
        bool inCone = distance < 0.0001f || Vector3.Dot(_attackDirection, toPlayer / distance) >= Mathf.Cos(attackHalfAngle * Mathf.Deg2Rad);
        if (!inRange || !inCone)
        {
            MissedAttackCount++;
            LastOutcome = "MISSED";
            return;
        }
        if (_targetMotor != null && _targetMotor.IsInvulnerable)
        {
            DodgedAttackCount++;
            LastOutcome = "DODGED";
            return;
        }

        if (_targetHealth.TakeDamage(attackDamage))
        {
            HitCount++;
            LastOutcome = "HIT";
            if (_targetMotor != null)
                _targetMotor.ApplyKnockback(_attackDirection, playerKnockback, 0.24f);
            CombatFx.SpawnBurst(_targetHealth.transform.position + Vector3.up * 1.1f, new Color(1f, 0.3f, 0.2f, 0.9f), 0.9f, 0.22f);
        }
    }

    void Move(Vector3 horizontalVelocity)
    {
        if (_controller != null && _controller.enabled)
        {
            Vector3 motion = horizontalVelocity;
            motion.y = _controller.isGrounded ? -2f : -20f;
            _controller.Move(motion * Time.deltaTime);
        }
        else
        {
            transform.position += horizontalVelocity * Time.deltaTime;
        }
    }

    // ---- events & visuals -----------------------------------------------------------------------

    void OnDamaged(float amount, float remaining)
    {
        _flashUntil = Time.time + FlashDuration;
    }

    void OnDied()
    {
        _dead = true;
        CancelWindup();
        _knockbackVelocity = Vector3.zero;
        if (_controller != null)
            _controller.enabled = false;
        if (_visualRoot != null)
        {
            // Placeholder death: the capsule topples over and lies on the floor.
            _visualRoot.localScale = _bodyHomeScale;
            _visualRoot.localRotation = Quaternion.Euler(82f, 0f, 28f);
            _visualRoot.localPosition = new Vector3(_bodyHomePosition.x, 0.5f, _bodyHomePosition.z);
        }
        ApplyColor(deadColor);
        CombatFx.SpawnBurst(transform.position + Vector3.up * 1f, new Color(1f, 0.85f, 0.4f, 0.8f), 1.4f, 0.4f);
    }

    void UpdateVisuals()
    {
        if (_material != null && !IsDead)
        {
            Color desired = Time.time < _flashUntil ? flashColor : (IsTelegraphing ? windupColor : aliveColor);
            if (desired != _shownColor)
                ApplyColor(desired);
        }

        if (_visualRoot != null && !IsDead)
        {
            // Hit punch: brief squash so every connecting hit visibly lands.
            float remaining = Mathf.Clamp01((_punchUntil - Time.time) / PunchDuration);
            float squash = Mathf.Sin(remaining * Mathf.PI) * 0.22f;
            _visualRoot.localScale = new Vector3(_bodyHomeScale.x * (1f + squash), _bodyHomeScale.y * (1f - squash), _bodyHomeScale.z * (1f + squash));
        }

        if (IsTelegraphing)
            UpdateTelegraph();
    }

    void UpdateTelegraph()
    {
        if (_telegraphFill == null)
            return;
        float p = WindupProgress;
        _telegraphFill.localScale = new Vector3(attackRange * p, 1f, attackRange * p);
        // Fill brightens as the strike approaches.
        CombatFx.SetColor(_telegraphFill, Color.Lerp(new Color(1f, 0.55f, 0.1f, 0.5f), new Color(1f, 0.1f, 0.05f, 0.85f), p));
    }

    void ApplyColor(Color color)
    {
        if (_material == null)
            return;
        _shownColor = color;
        if (_material.HasProperty("_BaseColor"))
            _material.SetColor("_BaseColor", color);
        if (_material.HasProperty("_Color"))
            _material.color = color;
        if (_material.HasProperty("_EmissionColor"))
        {
            _material.EnableKeyword("_EMISSION");
            _material.SetColor("_EmissionColor", color * 0.22f);
        }
    }

    void CreateTelegraphVisual()
    {
        var root = new GameObject("EnemyAttackTelegraph");
        root.transform.SetParent(transform, false);
        root.transform.localPosition = new Vector3(0f, 0.05f, 0f);
        _telegraph = root.transform;
        // Dim wedge = full strike area; bright wedge grows from the enemy to the edge as the windup completes.
        _telegraphArea = CombatFx.CreateWedge("Area", _telegraph, attackRange, attackHalfAngle, new Color(1f, 0.1f, 0.05f, 0.28f), 0f);
        _telegraphFill = CombatFx.CreateWedge("Fill", _telegraph, attackRange, attackHalfAngle, new Color(1f, 0.5f, 0.1f, 0.5f), 0.015f);
        _telegraphFill.localScale = new Vector3(0.001f, 1f, 0.001f);
        root.SetActive(false);
    }

    static void DestroyMaterial(Transform effect)
    {
        if (effect == null)
            return;
        var renderer = effect.GetComponent<Renderer>();
        if (renderer != null && renderer.sharedMaterial != null)
            Destroy(renderer.sharedMaterial);
    }

    void OnDrawGizmosSelected()
    {
        Gizmos.color = new Color(1f, 0.2f, 0.1f, 0.8f);
        Vector3 origin = transform.position + Vector3.up * 0.1f;
        Gizmos.DrawRay(origin, Quaternion.AngleAxis(attackHalfAngle, Vector3.up) * transform.forward * attackRange);
        Gizmos.DrawRay(origin, Quaternion.AngleAxis(-attackHalfAngle, Vector3.up) * transform.forward * attackRange);
        Gizmos.color = new Color(0.4f, 0.8f, 1f, 0.6f);
        Gizmos.DrawWireSphere(origin, preferredRange);
    }
}
