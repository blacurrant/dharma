using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// IMGUI prototype HUD: player/enemy health bars, dash and attack cooldown bars, enemy telegraph warning,
/// damage flash + floating damage numbers, and the encounter result banner.
/// </summary>
public class PrototypeHud : MonoBehaviour
{
    [SerializeField] Health playerHealth;
    [SerializeField] PlayerMotor playerMotor;
    [SerializeField] PlayerCombat playerCombat;
    [SerializeField] Health dummyHealth;
    [SerializeField] TrainingDummy enemy;
    [SerializeField] ArenaEncounter encounter;

    struct FloatingNumber
    {
        public Transform anchor;
        public float xOffset;
        public string text;
        public Color color;
        public float startedAt;
    }

    const float NumberLifetime = 0.9f;
    const float ScreenFlashDuration = 0.35f;

    readonly List<FloatingNumber> _numbers = new List<FloatingNumber>();
    float _damageCueUntil;
    float _lastDamageAmount;
    float _screenFlashStartedAt = -10f;
    float _playerGhost = 1f;
    float _enemyGhost = 1f;
    GUIStyle _barText;
    GUIStyle _numberText;
    GUIStyle _bannerText;
    GUIStyle _hintText;
    float _guiScale = 1f;
    float _viewWidth;
    float _viewHeight;

    public void Bind(Health player, PlayerMotor motor, Health dummy)
    {
        Unsubscribe();
        playerHealth = player;
        playerMotor = motor;
        dummyHealth = dummy;
        playerCombat = motor != null ? motor.GetComponent<PlayerCombat>() : null;
        enemy = dummy != null ? dummy.GetComponent<TrainingDummy>() : null;
        Subscribe();
    }

    void Awake()
    {
        if (playerMotor == null)
            playerMotor = FindAnyObjectByType<PlayerMotor>();
        if (playerHealth == null && playerMotor != null)
            playerHealth = playerMotor.GetComponent<Health>();
        if (playerCombat == null)
            playerCombat = FindAnyObjectByType<PlayerCombat>();
        if (enemy == null)
            enemy = FindAnyObjectByType<TrainingDummy>();
        if (dummyHealth == null && enemy != null)
            dummyHealth = enemy.GetComponent<Health>();
        if (encounter == null)
            encounter = FindAnyObjectByType<ArenaEncounter>();
    }

    void OnEnable() => Subscribe();
    void OnDisable() => Unsubscribe();

    void Subscribe()
    {
        if (playerHealth != null)
            playerHealth.Damaged += OnPlayerDamaged;
        if (dummyHealth != null)
            dummyHealth.Damaged += OnEnemyDamaged;
    }

    void Unsubscribe()
    {
        if (playerHealth != null)
            playerHealth.Damaged -= OnPlayerDamaged;
        if (dummyHealth != null)
            dummyHealth.Damaged -= OnEnemyDamaged;
    }

    void OnPlayerDamaged(float amount, float remaining)
    {
        _lastDamageAmount = amount;
        _damageCueUntil = Time.time + 0.65f;
        _screenFlashStartedAt = Time.time;
        AddNumber(playerHealth.transform, "-" + Mathf.CeilToInt(amount), new Color(1f, 0.28f, 0.2f));
    }

    void OnEnemyDamaged(float amount, float remaining)
    {
        AddNumber(dummyHealth.transform, Mathf.CeilToInt(amount).ToString(), new Color(1f, 0.93f, 0.45f));
    }

    void AddNumber(Transform anchor, string text, Color color)
    {
        _numbers.Add(new FloatingNumber
        {
            anchor = anchor,
            xOffset = Random.Range(-0.35f, 0.35f),
            text = text,
            color = color,
            startedAt = Time.time
        });
    }

