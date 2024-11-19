using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using System.Collections.Generic;
using System.Net;
using Newtonsoft.Json;
using System.Xml;
using Unity.VisualScripting;
using UnityEditor.PackageManager.Requests;

public class RobotManager : MonoBehaviour
{
    
    string serverURL = "http://127.0.0.1:5000";

    public List<GameObject> robots;
    private Dictionary<int, Vector3> robotPositions = new Dictionary<int, Vector3>(); // Inicialización aquí

    public BoxesAppear boxesManager;

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
            //Debug.Log($"Robot {index}: initial pos= {position}");

        }

        boxesManager.CreateBoxes(5);
        
        //Inicializar rutas
        StartCoroutine(InitializeModelOnServer());
        StartCoroutine(SendRobotPositions());
        StartCoroutine(SendBoxPositions());
        

    }

    

    void Update()
    {
        StartCoroutine(GetRobotPositions());
        StartCoroutine(SendRobotPositions());

    }

    /*              -----COROUTINES-----             */

    private IEnumerator InitializeModelOnServer()
    {
        UnityWebRequest request = UnityWebRequest.Get($"{serverURL}/initial");

        // Enviar la solicitud
        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError("Error al inicializar el modelo en el servidor: " + request.error);
        }
        else
        {
            Debug.Log("Modelo inicializado correctamente en el servidor.");
        }
    }

    
    IEnumerator SendRobotPositions()
    {
        // Asegurarse de que robotPositions no sea null o vacío
        if (robotPositions == null || robotPositions.Count == 0)
        {
            Debug.LogError("robotPositions no está inicializado o está vacío.");
            yield break;
        }

        var robotData = new List<Dictionary<string, object>>();

        foreach (var entry in robotPositions)
        {
            robotData.Add(new Dictionary<string, object>
            {
                {"id", entry.Key},
                {"position", new float[] {entry.Value.x, entry.Value.y, entry.Value.z}}
            });
        }

        // Serializar a JSON
        string json = JsonConvert.SerializeObject(new Wrapper<List<Dictionary<string, object>>>() { data = robotData });
        //Debug.Log("Robot Data: " + json);

        // Enviar a la ruta específica
        UnityWebRequest webRequest = new UnityWebRequest($"{serverURL}/robots", "POST");
        byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(json);

        webRequest.uploadHandler = new UploadHandlerRaw(jsonToSend);
        webRequest.downloadHandler = new DownloadHandlerBuffer();
        webRequest.SetRequestHeader("Content-Type", "application/json");

        yield return webRequest.SendWebRequest();

        if (webRequest.result == UnityWebRequest.Result.ConnectionError)
        {
            Debug.LogError("Error enviando datos de robots: " + webRequest.error);
        }
        else
        {
            Debug.Log("Datos de robots enviados exitosamente: " + webRequest.downloadHandler.text);
        }
    }

    IEnumerator GetRobotPositions()
    {
        UnityWebRequest webRequest = UnityWebRequest.Get($"{serverURL}/robots");
        yield return webRequest.SendWebRequest();

        if(webRequest.result == UnityWebRequest.Result.ConnectionError || webRequest.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError("Error: " + webRequest.error);
        }
        else
        {
            string jsonResponse = webRequest.downloadHandler.text;
            Debug.Log("Received JSON: " + jsonResponse);

            RobotData robotsData = JsonUtility.FromJson<RobotData>(jsonResponse);
            UpdateRobotPositions(robotsData);
        }
    }

    IEnumerator SendBoxPositions()
    {
        if (boxesManager == null)
        {
            Debug.LogError("boxesManager no está asignado.");
            yield break;
        }

        if (boxesManager.spawnedBoxes == null || boxesManager.spawnedBoxes.Count == 0)
        {
            Debug.LogError("spawnedBoxes está vacío o no inicializado.");
            yield break;
        }

        //Debug.Log($"Cantidad de cajas en spawnedBoxes: {boxesManager.spawnedBoxes.Count}");

        // Crea una lista para las cajas
        var boxList = new List<Dictionary<string, object>>();

        foreach (GameObject box in boxesManager.spawnedBoxes)
        {
            Vector3 pos = box.transform.position;
            boxList.Add(new Dictionary<string, object>
        {
            {"id", box.GetInstanceID()},
            {"position", new float[] {pos.x, pos.y, pos.z}}
        });
        }

        // Envuelve la lista en un objeto con clave "data"
        var payload = new Dictionary<string, object>
        {
            {"data", boxList}
        };

        string json = JsonConvert.SerializeObject(payload);
        //Debug.Log("Box Data JSON: " + json);

        // Enviar a la ruta específica
        UnityWebRequest webRequest = new UnityWebRequest($"{serverURL}/boxes", "POST");
        byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(json);

        webRequest.uploadHandler = new UploadHandlerRaw(jsonToSend);
        webRequest.downloadHandler = new DownloadHandlerBuffer();
        webRequest.SetRequestHeader("Content-Type", "application/json");

        yield return webRequest.SendWebRequest();

        if (webRequest.result == UnityWebRequest.Result.ConnectionError || webRequest.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError("Error enviando datos de cajas: " + webRequest.error);
        }
        else
        {
            Debug.Log("Datos de cajas enviados exitosamente: " + webRequest.downloadHandler.text);
        }
    }

    /*              ------HELPER FUNCTIONS------             */

    void UpdateRobotPositions(RobotData robotsData)
    {
        foreach (var robot in robotsData.robots)
        {
            Debug.Log($"Robot ID: {robot.id}, Position: {robot.position[0]}, {robot.position[1]}, {robot.position[2]}");
            Vector3 newPosition = new Vector3(robot.position[0], robot.position[1], robot.position[2]);
            MoveRobot(robot.id, newPosition);
        }
    }


    public void MoveRobot(int index, Vector3 newPosition)
    {
        // Forzar la posición Y a 0
        newPosition.y = 0;

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

[System.Serializable]
public class RobotData
{
    public Robot[] robots;
}

[System.Serializable]
public class Robot
{
    public int id;
    public float[] position;
}
