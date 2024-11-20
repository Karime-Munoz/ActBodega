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

    public GameObject boxPrefab;

    public List<GameObject> robots;
    public List<GameObject> shelves;
    public List<Transform> shelfPositions; 
    private Dictionary<int, Vector3> robotPositions = new Dictionary<int, Vector3>(); // Inicialización aquí

    public BoxesAppear boxesManager;

    private bool isUpdatingPositions = false;

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
        
        StartCoroutine(InitializeAndSendData());


        

    }

    private float updateInterval = 1f; // Intervalo en segundos
    private float lastUpdate = 0;

    void Update()
    {
        if (Time.time - lastUpdate >= updateInterval && !isUpdatingPositions)
        {
            StartCoroutine(UpdateRobotPositions());
            lastUpdate = Time.time;
        }

    }

    /*              -----COROUTINES-----             */

    IEnumerator InitializeAndSendData()
    {
        // Llamar primero a /initial
        yield return StartCoroutine(InitializeModelOnServer());

        // Una vez inicializado, enviar las posiciones de robots, cajas y estantes
        yield return StartCoroutine(SendRobotPositions());
        yield return StartCoroutine(SendBoxPositions());
        yield return StartCoroutine(SendShelfPositions());

        Debug.Log("Inicialización y envío de datos completados.");
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

        foreach (var entry in robotPositions)
        {
            Debug.Log($"Unity Robot {entry.Key} Pos: {entry.Value}");
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
            Debug.LogError("Respuesta del servidor: " + webRequest.downloadHandler.text);
        }
        else
        {
            string jsonResponse = webRequest.downloadHandler.text;
            Debug.Log("Received JSON: " + jsonResponse);

            RobotData robotsData = JsonUtility.FromJson<RobotData>(jsonResponse);
            UpRobotPositions(robotsData);
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

        int index = 1;
        foreach (GameObject box in boxesManager.spawnedBoxes)
        {
            Vector3 pos = box.transform.position;
            float x = Mathf.Round(pos.x * 100f) / 100f;
            float y = Mathf.Round(pos.y * 100f) / 100f;
            float z = Mathf.Round(pos.z * 100f) / 100f;

            boxList.Add(new Dictionary<string, object>
        {
            {"id", index++},
            {"position", new float[] {x, y, z}}
        });
        }

        // Envuelve la lista en un objeto con clave "data"
        var payload = new Dictionary<string, object>
        {
            {"data", boxList}
        };

        string json = JsonConvert.SerializeObject(payload);
        Debug.Log("Box Data JSON: " + json);

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
            Debug.LogError("Respuesta del servidor: " + webRequest.downloadHandler.text);
        }
        else
        {
            Debug.Log("Datos de cajas enviados exitosamente: " + webRequest.downloadHandler.text);
        }
    }

    IEnumerator SendShelfPositions()
    {
        if (shelves == null || shelves.Count == 0)
        {
            Debug.LogError("No se han asignado estantes.");
            yield break;
        }

        var shelfList = new List<Dictionary<string, object>>();

        int index = 1;
        foreach (GameObject shelf in shelves)
        {
            Vector3 pos = shelf.transform.position;
            float x = Mathf.Round(pos.x * 100f) / 100f;
            float y = 0.0f;
            float z = Mathf.Round(pos.z * 100f) / 100f;

            shelfList.Add(new Dictionary<string, object>
        {
            {"index", index++},
            {"position", new float[] {x, y, z}}
        });
        }

        var payload = new Dictionary<string, object>
    {
        {"data", shelfList}
    };

        string json = JsonConvert.SerializeObject(payload);
        Debug.Log("JSON generado para estantes: " + json);

        UnityWebRequest webRequest = new UnityWebRequest($"{serverURL}/shelves", "POST");
        byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(json);

        webRequest.uploadHandler = new UploadHandlerRaw(jsonToSend);
        webRequest.downloadHandler = new DownloadHandlerBuffer();
        webRequest.SetRequestHeader("Content-Type", "application/json");

        yield return webRequest.SendWebRequest();

        if (webRequest.result == UnityWebRequest.Result.ConnectionError || webRequest.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError("Error enviando datos de estantes: " + webRequest.error);
            Debug.LogError("Respuesta del servidor: " + webRequest.downloadHandler.text);
        }
        else
        {
            Debug.Log("Datos de estantes enviados exitosamente: " + webRequest.downloadHandler.text);
        }
    }

    IEnumerator UpdateRobotPositions()
    {
        isUpdatingPositions = true;

        // Llamada a la API para obtener las nuevas posiciones de los robots
        yield return StartCoroutine(GetRobotPositions());

        // Procesar datos y asignar nuevas posiciones
        foreach (KeyValuePair<int, Vector3> entry in robotPositions)
        {
            int robotIndex = entry.Key;
            Vector3 targetPos = entry.Value;

            if (entry.Key - 1 >= robots.Count)
            {
                Debug.LogError($"El índice {robotIndex} no corresponde a ningún robot en la lista.");
                continue;
            }

            GameObject robot = robots[robotIndex - 1];
            RobotController controller = robot.GetComponent<RobotController>();

            if (controller != null && !controller.IsMoving())
            {
                // Cuando el robot llega al objetivo, asignar nueva posición
                controller.SetTargetPosition(targetPos);
                Debug.Log($"Robot {robotIndex} assigned new target: {targetPos}");
            }
        }

        isUpdatingPositions = false;
    }




    /*              ------HELPER FUNCTIONS------             */

    void UpRobotPositions(RobotData robotsData)
    {
        if (robotsData == null || robotsData.robots.Length == 0)
        {
            Debug.LogWarning("No se recibieron datos de robots.");
            return;
        }

        foreach (var robot in robotsData.robots)
        {
            if (robot.target.Length != 3)
            {
                Debug.LogWarning($"El robot {robot.id} tiene datos incompletos.");
                continue;
            }

            Vector3 newPosition = new Vector3(robot.target[0], robot.target[1], robot.target[2]);
            MoveRobot(robot.id, newPosition);
        }
    }

    public void PickUpBox(GameObject robot)
    {
        float pickUpRange = 1.5f; // Rango para recoger cajas
        foreach (GameObject box in boxesManager.spawnedBoxes)
        {
            if (box != null && Vector3.Distance(robot.transform.position, box.transform.position) <= pickUpRange)
            {
                Debug.Log($"Robot {robot.name} recogió una caja.");
                box.SetActive(false);
                boxesManager.spawnedBoxes.Remove(box); // Remover caja de la lista
                Destroy(box); // Desaparecer la caja
                PlaceBoxOnShelf(robot); // Coloca la caja en un estante
                return;
            }
        }
    }

    public void PlaceBoxOnShelf(GameObject robot)
    {
        foreach (GameObject shelf in shelves)
        {
            ShelfController shelfController = shelf.GetComponent<ShelfController>();

            if (shelfController == null || !shelfController.HasAvailableSlot()) continue;

            Vector3 shelfPosition = shelfController.GetNextAvailableSlot();
            GameObject newBox = Instantiate(boxPrefab, shelfPosition, Quaternion.identity);
            newBox.transform.SetParent(shelf.transform);
            shelfController.AddBoxToShelf(newBox);

            Debug.Log($"Caja colocada en el estante en posición {shelfPosition} por el robot {robot.name}");
            return;
        }

        Debug.LogWarning("No hay espacio disponible en los estantes.");
    }


    public void MoveRobot(int index, Vector3 newPosition)
    {
        newPosition.y = 0;
        if (robotPositions.ContainsKey(index))
        {
            robotPositions[index] = newPosition;

            GameObject robot = robots[index - 1];
            RobotController controller = robot.GetComponent<RobotController>();

            if (controller != null)
            {
                controller.SetTargetPosition(newPosition);
                //Debug.Log($"Robot {index} moving to {newPosition}");
            }
            PickUpBox(robot);
            //Debug.Log($"Robot {index} moved to {newPosition}");
        }
        else
        {
            Debug.LogError($"Robot {index} not found");
        }
    }


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
    public float[] target;
}
