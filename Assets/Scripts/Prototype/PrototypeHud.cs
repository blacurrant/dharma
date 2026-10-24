using UnityEngine;

public class PrototypeHud : MonoBehaviour
{
    [SerializeField] Health playerHealth;
    [SerializeField] PlayerMotor playerMotor;
    [SerializeField] PlayerCombat playerCombat;
    [SerializeField] Health dummyHealth;
    [SerializeField] TrainingDummy enemy;

    float _damageCueUntil;
    float _lastDamageAmount;

    public void Bind(Health player, PlayerMotor motor, Health dummy)
    {
        playerHealth = player;
        playerMotor = motor;
        dummyHealth = dummy;
        playerCombat = motor != null ? motor.GetComponent<PlayerCombat>() : null;
        enemy = dummy != null ? dummy.GetComponent<TrainingDummy>() : null;
    }

    void Awake()
    {
        if (playerHealth == null)
        {
            PlayerMotor player = FindObjectOfType<PlayerMotor>();
            if (player != null)
                playerHealth = player.GetComponent<Health>();
        }
        if (playerMotor == null)
            playerMotor = FindObjectOfType<PlayerMotor>();
        if (playerCombat == null)
            playerCombat = FindObjectOfType<PlayerCombat>();
        if (enemy == null)
            enemy = FindObjectOfType<TrainingDummy>();
        if (dummyHealth == null && enemy != null)
            dummyHealth = enemy.GetComponent<Health>();
    }

    void OnEnable()
    {
        if (playerHealth != null)
            playerHealth.Damaged += OnPlayerDamaged;
    }

    void OnDisable()
    {
        if (playerHealth != null)
            playerHealth.Damaged -= OnPlayerDamaged;
    }

    void OnPlayerDamaged(float amount, float remaining)
    {
        _lastDamageAmount = amount;
        _damageCueUntil = Time.time + 0.65f;
    }

    void OnGUI()
    {
        const int pad = 14;
        const int width = 304;
        const int rowHeight = 34;
        GUIStyle style = new GUIStyle(GUI.skin.box)
        {
            fontSize = 16,
            alignment = TextAnchor.MiddleLeft,
            padding = new RectOffset(10, 10, 5, 5)
        };

        bool playerDown = playerHealth != null && playerHealth.IsDead;
        string hp = playerHealth == null ? "PLAYER  HP --" : playerDown
            ? "PLAYER DOWN"
            : $"PLAYER  {Mathf.CeilToInt(playerHealth.CurrentHealth)} / {Mathf.CeilToInt(playerHealth.MaxHealth)} HP";
        string dash = playerDown ? "DASH  DISABLED" : playerMotor == null ? "DASH  --" : playerMotor.IsDashing
            ? "DASH  ACTIVE"
            : playerMotor.IsDashReady ? "DASH  READY" : $"DASH  {playerMotor.DashCooldownRemaining:0.0}s";
        string attack = playerDown ? "ATTACK  DISABLED" : playerCombat == null ? "ATTACK  --" : playerCombat.IsAttackReady
            ? "ATTACK  READY"
            : $"ATTACK  {playerCombat.AttackCooldownRemaining:0.0}s";
        if (!playerDown && playerCombat != null && Time.time - playerCombat.LastAttackTime < 0.55f && playerCombat.LastHitCount > 0)
            attack += $"   HIT x{playerCombat.LastHitCount}";
        if (Time.time < _damageCueUntil && !playerDown)
            hp += $"   HIT -{Mathf.CeilToInt(_lastDamageAmount)}";

        string enemyText = dummyHealth == null ? "ENEMY  --" : dummyHealth.IsDead
            ? "ENEMY  DOWN"
            : $"ENEMY  {Mathf.CeilToInt(dummyHealth.CurrentHealth)} / {Mathf.CeilToInt(dummyHealth.MaxHealth)} HP";
        string enemyState = playerDown ? "YOU WERE DEFEATED" : enemy == null ? string.Empty : enemy.IsDead
            ? "ENCOUNTER CLEAR"
            : enemy.IsTelegraphing ? $"WARNING  STRIKE IN {enemy.WindupRemaining:0.0}s"
            : enemy.IsStaggered ? "ENEMY STAGGERED"
            : "ENEMY APPROACHING";

        GUI.color = playerDown ? new Color(1f, 0.48f, 0.35f) : playerHealth != null && playerHealth.CurrentHealth <= 30f
            ? new Color(1f, 0.62f, 0.45f) : Color.white;
        GUI.Box(new Rect(pad, pad, width, rowHeight), hp, style);
        GUI.color = playerMotor != null && !playerMotor.IsDashReady && !playerDown ? new Color(0.95f, 0.83f, 0.56f) : new Color(0.62f, 0.9f, 1f);
        GUI.Box(new Rect(pad, pad + rowHeight + 5, width, rowHeight), dash, style);
        GUI.color = playerCombat != null && !playerCombat.IsAttackReady && !playerDown ? new Color(0.95f, 0.83f, 0.56f) : new Color(1f, 0.88f, 0.54f);
        GUI.Box(new Rect(pad, pad + (rowHeight + 5) * 2, width, rowHeight), attack, style);
        GUI.color = dummyHealth != null && dummyHealth.IsDead ? new Color(0.7f, 1f, 0.72f) : Color.white;
        GUI.Box(new Rect(pad, pad + (rowHeight + 5) * 3, width, rowHeight), enemyText, style);
        if (!string.IsNullOrEmpty(enemyState))
        {
            GUI.color = playerDown || (enemy != null && enemy.IsTelegraphing) ? new Color(1f, 0.48f, 0.2f) : Color.white;
            GUI.Box(new Rect(pad, pad + (rowHeight + 5) * 4, width, rowHeight), enemyState, style);
        }
        GUI.color = Color.white;
        GUI.Label(new Rect(pad + 4, pad + (rowHeight + 5) * 5, width + 100, 26), "WASD move   SPACE dash   LMB / ENTER attack");
    }
}
