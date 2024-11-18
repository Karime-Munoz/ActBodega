using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BoxesAppear : MonoBehaviour
{
    public GameObject prefabBox;
    private float randomX;
    private float randomZ;  
    // Start is called before the first frame update
    void Start()
    {
        //CreateBoxes();
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    public List<GameObject> spawnedBoxes = new List<GameObject>();
    public void CreateBoxes()
    {
        for (int i = 0; i < 15; i++) 
        {
            randomX = Random.Range(-10, 10);
            randomZ= Random.Range(-10, 10);
            GameObject a = Instantiate(prefabBox) as GameObject;
            a.transform.position = new Vector3(randomX, 0f, randomZ);

            spawnedBoxes.Add(a);
        }
    }
}
