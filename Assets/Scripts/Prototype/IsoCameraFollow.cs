using UnityEngine;

[DefaultExecutionOrder(50)]
public class IsoCameraFollow : MonoBehaviour
{
    [SerializeField] Transform target;
    [SerializeField] Vector3 offset = new Vector3(12f, 18f, -12f);
    [SerializeField] float followSpeed = 14f;
    [SerializeField] float orthographicSize = 11f;

    Camera _camera;

    public Transform Target
    {
        get => target;
        set => target = value;
    }

    void Awake()
    {
        _camera = GetComponent<Camera>();
        if (_camera != null)
        {
            _camera.orthographic = true;
            _camera.orthographicSize = orthographicSize;
            _camera.nearClipPlane = 0.1f;
            _camera.farClipPlane = 80f;
        }

        transform.rotation = Quaternion.LookRotation(-offset.normalized, Vector3.up);
        Snap();
    }

    void LateUpdate()
    {
        if (target == null)
            return;

        Vector3 desired = target.position + offset;
        float t = 1f - Mathf.Exp(-followSpeed * Time.deltaTime);
        transform.position = Vector3.Lerp(transform.position, desired, t);
        transform.rotation = Quaternion.LookRotation(-offset.normalized, Vector3.up);
    }

    public void Snap()
    {
        if (target != null)
            transform.position = target.position + offset;
    }
}
