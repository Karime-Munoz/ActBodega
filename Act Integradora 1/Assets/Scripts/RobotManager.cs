using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using System.Collections.Generic;
using System.Net;
using Newtonsoft.Json;
using System.Xml;
using Unity.VisualScripting;



[System.Serializable]
public class RobotInstruction
{
    public int id;
    public float[] position;
    public bool avoid;
}
[System.Serializable]
public class Wrapper<T>
{
    public T data;
}


public class RobotManager : MonoBehaviour
{

    //string url1 = "http://127.0.0.1:5000/setup"; //recivir saludo de server python
    //string url2 = "http://127.0.0.1:5000/receive"; //los datos que vamos a enviar de unity a python 

    public BoxesAppear boxesManager; 


    string serverURL = "http://127.0.0.1:5000";

    public List<GameObject> robots;
    private Dictionary<int, Vector3> robotPositions;

    public GameObject boxPrefab;

    //START FUN
    void Start()
    {
        robotPositions = new Dictionary<int, Vector3>();

        for (int i = 0; i < robots.Count; i++)
        {
            GameObject robot = robots[i];
            int index = i + 1;
            Vector3 position = robot.transform.position;

            robotPositions.Add(index, position);
            Debug.Log($"Robot {index}: initial pos= {position}");

        }

        StartCoroutine(SendRobotAndBoxPositions());
        //StartCoroutine(FetchNewPosition());
        //MoveRobot(1, Roboto1Pos);


    }

    //Vector3 Roboto1Pos = new Vector3(-10f, 0.0f, -11f);


    void Update()
    {

        //SendRobotPositons();


    }

    IEnumerator FetchNewPosition()
    {
        while (true)
        {
            UnityWebRequest webRequest = UnityWebRequest.Get($"{serverURL}/positions");
            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.ConnectionError)
            {
                Debug.LogError("Error al conectar" + webRequest.error);

            }
            else
            {
                string jsonResponse = webRequest.downloadHandler.text;
                List<RobotInstruction> instructions = JsonConvert.DeserializeObject<List<RobotInstruction>>(jsonResponse);

                foreach (var instruction in instructions)
                {
                    ProcessInstruction(instruction);
                }
            }
            yield return new WaitForSeconds(2);
        }
    }

    void ProcessInstruction(RobotInstruction instruction)
    {
        if (instruction.avoid)
        {
            Debug.Log($"Robot {instruction.id} esquiva un obstaculo");
        }
        else
        {
            Vector3 targetPosition = new Vector3(
                instruction.position[0],
                instruction.position[1],
                instruction.position[2]
            );
            MoveRobot(instruction.id, targetPosition);
        }
    }

    IEnumerator SendRobotAndBoxPositions()
    {
        var positions = new List<Dictionary<string, object>>();

        
        foreach (var entry in robotPositions)
        {
            positions.Add(new Dictionary<string, object>
        {
            {"type", "robot"},
            {"id", entry.Key},
            {"position", new float[] {entry.Value.x, entry.Value.y, entry.Value.z}}
        });
        }

        
        foreach (GameObject box in boxesManager.spawnedBoxes)
        {
            Vector3 pos = box.transform.position;
            positions.Add(new Dictionary<string, object>
        {
            {"type", "box"},
            {"id", box.GetInstanceID()}, // Usa el ID único del objeto para identificarlo
            {"position", new float[] {pos.x, pos.y, pos.z}}
        });
        }

        // Serializar a JSON
        string json = JsonConvert.SerializeObject(new Wrapper<List<Dictionary<string, object>>>() { data = positions });
        Debug.Log(json);

        UnityWebRequest webRequest = new UnityWebRequest($"{serverURL}/initial", "POST");
        byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(json);

        webRequest.uploadHandler = new UploadHandlerRaw(jsonToSend);
        webRequest.downloadHandler = new DownloadHandlerBuffer();
        webRequest.SetRequestHeader("Content-Type", "application/json");

        yield return webRequest.SendWebRequest();

        if (webRequest.result == UnityWebRequest.Result.ConnectionError)
        {
            Debug.LogError("Error: " + webRequest.error);
        }
        else
        {
            Debug.Log("Success! Data sent: " + webRequest.downloadHandler.text);
        }
    }



    public void MoveRobot(int index, Vector3 newPosition)
    {
        if (robotPositions.ContainsKey(index))
        {
            robotPositions[index] = newPosition;

            GameObject robot = robots[index - 1];
            RobotController controller = robot.GetComponent<RobotController>();
            if (controller != null)
            {
                controller.SetTargetPosition(newPosition);
            }
            Debug.Log($"Robot {index} moved to {newPosition}");
        }
        else
        {

            Debug.LogError($"Robot {index} not found");
        }
    }



}