# Librerias
import agentpy as ap
from owlready2 import *
from flask import Flask,jsonify,request



"""                            ----FLASK SERVER------                       """

app = Flask(__name__)

model = None

@app.route("/initial", methods=["GET"])
def receive():
    global model
    params = {
            "robotAgents": 5,
            "boxAgents": 15,  
            "shelfAgents": 9,
            "worldSize": (20, 20, 20),
        }
    
    model = WarehouseModel(params)
    model.setup()
    return jsonify({f"Modelo inicializado"})

@app.route("/robots", methods=["POST", "GET"])
def handle_robots():
    global model
    try:
        if model is None:
            return jsonify({"message": "Model not initialized"}), 400

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
        if model is None:
            return jsonify({"message": "Model not initialized"}), 400

        if request.method == "POST":
            data = request.get_json()
            for box_data in data.get("boxes", []):
                box_id = box_data.get("id", None)
                position = box_data.get("position", [])
                if box_id is None or len(position) != 3:
                    return jsonify({"error": f"Invalid box data: {box_data}"}), 400
                
                position = tuple(float(coord) for coord in position)
                box_index = box_id - 1
                if 0 <= box_index < len(model.boxes):
                    model.boxWorld.move_to(model.boxes[box_index], position)
                else:
                    return jsonify({"error": f"Box index {box_index} out of range"}), 400
            
            return jsonify({"message": "Box positions updated"}), 200

        elif request.method == "GET":
            boxes_data = [
                {"id": i + 1, "position": model.boxWorld.positions[box]}
                for i, box in enumerate(model.boxes)
            ]
            return jsonify({"boxes": boxes_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route("/step", methods=['POST'])
def step():
    data = request.json
    robots = [item for item in data['data'] if item['type'] == 'robot']
    boxes = [item for item in data['data'] if item['type'] == 'box']

    print("Robots:")
    for robot in robots:
        print(f"ID: {robot['id']}, Position: {robot['position']}")

    print("Boxes:")
    for box in boxes:
        print(f"ID: {box['id']}, Position: {box['position']}")

    return jsonify({"message": "Data received successfully"}), 200




"""                            ----ONTOLOGIA------                       """
onto = get_ontology("file:///content/robots_ontology.owl")

with onto:

  class Entity(Thing):
    pass

  class Robot(Entity):
    pass

  class Box(Entity):
    pass

  class Shelf(Entity):
    pass

  class WareHouse(Thing):
    pass

  # AGREGAR PROPIEDADES

  class has_position(DataProperty, FunctionalProperty):
    domain = [Thing]
    range = [str]

  class has_id(DataProperty, FunctionalProperty):
    domain = [Entity]
    range = [int]

  class is_carrying(ObjectProperty, FunctionalProperty):
    domain = [Robot]
    range = [Box]



"""                           -----AGENTES------                       """
#ROBOT AGENT
class RobotAgent(ap.Agent):
    def setup(self):
        self.is_carrying = False
        self.targetBox = None
        self.path = []
        self.movements = 0  # Contador de movimientos

    def see(self):
        # Detectar agentes en las posiciones cercanas
        nearby = self.model.boxWorld.neighbors(self, distance=1)
        observations = {
            "boxes": [agent for agent in nearby if isinstance(agent, BoxAgent)],
            "shelves": [agent for agent in nearby if isinstance(agent, ShelfAgent)],
            "robots": [agent for agent in nearby if isinstance(agent, RobotAgent) and agent != self]
        }
        return observations

    def pick_box(self):
        if not self.is_carrying and self.targetBox:
            current_pos = self.model.boxWorld.positions[self]
            target_pos = self.model.boxWorld.positions[self.targetBox]
            if current_pos == target_pos:
                self.is_carrying = True
                self.targetBox = None
                print(f"Robot {self.id} ha recogido una caja.")

    def move(self):
        if self.path:
            move = self.path.pop(0)
            new_position = (
                max(0, min(move[0], self.model.p.worldSize[0] - 1)),
                max(0, min(move[1], self.model.p.worldSize[1] - 1)),
                max(0, min(move[2], self.model.p.worldSize[2] - 1)),
            )
            self.model.boxWorld.move_to(self, new_position)
            self.movements += 1  # Incrementar movimientos

    def calculate_alternate_path(self, target_pos, obstacles):
        current_pos = self.model.boxWorld.positions[self]
        # Generar un camino alternativo básico rodeando el obstáculo
        if obstacles:
            for obstacle in obstacles:
                obs_pos = self.model.boxWorld.positions[obstacle]
                # Evitar la posición del obstáculo moviéndote a una posición adyacente válida
                if obs_pos[0] > current_pos[0]:
                    target_pos = (current_pos[0] - 1, current_pos[1], current_pos[2])
                elif obs_pos[0] < current_pos[0]:
                    target_pos = (current_pos[0] + 1, current_pos[1], current_pos[2])
        return target_pos

    def plan_path(self, target_pos):
        current_pos = self.model.boxWorld.positions[self]
        dx, dy, dz = (
            target_pos[0] - current_pos[0],
            target_pos[1] - current_pos[1],
            target_pos[2] - current_pos[2],
        )
        self.path = [(current_pos[0] + dx, current_pos[1], current_pos[2])] * abs(dx) + \
                    [(current_pos[0], current_pos[1] + dy, current_pos[2])] * abs(dy) + \
                    [(current_pos[0], current_pos[1], current_pos[2] + dz)] * abs(dz)

    def step(self):
        observations = self.see()
        if not self.is_carrying:
            if not self.targetBox and observations["boxes"]:
                self.targetBox = observations["boxes"][0]
            if self.targetBox:
                target_pos = self.model.boxWorld.positions[self.targetBox]
                obstacles = observations["shelves"]  # Detectar estantes como obstáculos
                if obstacles:
                    target_pos = self.calculate_alternate_path(target_pos, obstacles)
                self.plan_path(target_pos)
            self.move()
            self.pick_box()
            


#BOX AGENT
class BoxAgent(ap.Agent):
  def setup(self):
        self.agentType = 1
        self.position = None  

  def set_position(self, position):
      self.position = position

  def step(self):
      pass  # Las cajas no hacen nada en este modelo

#SHELF
class ShelfAgent(ap.Agent):
  def setup(self):
    self.agentType = 2

  def step(self):
    pass

  def update(self):
    pass

  def end(self):
    pass

"""                            ----MODELO------                       """
class WarehouseModel(ap.Model):
    def setup(self):
        # Diccionario para almacenar las posiciones de los agentes
        self.positions = {}

        # Crear los robots, cajas y estantes
        self.robots = ap.AgentList(self, self.p.robotAgents, RobotAgent)
        self.boxes = ap.AgentList(self, self.p.boxAgents, BoxAgent)
        self.shelves = ap.AgentList(self, self.p.shelfAgents, ShelfAgent)

        # Crear el grid
        self.boxWorld = ap.Grid(self, self.p.worldSize, track_empty=True)

        # Agregar los agentes
        self.boxWorld.add_agents(self.robots, random=True, empty=True)
        self.boxWorld.add_agents(self.boxes, random=True, empty=True)
        self.boxWorld.add_agents(self.shelves, random=True, empty=True)

        # Inicializar posiciones
        self.update_positions()

    def update_positions(self):
        """Actualizar el diccionario de posiciones."""
        self.positions = {
            agent: self.boxWorld.positions[agent]
            for agent in self.robots + self.boxes + self.shelves
        }

    def step(self):
        # Actualizar posiciones al final de cada paso
        self.robots.step()
        self.update_positions()





"""                           -----MAIN-----                       """
if __name__ == "__main__":
    app.run(debug=True)