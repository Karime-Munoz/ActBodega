using UnityEngine;
using System.IO;
using System.Net.Sockets;
using System.Linq;

public class RobotCamera : MonoBehaviour
{
    public Camera robotCamera;  // Cámara del robot
    public RenderTexture renderTexture;  // RenderTexture donde se renderiza la cámara
    public string pythonServerIP = "127.0.0.1";  // IP del servidor Python
    public int pythonServerPort = 12345;  // Puerto del servidor Python

    private TcpClient client;
    private NetworkStream stream;
    private BinaryWriter writer;

    void Start()
    {
        // Conectar al servidor Python
        try
        {
            client = new TcpClient(pythonServerIP, pythonServerPort);
            stream = client.GetStream();
            writer = new BinaryWriter(stream);
            Debug.Log($"Conectado a Python en {pythonServerIP}:{pythonServerPort}");
        }
        catch (SocketException e)
        {
            Debug.LogError($"Error al conectar con Python: {e.Message}");
        }
    }

    void Update()
    {
        if (client != null && stream != null)
        {
            CaptureAndSendImage();
        }
    }

    void CaptureAndSendImage()
    {
        Texture2D texture = new Texture2D(renderTexture.width, renderTexture.height, TextureFormat.RGB24, false);
        RenderTexture.active = renderTexture;
        texture.ReadPixels(new Rect(0, 0, renderTexture.width, renderTexture.height), 0, 0);
        texture.Apply();
        RenderTexture.active = null;

        byte[] imageBytes = texture.EncodeToPNG();

        try
        {
            writer.Write(System.BitConverter.GetBytes(imageBytes.Length).Reverse().ToArray());
            writer.Write(imageBytes);
        }
        catch (IOException e)
        {
            Debug.LogError($"Error al enviar la imagen: {e.Message}");
        }

        Destroy(texture);
    }

    void OnApplicationQuit()
    {
        if (writer != null) writer.Close();
        if (stream != null) stream.Close();
        if (client != null) client.Close();
        Debug.Log("Conexión cerrada con el servidor Python.");
    }
}