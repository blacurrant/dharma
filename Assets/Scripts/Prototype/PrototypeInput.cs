using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;

public static class PrototypeInput
{
    public static bool IsHeld(InputAction action)
    {
        if (action == null)
            return false;
        if (action.IsPressed())
            return true;

        var controls = action.controls;
        for (int i = 0; i < controls.Count; i++)
        {
            if (controls[i] is ButtonControl button && button.isPressed)
                return true;
        }

        return false;
    }
}
