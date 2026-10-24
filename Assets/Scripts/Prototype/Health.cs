using System;
using UnityEngine;

public class Health : MonoBehaviour
{
    [SerializeField] float maxHealth = 100f;

    float _current;

    public float MaxHealth => maxHealth;
    public float CurrentHealth => _current;
    public bool IsDead => _current <= 0f;

    public event Action<float, float> Damaged;
    public event Action Died;

    void Awake()
    {
        _current = maxHealth;
    }

    /// <returns>true if health was actually reduced.</returns>
    public bool TakeDamage(float amount)
    {
        if (IsDead || amount <= 0f)
            return false;

        _current = Mathf.Max(0f, _current - amount);
        Damaged?.Invoke(amount, _current);
        if (IsDead)
            Died?.Invoke();
        return true;
    }

    /// <summary>Restores full health (used by encounter restart). Raises no events.</summary>
    public void Revive()
    {
        _current = maxHealth;
    }
}
