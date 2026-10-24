using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(CharacterController))]
public class PlayerMotor : MonoBehaviour
{
    [SerializeField] InputActionAsset actions;
    [SerializeField] float moveSpeed = 8f;
    [SerializeField] float dashSpeed = 22f;
    [SerializeField] float dashDuration = 0.14f;
    [SerializeField] float dashCooldown = 0.75f;
    [SerializeField] Transform cameraTransform;
    [SerializeField] Color damageFlashColor = new Color(1f, 0.2f, 0.16f);
    [SerializeField] float damageFlashDuration = 0.12f;
    [SerializeField] float knockbackDrag = 28f;

    CharacterController _controller;
    InputActionMap _playerMap;
    InputAction _move;
    InputAction _dash;
    Health _health;
    Renderer _visualRenderer;
    Material _visualMaterial;
    Color _baseColor = Color.white;
    Vector3 _facing = Vector3.forward;
    Vector3 _dashDirection;
    Vector3 _knockbackVelocity;
    float _dashTimeRemaining;
    float _dashReadyAt;
    float _knockbackUntil;
    float _flashUntil;
    Vector3 _bodyHomePosition;
    Quaternion _bodyHomeRotation = Quaternion.identity;
    Color _homeColor = Color.white;

    public int DashCount { get; private set; }
    public float DashCooldownDuration => dashCooldown;
    public Vector3 Velocity { get; private set; }
    public Vector3 Facing => _facing;
    public bool IsDashing => _dashTimeRemaining > 0f;
    public bool IsInvulnerable => IsDashing;
    public bool IsDashReady => !IsDashing && Time.time >= _dashReadyAt;
    public float DashCooldownRemaining => Mathf.Max(0f, _dashReadyAt - Time.time);

    void Awake()
    {
        _controller = GetComponent<CharacterController>();
        _health = GetComponent<Health>();
        _visualRenderer = GetComponentInChildren<Renderer>();
        if (_visualRenderer != null)
        {
            _visualMaterial = _visualRenderer.material;
            if (_visualMaterial.HasProperty("_BaseColor"))
                _baseColor = _visualMaterial.GetColor("_BaseColor");
            else if (_visualMaterial.HasProperty("_Color"))
                _baseColor = _visualMaterial.color;
            _homeColor = _baseColor;
            _bodyHomePosition = _visualRenderer.transform.localPosition;
            _bodyHomeRotation = _visualRenderer.transform.localRotation;
        }
        ResolveCamera();
    }

