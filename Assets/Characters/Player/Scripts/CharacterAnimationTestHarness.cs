using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Isolated test harness for the protagonist Animator. Lives only in CharacterRigTest.unity.
/// It does not reference any combat/gameplay scripts; it only drives the Animator parameters
/// (Speed, Dash, Attack, Hit, Dead) so every clip can be triggered separately.
/// Keys: 1 Idle  2 Run (toggle)  3 Dash  4 Attack  5 Hit  6 Death (toggle)  0 reset
/// </summary>
public class CharacterAnimationTestHarness : MonoBehaviour
{
    [SerializeField] Animator animator;
    [Tooltip("Animator 'Speed' value used for Run.")]
    [SerializeField] float runSpeedValue = 1f;
    [SerializeField] bool showPanel = true;

    static readonly int SpeedHash = Animator.StringToHash("Speed");
    static readonly int DashHash = Animator.StringToHash("Dash");
    static readonly int AttackHash = Animator.StringToHash("Attack");
    static readonly int HitHash = Animator.StringToHash("Hit");
    static readonly int DeadHash = Animator.StringToHash("Dead");

    Vector3 _startPosition;
    Quaternion _startRotation;
    bool _running;
    bool _dead;

    public Animator Target => animator;
    public bool IsRunning => _running;
    public bool IsDead => _dead;
    /// <summary>Distance the animated object has moved from where it started (should stay ~0 with root motion off).</summary>
    public float Drift => animator == null ? 0f : Vector3.Distance(animator.transform.position, _startPosition);
    public float YawDrift => animator == null ? 0f : Quaternion.Angle(animator.transform.rotation, _startRotation);

    public static readonly string[] StateNames = { "Idle", "Run", "Dash", "Attack", "HitReaction", "Death" };

    public string CurrentStateName
    {
        get
        {
            if (animator == null) return "-";
            AnimatorStateInfo s = animator.GetCurrentAnimatorStateInfo(0);
            foreach (string n in StateNames)
                if (s.IsName(n)) return n;
            return "?";
        }
    }

    public float CurrentNormalizedTime => animator == null ? 0f : animator.GetCurrentAnimatorStateInfo(0).normalizedTime;
    public bool InTransition => animator != null && animator.IsInTransition(0);

    void Awake()
    {
        if (animator == null)
            animator = GetComponentInChildren<Animator>();
        if (animator != null)
        {
            _startPosition = animator.transform.position;
            _startRotation = animator.transform.rotation;
        }
    }

    void Update()
    {
        Keyboard kb = Keyboard.current;
        if (kb == null) return;
        if (kb.digit1Key.wasPressedThisFrame) SetRun(false);
        if (kb.digit2Key.wasPressedThisFrame) SetRun(!_running);
        if (kb.digit3Key.wasPressedThisFrame) TriggerDash();
        if (kb.digit4Key.wasPressedThisFrame) TriggerAttack();
        if (kb.digit5Key.wasPressedThisFrame) TriggerHit();
        if (kb.digit6Key.wasPressedThisFrame) SetDead(!_dead);
        if (kb.digit0Key.wasPressedThisFrame) ResetAll();
    }

    public void SetRun(bool run)
    {
        _running = run;
        if (animator != null) animator.SetFloat(SpeedHash, run ? runSpeedValue : 0f);
    }

    public void TriggerDash() { if (animator != null) animator.SetTrigger(DashHash); }
    public void TriggerAttack() { if (animator != null) animator.SetTrigger(AttackHash); }
    public void TriggerHit() { if (animator != null) animator.SetTrigger(HitHash); }

    public void SetDead(bool dead)
    {
        _dead = dead;
        if (animator == null) return;
        if (dead)
        {
            animator.ResetTrigger(DashHash);
            animator.ResetTrigger(AttackHash);
            animator.ResetTrigger(HitHash);
        }
        animator.SetBool(DeadHash, dead);
    }

    public void ResetAll()
    {
        SetRun(false);
        SetDead(false);
    }

    void OnGUI()
    {
        if (!showPanel || animator == null) return;
        float scale = Mathf.Clamp(Screen.height / 600f, 0.7f, 2f);
        GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));
        const float x = 10f, w = 190f, h = 26f;
        float y = 10f;
        GUI.Box(new Rect(x, y, w, 62f), $"STATE  {CurrentStateName}{(InTransition ? "  (blend)" : "")}\nnormTime {CurrentNormalizedTime:0.00}   drift {Drift:0.000} m");
        y += 68f;
        if (GUI.Button(new Rect(x, y, w, h), "1  Idle")) SetRun(false); y += h + 3f;
        if (GUI.Button(new Rect(x, y, w, h), _running ? "2  Run  (on)" : "2  Run")) SetRun(!_running); y += h + 3f;
        if (GUI.Button(new Rect(x, y, w, h), "3  Dash")) TriggerDash(); y += h + 3f;
        if (GUI.Button(new Rect(x, y, w, h), "4  Attack")) TriggerAttack(); y += h + 3f;
        if (GUI.Button(new Rect(x, y, w, h), "5  Hit Reaction")) TriggerHit(); y += h + 3f;
        if (GUI.Button(new Rect(x, y, w, h), _dead ? "6  Death  (revive)" : "6  Death")) SetDead(!_dead); y += h + 3f;
        if (GUI.Button(new Rect(x, y, w, h), "0  Reset")) ResetAll();
    }
}
