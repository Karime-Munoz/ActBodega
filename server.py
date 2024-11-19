from flask import Flask, jsonify, request
from agents import WarehouseModel  # Importar el modelo desde agents.py

app = Flask(__name__)

params = {
    "robotAgents": 5,
    "boxAgents": 15,  
    "shelfAgents": 9,
    "worldSize": (20, 20, 20),
}

model = WarehouseModel(params)

@app.route("/initial", methods=["GET"])
def receive():
    global model
    model.setup()
    return jsonify({"message": "Modelo inicializado"})

@app.route("/robots", methods=["POST", "GET"])
def handle_robots():
    global model
    try:
        if request.method == "POST":
            data = request.get_json()
            for robot_data in data.get("robots", []):
                index = robot_data.get("index", None)
                position = robot_data.get("position", [])
                if index is None or len(position) != 3:
                    return jsonify({"error": f"Invalid robot data: {robot_data}"}), 400
                
                position = tuple(float(coord) for coord in position)
                robot_index = index - 1
                if 0 <= robot_index < len(model.robots):
                    model.boxWorld.move_to(model.robots[robot_index], position)
                else:
                    return jsonify({"error": f"Robot index {robot_index} out of range"}), 400
            
            return jsonify({"message": "Robot positions updated"}), 200

        elif request.method == "GET":
            robots_data = [
                {"id": i + 1, "position": model.boxWorld.positions[robot]}
                for i, robot in enumerate(model.robots)
            ]
            return jsonify({"robots": robots_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/boxes", methods=["POST", "GET"])
def handle_boxes():
    global model
    try:
        data = request.get_json()  # Obtén el JSON enviado por Unity
        box_list = data.get("data", [])  # Cambia "boxes" a "data"
        
        # Procesa cada caja
        for box_data in box_list:
            box_id = box_data.get("id")
            position = box_data.get("position")
            print(f"Processing box {box_id} at position {position}")
            # Realiza cualquier otra operación necesaria con los datos
        
        return jsonify({"message": "Datos de cajas procesados exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    

if __name__ == "__main__":
    app.run(debug=True)
