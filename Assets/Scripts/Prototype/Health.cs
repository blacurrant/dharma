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

    public void TakeDamage(float amount)
    {
        if (IsDead || amount <= 0f)
            return;

        _current = Mathf.Max(0f, _current - amount);
        Damaged?.Invoke(amount, _current);
        if (IsDead)
            Died?.Invoke();
    }
}
