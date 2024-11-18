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
    public BoxesAppear boxesManager;
    string serverURL = "http://127.0.0.1:5000";

    public List<GameObject> robots;
    private Dictionary<int, Vector3> robotPositions = new Dictionary<int, Vector3>(); // Inicializaci�n aqu�

    public GameObject boxPrefab;


    //START FUN
    void Start()
    {
        robotPositions = new Dictionary<int, Vector3>();
        StartCoroutine(InitializeModelOnServer());

        for (int i = 0; i < robots.Count; i++)
        {
            GameObject robot = robots[i];
            int index = i + 1;
            Vector3 position = robot.transform.position;

            robotPositions.Add(index, position);
            Debug.Log($"Robot {index}: initial pos= {position}");

        }

        boxesManager.CreateBoxes();

        StartCoroutine(SendRobotPositions());
        StartCoroutine(SendBoxPositions());
    }

    //Vector3 Roboto1Pos = new Vector3(-10f, 0.0f, -11f);

    void Update()
    {
        //SendRobotPositons();
    }

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

    IEnumerator SendRobotPositions()
    {
        // Asegurarse de que robotPositions no sea null o vac�o
        if (robotPositions == null || robotPositions.Count == 0)
        {
            Debug.LogError("robotPositions no est� inicializado o est� vac�o.");
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
        Debug.Log("Robot Data: " + json);

        // Enviar a la ruta espec�fica
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

    IEnumerator SendBoxPositions()
    {
        if (boxesManager == null)
        {
            Debug.LogError("boxesManager no est� asignado.");
            yield break;
        }

        if (boxesManager.spawnedBoxes == null || boxesManager.spawnedBoxes.Count == 0)
        {
            Debug.LogError("spawnedBoxes est� vac�o o no inicializado.");
            yield break;
        }

        Debug.Log($"Cantidad de cajas en spawnedBoxes: {boxesManager.spawnedBoxes.Count}");

        var boxData = new List<Dictionary<string, object>>();

        foreach (GameObject box in boxesManager.spawnedBoxes)
        {
            Vector3 pos = box.transform.position;
            boxData.Add(new Dictionary<string, object>
            {
                {"id", box.GetInstanceID()},
                {"position", new float[] {pos.x, pos.y, pos.z}}
            });
        }

        string json = JsonConvert.SerializeObject(boxData);
        Debug.Log("Box Data: " + json);

        // Enviar a la ruta espec�fica
        UnityWebRequest webRequest = new UnityWebRequest($"{serverURL}/boxes", "POST");
        byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(json);

        webRequest.uploadHandler = new UploadHandlerRaw(jsonToSend);
        webRequest.downloadHandler = new DownloadHandlerBuffer();
        webRequest.SetRequestHeader("Content-Type", "application/json");

        yield return webRequest.SendWebRequest();

        if (webRequest.result == UnityWebRequest.Result.ConnectionError)
        {
            Debug.LogError("Error enviando datos de cajas: " + webRequest.error);
        }
        else
        {
            Debug.Log("Datos de cajas enviados exitosamente: " + webRequest.downloadHandler.text);
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
