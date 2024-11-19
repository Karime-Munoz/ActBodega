using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ShelfController : MonoBehaviour
{
    public List<Transform> boxSlots; // Posiciones para las cajas
    private List<bool> slotOccupied;

    void Start()
    {
        slotOccupied = new List<bool>(new bool[boxSlots.Count]);
    }

    public bool HasAvailableSlot()
    {
        return slotOccupied.Contains(false);
    }

    public Vector3 GetNextAvailableSlot()
    {
        for (int i = 0; i < slotOccupied.Count; i++)
        {
            if (!slotOccupied[i])
            {
                slotOccupied[i] = true;
                return boxSlots[i].position;
            }
        }
        return Vector3.zero; // Retorna un valor por defecto si no hay slots disponibles
    }
}