    void OnEnable()
    {
        ResolveActions();
        _playerMap?.Enable();
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

    /// <summary>Moves the player without the CharacterController fighting the change, and clears transient state.</summary>
    public void TeleportTo(Vector3 position, Quaternion rotation)
    {
        if (_controller != null)
            _controller.enabled = false;
        transform.SetPositionAndRotation(position, rotation);
        if (_controller != null)
            _controller.enabled = true;

        Vector3 forward = rotation * Vector3.forward;
        forward.y = 0f;
        _facing = forward.sqrMagnitude > 0.0001f ? forward.normalized : Vector3.forward;
        _dashTimeRemaining = 0f;
        _dashReadyAt = 0f;
        _knockbackVelocity = Vector3.zero;
        _knockbackUntil = 0f;
        _flashUntil = 0f;
        Velocity = Vector3.zero;

        _baseColor = _homeColor;
        if (_visualRenderer != null)
        {
            _visualRenderer.transform.localPosition = _bodyHomePosition;
            _visualRenderer.transform.localRotation = _bodyHomeRotation;
        }
    }

    void OnDied()
    {
        _dashTimeRemaining = 0f;
        _knockbackVelocity = Vector3.zero;
        _baseColor = _homeColor * 0.4f;
        _baseColor.a = _homeColor.a;
        if (_visualRenderer != null)
        {
            // Placeholder death: capsule falls over and lies on the floor.
            _visualRenderer.transform.localRotation = Quaternion.Euler(0f, 0f, 85f);
            _visualRenderer.transform.localPosition = new Vector3(_bodyHomePosition.x, 0.5f, _bodyHomePosition.z);
        }
    }

    void OnDestroy()
    {
        if (_visualMaterial != null)
            Destroy(_visualMaterial);
    }

    void Start()
    {
        if (_move == null)
            ResolveActions();
    }

    void Update()
    {
        UpdateDamageFlash();
        if (_move == null)
            ResolveActions();
        if (_move == null || _controller == null)
            return;

        ResolveCamera();
        Vector2 input = _move.ReadValue<Vector2>();
        Vector3 wish = CameraRelative(input);
        if (wish.sqrMagnitude > 1f)
            wish.Normalize();
        if (wish.sqrMagnitude > 0.0001f)
            _facing = wish.normalized;

        bool alive = _health == null || !_health.IsDead;
        bool dashHeld = alive && PrototypeInput.IsHeld(_dash);
        if (dashHeld && IsDashReady)
            BeginDash(wish);

        Vector3 motion;
        if (!alive)
        {
            motion = Vector3.zero;
        }
        else if (IsDashing)
        {
            motion = _dashDirection * dashSpeed;
            _dashTimeRemaining = Mathf.Max(0f, _dashTimeRemaining - Time.deltaTime);
        }
        else
        {
            motion = wish * moveSpeed;
            if (Time.time < _knockbackUntil)
            {
                motion += _knockbackVelocity;
                _knockbackVelocity = Vector3.MoveTowards(_knockbackVelocity, Vector3.zero, knockbackDrag * Time.deltaTime);
            }
            else
            {
                _knockbackVelocity = Vector3.zero;
            }
        }

        motion.y = _controller.isGrounded ? -2f : -20f;
        Velocity = motion;
        _controller.Move(motion * Time.deltaTime);

        if (_facing.sqrMagnitude > 0.0001f)
        {
            Quaternion look = Quaternion.LookRotation(_facing, Vector3.up);
            transform.rotation = Quaternion.Slerp(transform.rotation, look, 1f - Mathf.Exp(-14f * Time.deltaTime));
        }
    }

    public void ApplyKnockback(Vector3 direction, float strength, float duration = 0.2f)
    {
        direction.y = 0f;
        if (direction.sqrMagnitude < 0.0001f)
            direction = -_facing;
        _knockbackVelocity = direction.normalized * Mathf.Max(0f, strength);
        _knockbackUntil = Time.time + Mathf.Max(0f, duration);
    }

    void OnDamaged(float amount, float remaining)
    {
        _flashUntil = Time.time + damageFlashDuration;
        SetVisualColor(damageFlashColor);
    }

    void UpdateDamageFlash()
    {
        if (_visualMaterial == null || _health == null)
            return;
        if (Time.time < _flashUntil)
            SetVisualColor(damageFlashColor);
        else
            SetVisualColor(_baseColor);
    }

    void SetVisualColor(Color color)
    {
        if (_visualMaterial == null)
            return;
        if (_visualMaterial.HasProperty("_BaseColor"))
            _visualMaterial.SetColor("_BaseColor", color);
        if (_visualMaterial.HasProperty("_Color"))
            _visualMaterial.color = color;
    }

    void BeginDash(Vector3 wish)
    {
        _dashDirection = wish.sqrMagnitude > 0.0001f ? wish.normalized : _facing;
        if (_dashDirection.sqrMagnitude < 0.0001f)
            _dashDirection = transform.forward;
        _dashDirection.y = 0f;
        _dashDirection.Normalize();
        _dashTimeRemaining = dashDuration;
        _dashReadyAt = Time.time + dashCooldown;
        DashCount++;
        _knockbackVelocity = Vector3.zero;
        _knockbackUntil = 0f;
    }

    Vector3 CameraRelative(Vector2 input)
    {
        Vector3 forward = Vector3.forward;
        Vector3 right = Vector3.right;
        if (cameraTransform != null)
        {
            forward = cameraTransform.forward;
            right = cameraTransform.right;
            forward.y = 0f;
            right.y = 0f;
            if (forward.sqrMagnitude < 0.0001f)
                forward = Vector3.forward;
            else
                forward.Normalize();
            if (right.sqrMagnitude < 0.0001f)
                right = Vector3.right;
            else
                right.Normalize();
        }
        return forward * input.y + right * input.x;
    }

    void ResolveCamera()
    {
        if (cameraTransform == null && Camera.main != null)
            cameraTransform = Camera.main.transform;
    }

    void ResolveActions()
    {
        var playerInput = GetComponent<PlayerInput>();
        InputActionAsset asset = playerInput != null && playerInput.actions != null
            ? playerInput.actions
            : (actions != null ? actions : InputSystem.actions);
        if (asset == null)
        {
            Debug.LogError("PlayerMotor: no InputActionAsset assigned and InputSystem.actions is null.");
            return;
        }
        _playerMap = asset.FindActionMap("Player", true);
        _playerMap.bindingMask = null;
        _move = _playerMap.FindAction("Move", true);
        _dash = _playerMap.FindAction("Jump", true);
    }
}
