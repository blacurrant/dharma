using UnityEngine;

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
    [SerializeField] float attackDamage = 12f;
    [SerializeField] float playerKnockback = 6f;
    [Header("Reaction")]
    [SerializeField] float hitKnockback = 5f;
    [SerializeField] float staggerDuration = 0.2f;
    [SerializeField] Color aliveColor = new Color(0.55f, 0.28f, 0.28f);
    [SerializeField] Color windupColor = new Color(1f, 0.42f, 0.08f);
    [SerializeField] Color flashColor = Color.white;
    [SerializeField] Color deadColor = new Color(0.18f, 0.16f, 0.16f);

    CharacterController _controller;
    Health _health;
    Health _targetHealth;
    PlayerMotor _targetMotor;
    Renderer _renderer;
    Material _material;
    Material _warningMaterial;
    Transform _visualRoot;
    Transform _warning;
    Vector3 _attackDirection = Vector3.forward;
    Vector3 _knockbackVelocity;
    float _windupRemaining;
    float _attackReadyAt;
    float _staggerUntil;
    float _flashUntil;
    Color _shownColor;
    bool _dead;

    public bool IsDead => _dead || (_health != null && _health.IsDead);
    public bool IsTelegraphing => !_dead && _windupRemaining > 0f;
    public float WindupRemaining => Mathf.Max(0f, _windupRemaining);
    public bool IsStaggered => Time.time < _staggerUntil;
    public int AttackCount { get; private set; }
    public int HitCount { get; private set; }
    public int DodgedAttackCount { get; private set; }
    public string StateLabel
    {
        get
        {
            if (IsDead) return "DOWN";
            if (IsTelegraphing) return "WINDUP";
            if (IsStaggered) return "STAGGERED";
            return "HUNTING";
        }
    }

    void Awake()
    {
        _controller = GetComponent<CharacterController>();
        _health = GetComponent<Health>();
        _visualRoot = transform.Find("Body");
        _renderer = _visualRoot != null ? _visualRoot.GetComponent<Renderer>() : GetComponentInChildren<Renderer>();
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
        if (_warningMaterial != null)
            Destroy(_warningMaterial);
    }

    void Start()
    {
        GameObject player = GameObject.Find("Player");
        if (player != null)
        {
            _targetHealth = player.GetComponent<Health>();
            _targetMotor = player.GetComponent<PlayerMotor>();
        }
        _attackReadyAt = Time.time + 0.65f;
        if (_warning != null)
            _warning.gameObject.SetActive(false);
    }

    void Update()
    {
        UpdateVisualColor();
        if (IsDead)
            return;
        if (_targetHealth == null || _targetHealth.IsDead)
            return;

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

        Vector3 toPlayer = _targetHealth.transform.position - transform.position;
        toPlayer.y = 0f;
        float distance = toPlayer.magnitude;
        if (distance > 0.0001f)
        {
            Vector3 direction = toPlayer / distance;
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), 1f - Mathf.Exp(-12f * Time.deltaTime));

            Vector3 move = Vector3.zero;
            if (distance > preferredRange + rangeSlack)
                move = direction * approachSpeed;
            else if (distance < preferredRange - rangeSlack)
                move = -direction * (approachSpeed * 0.7f);
            Move(move);

            if (distance <= attackRange && Time.time >= _attackReadyAt)
                BeginTelegraph(direction);
        }
    }

    public void ApplyHitReaction(Vector3 direction, float strength)
    {
        if (IsDead)
            return;
        direction.y = 0f;
        if (direction.sqrMagnitude < 0.0001f)
            direction = -transform.forward;
        _knockbackVelocity = direction.normalized * Mathf.Max(hitKnockback, strength);
        _staggerUntil = Time.time + staggerDuration;
        _windupRemaining = 0f;
        if (_warning != null)
            _warning.gameObject.SetActive(false);
    }

    void BeginTelegraph(Vector3 direction)
    {
        _attackDirection = direction.normalized;
        if (_attackDirection.sqrMagnitude > 0.0001f)
            transform.rotation = Quaternion.LookRotation(_attackDirection);
        _windupRemaining = attackWindup;
        if (_warning != null)
            _warning.gameObject.SetActive(true);
    }

    void ResolveAttack()
    {
        _windupRemaining = 0f;
        _attackReadyAt = Time.time + attackCooldown;
        if (_warning != null)
            _warning.gameObject.SetActive(false);
        AttackCount++;

        if (_targetHealth == null || _targetHealth.IsDead)
            return;
        Vector3 toPlayer = _targetHealth.transform.position - transform.position;
        toPlayer.y = 0f;
        float distance = toPlayer.magnitude;
        if (distance > attackRange || distance < 0.0001f)
            return;
        float requiredDot = Mathf.Cos(attackHalfAngle * Mathf.Deg2Rad);
        if (Vector3.Dot(_attackDirection, toPlayer / distance) < requiredDot)
            return;
        if (_targetMotor != null && _targetMotor.IsInvulnerable)
        {
            DodgedAttackCount++;
            return;
        }

        float before = _targetHealth.CurrentHealth;
        _targetHealth.TakeDamage(attackDamage);
        if (_targetHealth.CurrentHealth < before)
        {
            HitCount++;
            if (_targetMotor != null)
                _targetMotor.ApplyKnockback(-_attackDirection, playerKnockback, 0.24f);
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

    void OnDamaged(float amount, float remaining)
    {
        _flashUntil = Time.time + 0.14f;
    }

    void OnDied()
    {
        _dead = true;
        _windupRemaining = 0f;
        if (_warning != null)
            _warning.gameObject.SetActive(false);
        if (_controller != null)
            _controller.enabled = false;
        if (_visualRoot != null)
            _visualRoot.localRotation = Quaternion.Euler(82f, 0f, 28f);
        ApplyColor(deadColor);
    }

    void UpdateVisualColor()
    {
        if (_material == null || IsDead)
            return;
        Color desired = Time.time < _flashUntil ? flashColor : (IsTelegraphing ? windupColor : aliveColor);
        if (desired != _shownColor)
            ApplyColor(desired);
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
        GameObject disk = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disk.name = "EnemyAttackTelegraph";
        disk.transform.SetParent(transform, false);
        disk.transform.localPosition = new Vector3(0f, 0.045f, 0f);
        disk.transform.localScale = new Vector3(attackRange * 2f, 0.035f, attackRange * 2f);
        Collider collider = disk.GetComponent<Collider>();
        if (collider != null)
            Destroy(collider);
        Renderer renderer = disk.GetComponent<Renderer>();
        if (renderer != null)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
                shader = Shader.Find("Standard");
            _warningMaterial = new Material(shader);
            Color warning = new Color(1f, 0.08f, 0.035f);
            if (_warningMaterial.HasProperty("_BaseColor"))
                _warningMaterial.SetColor("_BaseColor", warning);
            if (_warningMaterial.HasProperty("_Color"))
                _warningMaterial.color = warning;
            if (_warningMaterial.HasProperty("_EmissionColor"))
            {
                _warningMaterial.EnableKeyword("_EMISSION");
                _warningMaterial.SetColor("_EmissionColor", warning * 0.8f);
            }
            renderer.material = _warningMaterial;
        }
        _warning = disk.transform;
        _warning.gameObject.SetActive(false);
    }
}
