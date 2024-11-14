using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class MoveOnWayPoint : MonoBehaviour
{

    public List<GameObject> waypoints;
    public float Speed = 2;
    int index = 0;
    public bool Loop = true;
    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        Vector3 destination = waypoints[index].transform.position;
        Vector3 newPos = Vector3.MoveTowards(transform.position, destination, Speed * Time.deltaTime);
        transform.position = newPos;

        float distance = Vector3.Distance(transform.position, destination);
        if (distance <= 0.01)
        {
            //index++;
            if (index < waypoints.Count - 1)
            {
                index++;
            }
            else
            {
                if (Loop)
                {
                    index = 0;
                }
            }
        }
    }
}
