using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerCombat : MonoBehaviour
{
    [SerializeField] InputActionAsset actions;
    [SerializeField] float attackRange = 1.8f;
    [SerializeField] float attackRadius = 1.15f;
    [SerializeField, Range(0f, 90f)] float attackHalfAngle = 58f;
    [SerializeField] float damage = 25f;
    [SerializeField] float attackCooldown = 0.35f;
    [SerializeField] float hitKnockback = 4.5f;
    [SerializeField] float slashDuration = 0.18f;

    InputActionMap _playerMap;
    InputAction _attack;
    Health _self;
    PlayerMotor _motor;
    float _readyAt;
    float _slashStartedAt;
    GameObject _slash;
    Material _slashMaterial;

    public bool IsAttackReady => Time.time >= _readyAt;
    public float AttackCooldownRemaining => Mathf.Max(0f, _readyAt - Time.time);
    public int LastHitCount { get; private set; }
    public int SuccessfulSwings { get; private set; }
    public float LastAttackTime { get; private set; }

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
        if (_slash != null)
            Destroy(_slash);
        if (_slashMaterial != null)
            Destroy(_slashMaterial);
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
        UpdateSlash();
        if (_self != null && _self.IsDead)
            return;

        // Holding attack intentionally repeats one fully validated swing per cooldown.
        if (PrototypeInput.IsHeld(_attack) && IsAttackReady)
            PerformAttack();
    }

    public bool PerformAttack()
    {
        if (!IsAttackReady || (_self != null && _self.IsDead))
            return false;

        _readyAt = Time.time + attackCooldown;
        LastAttackTime = Time.time;
        LastHitCount = 0;
        SuccessfulSwings++;

        Vector3 facing = GetFacing();
        Vector3 attackOrigin = transform.position + Vector3.up;
        Vector3 hitCenter = attackOrigin + facing * Mathf.Max(0f, attackRange - attackRadius);
        Collider[] hits = Physics.OverlapSphere(hitCenter, attackRadius, ~0, QueryTriggerInteraction.Ignore);
        var damaged = new HashSet<Health>();
        float minimumFacingDot = Mathf.Cos(attackHalfAngle * Mathf.Deg2Rad);

        for (int i = 0; i < hits.Length; i++)
        {
            Health target = hits[i].GetComponentInParent<Health>();
            if (target == null || target == _self || target.IsDead || !damaged.Add(target))
                continue;

            Vector3 toTarget = target.transform.position - transform.position;
            toTarget.y = 0f;
            float distance = toTarget.magnitude;
            if (distance > attackRange || distance < 0.0001f || Vector3.Dot(facing, toTarget / distance) < minimumFacingDot)
                continue;
            if (!HasLineOfSight(attackOrigin, target, distance))
                continue;

            float before = target.CurrentHealth;
            target.TakeDamage(damage);
            if (target.CurrentHealth >= before)
                continue;

            LastHitCount++;
            TrainingDummy enemy = target.GetComponent<TrainingDummy>();
            if (enemy == null)
                enemy = target.GetComponentInParent<TrainingDummy>();
            if (enemy != null)
                enemy.ApplyHitReaction(facing, hitKnockback);
        }

        StartSlash();
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

    void StartSlash()
    {
        if (_slash != null)
            Destroy(_slash);
        _slash = GameObject.CreatePrimitive(PrimitiveType.Cube);
        _slash.name = "AttackSlashEffect";
        _slash.transform.SetParent(transform, false);
        _slash.transform.localPosition = new Vector3(0f, 1f, 0.68f);
        _slash.transform.localRotation = Quaternion.identity;
        _slash.transform.localScale = new Vector3(0.16f, 0.1f, 1.35f);
        Collider collider = _slash.GetComponent<Collider>();
        if (collider != null)
            Destroy(collider);

        Renderer renderer = _slash.GetComponent<Renderer>();
        if (renderer != null)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
                shader = Shader.Find("Standard");
            _slashMaterial = new Material(shader);
            Color slashColor = new Color(1f, 0.66f, 0.16f);
            if (_slashMaterial.HasProperty("_BaseColor"))
                _slashMaterial.SetColor("_BaseColor", slashColor);
            if (_slashMaterial.HasProperty("_Color"))
                _slashMaterial.color = slashColor;
            if (_slashMaterial.HasProperty("_EmissionColor"))
            {
                _slashMaterial.EnableKeyword("_EMISSION");
                _slashMaterial.SetColor("_EmissionColor", slashColor * 1.5f);
            }
            renderer.material = _slashMaterial;
        }
        _slashStartedAt = Time.time;
    }

    void UpdateSlash()
    {
        if (_slash == null)
            return;
        float t = slashDuration <= 0f ? 1f : (Time.time - _slashStartedAt) / slashDuration;
        if (t >= 1f)
        {
            Destroy(_slash);
            _slash = null;
            return;
        }
        _slash.transform.localRotation = Quaternion.Euler(0f, Mathf.Lerp(-62f, 62f, t), 0f);
        float length = Mathf.Lerp(1.25f, 1.5f, Mathf.Sin(t * Mathf.PI));
        _slash.transform.localScale = new Vector3(0.16f, 0.1f, length);
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
        Vector3 center = transform.position + Vector3.up + facing.normalized * Mathf.Max(0f, attackRange - attackRadius);
        Gizmos.color = new Color(1f, 0.4f, 0.12f, 0.5f);
        Gizmos.DrawWireSphere(center, attackRadius);
        Gizmos.color = new Color(1f, 0.9f, 0.2f, 0.35f);
        Gizmos.DrawWireSphere(transform.position + Vector3.up, attackRange);
    }
}