    void Update()
    {
        // Trailing "ghost" bar: shows how much health the last hit removed.
        _playerGhost = TrailTowards(_playerGhost, Ratio(playerHealth));
        _enemyGhost = TrailTowards(_enemyGhost, Ratio(dummyHealth));
        for (int i = _numbers.Count - 1; i >= 0; i--)
        {
            if (Time.time - _numbers[i].startedAt > NumberLifetime)
                _numbers.RemoveAt(i);
        }
    }

    // IMGUI tints are not gamma-corrected in a Linear project, which washes colours out; convert so they read as authored.
    static Color Tint(Color c) => QualitySettings.activeColorSpace == ColorSpace.Linear ? c.linear : c;

    static float Ratio(Health h) => h == null || h.MaxHealth <= 0f ? 0f : Mathf.Clamp01(h.CurrentHealth / h.MaxHealth);

    static float TrailTowards(float ghost, float target)
    {
        if (target >= ghost)
            return target;
        return Mathf.MoveTowards(ghost, target, 0.6f * Time.deltaTime);
    }

    // ---- drawing --------------------------------------------------------------------------------

    void EnsureStyles()
    {
        if (_barText != null)
            return;
        _barText = new GUIStyle(GUI.skin.label) { fontSize = 15, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleLeft, padding = new RectOffset(10, 6, 0, 0) };
        _numberText = new GUIStyle(GUI.skin.label) { fontSize = 26, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
        _bannerText = new GUIStyle(GUI.skin.label) { fontSize = 46, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
        _hintText = new GUIStyle(GUI.skin.label) { fontSize = 13, alignment = TextAnchor.MiddleLeft, padding = new RectOffset(4, 0, 0, 0) };
    }

    void OnGUI()
    {
        EnsureStyles();
        // Lay out in a virtual 600-unit-tall space so the HUD stays proportionate at any Game view size.
        _guiScale = Mathf.Clamp(Screen.height / 600f, 0.7f, 2f);
        _viewWidth = Screen.width / _guiScale;
        _viewHeight = Screen.height / _guiScale;
        GUI.matrix = Matrix4x4.Scale(new Vector3(_guiScale, _guiScale, 1f));
        DrawScreenFlash();
        DrawPanel();
        DrawFloatingNumbers();
        DrawBanner();
    }

    void DrawScreenFlash()
    {
        float t = (Time.time - _screenFlashStartedAt) / ScreenFlashDuration;
        if (t < 0f || t >= 1f)
            return;
        GUI.color = Tint(new Color(1f, 0.05f, 0.02f, 0.28f * (1f - t)));
        GUI.DrawTexture(new Rect(0f, 0f, _viewWidth, _viewHeight), Texture2D.whiteTexture);
        GUI.color = Color.white;
    }

    void DrawPanel()
    {
        const int pad = 14;
        const int width = 330;
        const int rowHeight = 30;
        const int gap = 5;
        float y = pad;

        bool playerDown = playerHealth != null && playerHealth.IsDead;

        // Player health.
        string hp = playerHealth == null ? "PLAYER  HP --" : playerDown
            ? "PLAYER DOWN"
            : $"PLAYER  {Mathf.CeilToInt(playerHealth.CurrentHealth)} / {Mathf.CeilToInt(playerHealth.MaxHealth)} HP";
        if (Time.time < _damageCueUntil && !playerDown)
            hp += $"   HIT -{Mathf.CeilToInt(_lastDamageAmount)}";
        float hpRatio = Ratio(playerHealth);
        DrawBar(new Rect(pad, y, width, rowHeight), hpRatio, _playerGhost, Color.Lerp(new Color(0.9f, 0.18f, 0.15f), new Color(0.3f, 0.85f, 0.35f), hpRatio), hp);
        y += rowHeight + gap;

        // Dash.
        string dash;
        float dashFill;
        Color dashColor;
        if (playerDown || playerMotor == null)
        {
            dash = playerDown ? "DASH  DISABLED" : "DASH  --";
            dashFill = 0f;
            dashColor = new Color(0.4f, 0.4f, 0.4f);
        }
        else if (playerMotor.IsDashing)
        {
            dash = "DASH  ACTIVE";
            dashFill = 1f;
            dashColor = new Color(0.85f, 1f, 1f);
        }
        else if (playerMotor.IsDashReady)
        {
            dash = "DASH  READY";
            dashFill = 1f;
            dashColor = new Color(0.3f, 0.78f, 1f);
        }
        else
        {
            dash = $"DASH  {playerMotor.DashCooldownRemaining:0.0}s";
            dashFill = 1f - Mathf.Clamp01(playerMotor.DashCooldownRemaining / Mathf.Max(0.01f, playerMotor.DashCooldownDuration));
            dashColor = new Color(0.8f, 0.62f, 0.22f);
        }
        DrawBar(new Rect(pad, y, width, rowHeight), dashFill, -1f, dashColor, dash);
        y += rowHeight + gap;

        // Attack.
        string attack;
        float attackFill;
        Color attackColor;
        if (playerDown || playerCombat == null)
        {
            attack = playerDown ? "ATTACK  DISABLED" : "ATTACK  --";
            attackFill = 0f;
            attackColor = new Color(0.4f, 0.4f, 0.4f);
        }
        else if (playerCombat.IsAttackReady)
        {
            attack = "ATTACK  READY";
            attackFill = 1f;
            attackColor = new Color(1f, 0.78f, 0.25f);
        }
        else
        {
            attack = $"ATTACK  {playerCombat.AttackCooldownRemaining:0.0}s";
            attackFill = 1f - Mathf.Clamp01(playerCombat.AttackCooldownRemaining / Mathf.Max(0.01f, playerCombat.AttackCooldownDuration));
            attackColor = new Color(0.8f, 0.55f, 0.2f);
        }
        if (!playerDown && playerCombat != null && Time.time - playerCombat.LastAttackTime < 0.55f && playerCombat.LastHitCount > 0)
            attack += $"   HIT x{playerCombat.LastHitCount}";
        DrawBar(new Rect(pad, y, width, rowHeight), attackFill, -1f, attackColor, attack);
        y += rowHeight + gap;

        // Enemy health.
        string enemyText = dummyHealth == null ? "ENEMY  --" : dummyHealth.IsDead
            ? "ENEMY  DOWN"
            : $"ENEMY  {Mathf.CeilToInt(dummyHealth.CurrentHealth)} / {Mathf.CeilToInt(dummyHealth.MaxHealth)} HP";
        DrawBar(new Rect(pad, y, width, rowHeight), Ratio(dummyHealth), _enemyGhost, new Color(0.78f, 0.3f, 0.28f), enemyText);
        y += rowHeight + gap;

        // Enemy state / telegraph warning.
        string state = playerDown ? "YOU WERE DEFEATED" : enemy == null ? string.Empty : enemy.IsDead
            ? "ENCOUNTER CLEAR"
            : enemy.IsTelegraphing ? $"WARNING  STRIKE IN {enemy.WindupRemaining:0.0}s"
            : enemy.IsStaggered ? "ENEMY STAGGERED"
            : enemy.IsRecovering ? "ENEMY RECOVERING"
            : "ENEMY APPROACHING";
        if (!playerDown && enemy != null && !enemy.IsDead && !enemy.IsTelegraphing && enemy.LastOutcome != "NONE" && Time.time - enemy.LastResolvedAt < 1.1f)
            state += $"   ({enemy.LastOutcome})";
        if (!string.IsNullOrEmpty(state))
        {
            bool warning = !playerDown && enemy != null && enemy.IsTelegraphing;
            Color stateColor = playerDown ? new Color(0.85f, 0.25f, 0.2f) : warning
                ? Color.Lerp(new Color(0.9f, 0.4f, 0.05f), new Color(1f, 0.1f, 0.05f), Mathf.PingPong(Time.time * 8f, 1f))
                : enemy != null && enemy.IsDead ? new Color(0.3f, 0.7f, 0.35f) : new Color(0.25f, 0.25f, 0.28f);
            DrawBar(new Rect(pad, y, width, rowHeight), 1f, -1f, stateColor, state);
            y += rowHeight + gap;
        }

        GUI.color = Color.white;
        GUI.Label(new Rect(pad, y, width + 140, 22), "WASD move   SPACE dash   LMB / ENTER attack   R restart", _hintText);
    }

    void DrawBar(Rect rect, float fill, float ghost, Color fillColor, string label)
    {
        GUI.color = new Color(0f, 0f, 0f, 0.7f);
        GUI.DrawTexture(rect, Texture2D.whiteTexture);
        Rect inner = new Rect(rect.x + 3f, rect.y + 3f, rect.width - 6f, rect.height - 6f);
        if (ghost > fill)
        {
            GUI.color = new Color(1f, 1f, 1f, 0.55f);
            GUI.DrawTexture(new Rect(inner.x, inner.y, inner.width * Mathf.Clamp01(ghost), inner.height), Texture2D.whiteTexture);
        }
        GUI.color = Tint(fillColor);
        GUI.DrawTexture(new Rect(inner.x, inner.y, inner.width * Mathf.Clamp01(fill), inner.height), Texture2D.whiteTexture);
        DrawShadowedLabel(rect, label, _barText, Color.white);
    }

    static void DrawShadowedLabel(Rect rect, string text, GUIStyle style, Color color)
    {
        GUI.color = new Color(0f, 0f, 0f, color.a * 0.85f);
        GUI.Label(new Rect(rect.x + 1.5f, rect.y + 1.5f, rect.width, rect.height), text, style);
        GUI.color = Tint(color);
        GUI.Label(rect, text, style);
        GUI.color = Color.white;
    }

    void DrawFloatingNumbers()
    {
        Camera cam = Camera.main;
        if (cam == null)
            return;
        for (int i = 0; i < _numbers.Count; i++)
        {
            FloatingNumber n = _numbers[i];
            if (n.anchor == null)
                continue;
            float age = (Time.time - n.startedAt) / NumberLifetime;
            Vector3 world = n.anchor.position + new Vector3(n.xOffset, 2.4f + age * 1.1f, 0f);
            Vector3 screen = cam.WorldToScreenPoint(world);
            if (screen.z <= 0f)
                continue;
            Color c = n.color;
            c.a = 1f - Mathf.Clamp01((age - 0.45f) / 0.55f);
            DrawShadowedLabel(new Rect(screen.x / _guiScale - 60f, (Screen.height - screen.y) / _guiScale - 20f, 120f, 40f), n.text, _numberText, c);
        }
    }

    void DrawBanner()
    {
        if (encounter == null || encounter.State == ArenaEncounter.EncounterState.Fighting)
            return;
        bool cleared = encounter.State == ArenaEncounter.EncounterState.Cleared;
        Color tint = cleared ? new Color(0.45f, 1f, 0.55f) : new Color(1f, 0.35f, 0.3f);
        float a = Mathf.Clamp01(encounter.ElapsedSinceStateChange / 0.4f);
        GUI.color = new Color(0f, 0f, 0f, 0.45f * a);
        GUI.DrawTexture(new Rect(0f, _viewHeight * 0.74f, _viewWidth, 130f), Texture2D.whiteTexture);
        tint.a = a;
        DrawShadowedLabel(new Rect(0f, _viewHeight * 0.74f, _viewWidth, 85f), cleared ? "ENCOUNTER CLEAR" : "YOU DIED", _bannerText, tint);
        DrawShadowedLabel(new Rect(0f, _viewHeight * 0.74f + 80f, _viewWidth, 40f), "Press R to restart", _numberText, new Color(1f, 1f, 1f, a));
    }
}
