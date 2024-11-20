from flask import Flask, jsonify, request
from agents import WarehouseModel  # Importar el modelo desde agents.py

app = Flask(__name__)

params = {
    "robotAgents": 5,
    "boxAgents": 5,  
    "shelfAgents": 6,
    "worldSize": (18, 20, 20),
}

model = None

@app.route("/initial", methods=["GET"])
def receive():
    global model
    model = WarehouseModel(params)
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
            robots_data = []
        for i, robot in enumerate(model.robots):
            if robot.is_carrying:  
                # Si el robot está cargando una caja, su target es el shelf asignado
                shelf = model.robot_shelf_map.get(robot)
                target_position = model.boxWorld.positions[shelf] if shelf else model.boxWorld.positions[robot]
            elif robot.target and isinstance(robot.target):  
                # Si el robot tiene una caja asignada como target
                target_position = robot.target.position
            else:  
                # Si el robot no tiene target asignado, se queda en su posición actual
                target_position = model.boxWorld.positions[robot]

            robots_data.append({
                "id": i + 1,
                "target": target_position,  # Devuelve solo coordenadas
            })
            
            print(robots_data)

        return jsonify({"robots": robots_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/boxes", methods=["POST", "GET"])
def handle_boxes():
    global model
    try:
        data = request.get_json()
        #print(f"Data received: {data}")

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

            # Map shelves by their index in the model
            shelf_map = {i + 1: shelf for i, shelf in enumerate(model.shelves)}

            for shelf_data in data.get("data", []):
                shelf_id = shelf_data.get("index")  # Shelf ID from Unity
                position = shelf_data.get("position")

                # Validate input data
                if shelf_id is None or not isinstance(position, list) or len(position) != 3:
                    print(f"Invalid shelf data: {shelf_data}")
                    continue

                try:
                    # Convert position to integers
                    position = tuple(int(round(coord)) for coord in position)
                except ValueError:
                    print(f"Invalid position format for shelf {shelf_id}: {position}")
                    continue

                # Check if the shelf ID is valid
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
            # Generate output data for the shelves
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






if __name__ == "__main__":
    app.run(debug=True)
