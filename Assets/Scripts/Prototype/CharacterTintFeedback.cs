using UnityEngine;

/// <summary>
/// Hit-flash / telegraph / death tint for a Paladin visual, applied per renderer with a MaterialPropertyBlock.
/// The shared material assets are never written to, so the player's and the enemy's materials stay independent.
/// Sits on the gameplay root (Player or ArenaEnemy) and reads that root's Health (and TrainingDummy, if any).
/// </summary>
public class CharacterTintFeedback : MonoBehaviour
{
    [SerializeField] Health health;
    [Tooltip("Optional: when set, the visual glows while the enemy telegraphs its strike.")]
    [SerializeField] TrainingDummy enemy;
    [Tooltip("Renderers to tint. Collected from the children when left empty.")]
    [SerializeField] Renderer[] renderers;
    [Tooltip("Multiplies the material's _BaseColor for a moment when damaged (values above 1 overbrighten).")]
    [SerializeField] Color flashColor = new Color(2.6f, 0.45f, 0.4f, 1f);
    [SerializeField] float flashDuration = 0.12f;
    [SerializeField] Color telegraphColor = new Color(2.2f, 0.9f, 0.55f, 1f);
    [SerializeField] Color deadColor = new Color(0.55f, 0.55f, 0.55f, 1f);
    [SerializeField] bool dimWhenDead = true;

    static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");

    MaterialPropertyBlock _block;
    Color[] _baseColors;
    float _flashUntil = -1f;
    Color _applied = Color.white;
    bool _hasOverride;

    public bool IsFlashing => Time.time < _flashUntil;

    void Awake()
    {
        if (health == null)
            health = GetComponent<Health>();
        if (enemy == null)
            enemy = GetComponent<TrainingDummy>();
        if (renderers == null || renderers.Length == 0)
            renderers = GetComponentsInChildren<SkinnedMeshRenderer>(true);
        _block = new MaterialPropertyBlock();
        _baseColors = new Color[renderers.Length];
        for (int i = 0; i < renderers.Length; i++)
        {
            Material m = renderers[i] != null ? renderers[i].sharedMaterial : null;
            _baseColors[i] = m != null && m.HasProperty(BaseColorId) ? m.GetColor(BaseColorId) : Color.white;
        }
    }

    void OnEnable()
    {
        if (health != null)
            health.Damaged += OnDamaged;
    }

    void OnDisable()
    {
        if (health != null)
            health.Damaged -= OnDamaged;
        Apply(Color.white, true);
    }

    void OnDamaged(float amount, float remaining)
    {
        _flashUntil = Time.time + flashDuration;
    }

    void LateUpdate()
    {
        Color target = Color.white;
        bool dead = health != null && health.IsDead;
        if (Time.time < _flashUntil)
            target = flashColor;
        else if (dead && dimWhenDead)
            target = deadColor;
        else if (enemy != null && enemy.IsTelegraphing)
            target = Color.Lerp(Color.white, telegraphColor, 0.35f + 0.65f * enemy.WindupProgress);
        Apply(target, false);
    }

    void Apply(Color tint, bool force)
    {
        bool wantsOverride = tint != Color.white;
        if (!force && wantsOverride == _hasOverride && (!wantsOverride || tint == _applied))
            return;
        _applied = tint;
        _hasOverride = wantsOverride;
        if (renderers == null)
            return;
        for (int i = 0; i < renderers.Length; i++)
        {
            Renderer r = renderers[i];
            if (r == null)
                continue;
            if (!wantsOverride)
            {
                r.SetPropertyBlock(null);
                continue;
            }
            r.GetPropertyBlock(_block);
            Color b = _baseColors[i];
            _block.SetColor(BaseColorId, new Color(b.r * tint.r, b.g * tint.g, b.b * tint.b, b.a));
            r.SetPropertyBlock(_block);
        }
    }
}
