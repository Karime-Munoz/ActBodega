from flask import Flask, jsonify, request
from agents import WarehouseModel  # Importar el modelo desde agents.py

app = Flask(__name__)

params = {
    "robotAgents": 5,
    "boxAgents": 5,  
    "shelfAgents": 5,
    "worldSize": (20, 20, 20),
}

model = WarehouseModel(params)

@app.route("/initial", methods=["GET"])
def receive():
    global model
    model.setup()
    return jsonify({"message ": "Modelo inicializado"})

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
        data = request.get_json()
        print(f"Data received: {data}")

        box_list = data.get("data", [])
        box_map = {box.id: box for box in model.boxes}  # Mapeo de cajas por ID

        for box_data in box_list:
            box_id = box_data.get("id")
            position = box_data.get("position")

            # Validaciones
            if box_id is None:
                print("Missing box ID")
                continue
            if not isinstance(position, list) or len(position) < 2:
                print(f"Invalid position for box {box_id}: {position}")
                continue

            print(f"Processing box {box_id} with position {position}")

            if box_id not in box_map:
                #print(f"Box ID {box_id} not found in model.boxes")
                continue

            box_agent = box_map[box_id]

            try:
                box_agent.set_position(position)
            except Exception as e:
                print(f"Error setting position for box {box_id}: {e}")
                continue

            try:
                model.boxWorld.move_to(box_agent, tuple(position[:2]))
            except Exception as e:
                print(f"Error moving box {box_id} to position {tuple(position[:2])}: {e}")
                continue

        return jsonify({"message": "Datos de cajas procesados exitosamente"}), 200
    except Exception as e:
        print("Error procesando datos de cajas:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/shelves", methods=["POST", "GET"])
def handle_shelves():
    global model
    try:
        if request.method == "POST":
            data = request.get_json()
            #print(f"Data received for shelves: {data}")

            # Mapeo de estantes por su índice en el modelo
            shelf_map = {i + 1: shelf for i, shelf in enumerate(model.shelves)}

            for shelf_data in data.get("data", []):
                shelf_id = shelf_data.get("index")  # ID de estante enviado desde Unity
                position = shelf_data.get("position")

                # Validar datos de entrada
                if shelf_id is None or not isinstance(position, list) or len(position) != 3:
                    print(f"Invalid shelf data: {shelf_data}")
                    continue

                try:
                    position = tuple(float(coord) for coord in position)
                except ValueError:
                    print(f"Invalid position format for shelf {shelf_id}: {position}")
                    continue

                # Verificar si el ID de estante es válido
                if shelf_id not in shelf_map:
                    print(f"Shelf ID {shelf_id} not found in model.shelves")
                    continue

                shelf_agent = shelf_map[shelf_id]

                try:
                    model.boxWorld.move_to(shelf_agent, position)
                    print(f"Shelf {shelf_id} moved to position {position}")
                except Exception as e:
                    print(f"Error moving shelf {shelf_id} to position {position}: {e}")
                    continue

            return jsonify({"message": "Shelf positions updated successfully"}), 200

        elif request.method == "GET":
            # Generar datos de salida para los estantes
            shelves_data = [
                {
                    "id": i + 1,
                    "position": model.boxWorld.positions[shelf],
                    "stack": len(shelf.stack),
                }
                for i, shelf in enumerate(model.shelves)
            ]
            print(f"Shelves data sent: {shelves_data}")
            return jsonify({"shelves": shelves_data}), 200

    except Exception as e:
        print("Error handling shelves:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/unused_shelves", methods=["POST"])
def handle_unused_shelves():
    global model
    try:
        if request.method == "POST":
            data = request.get_json()
            shelf_map = {i + 1: shelf for i, shelf in enumerate(model.unused_shelves)}

            for shelf_data in data.get("data", []):
                shelf_id = shelf_data.get("index")
                position = shelf_data.get("position")

                if shelf_id is None or not isinstance(position, list) or len(position) != 3:
                    return jsonify({"error": f"Invalid shelf data: {shelf_data}"}), 400

                position = tuple(float(coord) for coord in position)

                if shelf_id not in shelf_map:
                    return jsonify({"error": f"Shelf ID {shelf_id} not found"}), 404

                shelf_agent = shelf_map[shelf_id]
                model.boxWorld.move_to(shelf_agent, position)

            return jsonify({"message": "Unused shelf positions updated"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/state", methods=["GET"])
def get_state():
    global model
    try:
        return jsonify(model.positions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)
