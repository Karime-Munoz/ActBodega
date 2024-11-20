using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting.Antlr3.Runtime.Misc;
using UnityEngine;

public class ShelfController : MonoBehaviour
{
    public List<Transform> boxSlots; // Posiciones para las cajas
    private List<GameObject> occupiedSlots = new List<GameObject>();

    public bool HasAvailableSlot()
    {
        return occupiedSlots.Count < boxSlots.Count;
    }

    public Vector3 GetNextAvailableSlot()
    {
        foreach (Transform slot in boxSlots)
        {
            if (!occupiedSlots.Exists(box => box.transform.position == slot.position))
            {
                return slot.position;
            }
        }
        return Vector3.zero; // Si no hay slots disponibles
    }

    public void AddBoxToShelf(GameObject box)
    {
        if (!HasAvailableSlot()) return;
        occupiedSlots.Add(box);
    }
}

