import agentpy as ap
from owlready2 import *

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

# ROBOT AGENT
class RobotAgent(ap.Agent):
    def setup(self):
        self.is_carrying = False
        self.target = None
        self.movements = 0

    def plan_path(self, boxes, shelves):
        if not self.is_carrying:
            available_boxes = [
                box for box in boxes 
                if box.position is not None and box not in self.model.assigned_targets
            ]
            if available_boxes:
                self.target = min(
                    available_boxes,
                    key=lambda box: self.model.boxWorld.get_distance(self, box)
                )
                self.model.assigned_targets.add(self.target)
            else:
                self.target = None

        else:
             assigned_shelf = self.model.robot_shelf_map[self]
             if assigned_shelf not in self.model.assigned_targets:
                self.target = assigned_shelf
                self.model.assigned_targets.add(self.target)

        print(f"Robot {self}: Target: {self.target}, Assigned Targets: {self.model.assigned_targets}")


    def step(self):
        if self.target:
            next_position = self.model.boxWorld.get_path(self, self.target)
            print(f"Robot {self}: Path to target {self.target} is {next_position}")

            if next_position:
                # Comprobar si la posición está ocupada por un estante
                if any(
                    self.model.boxWorld.positions[shelf] == next_position 
                    for shelf in self.model.shelves
                ):
                    # Intentar rodear el estante
                    alternative_path = self.find_alternative_path(next_position)
                    if alternative_path:
                        next_position = alternative_path

                # Mover al siguiente paso (si no está bloqueado)
                if self.model.boxWorld.is_empty(next_position):
                    fixed_position = (next_position[0], 0, next_position[2])  # Asegurar Y=0
                    self.model.boxWorld.move_to(self, fixed_position)
                    self.movements += 1

            # Lógica de carga y descarga
            if self.model.boxWorld.positions[self] == self.model.boxWorld.positions[self.target]:
                if isinstance(self.target, BoxAgent) and not self.is_carrying:
                    # Recoger caja
                    self.is_carrying = True
                    self.target.position = None
                    self.model.boxWorld.remove_agent(self.target)
                    self.target = None  # Reiniciar objetivo
                
                elif isinstance(self.target, ShelfAgent) and self.is_carrying:
                    # Dejar caja
                    self.is_carrying = False
                    shelf = self.target
                    shelf.add_box(self.target)  # Apilar caja en el estante
                    self.target = None  # Reiniciar objetivo

                    # Buscar nueva caja
                    self.plan_path(self.model.boxes, self.model.shelves)
        else:
            # Si no hay objetivo, buscar uno nuevo
            self.plan_path(self.model.boxes, self.model.shelves)

def find_alternative_path(self, blocked_position):
    """
    Encuentra una ruta alternativa alrededor de un estante.
    """
    adjacent_positions = self.model.boxWorld.get_neighborhood(
        blocked_position, distance=1, include_center=False
    )

    for pos in adjacent_positions:
        if self.model.boxWorld.is_empty(pos) and not any(
            self.model.boxWorld.positions[shelf] == pos for shelf in self.model.shelves
        ):
            return pos  # Devolver una posición alternativa válida

    return None  # Si no se encuentra alternativa




# BOX AGENT
class BoxAgent(ap.Agent):
    def setup(self):
        self.agentType = 1
        self.position = None  

    def set_position(self, position):
        self.position = position


# SHELF AGENT
class ShelfAgent(ap.Agent):
    def setup(self):
        self.agentType = 2
        self.stack = []  

    def add_box(self,box):
        self.stack.append(box)
        print(f"Caja {box} apilada en estante {self}")
        



# WAREHOUSE MODEL
class WarehouseModel(ap.Model):
    def setup(self):
        self.robots = ap.AgentList(self, self.p.robotAgents, RobotAgent)
        self.boxes = ap.AgentList(self, self.p.boxAgents, BoxAgent)
        self.shelves = ap.AgentList(self, self.p.shelfAgents, ShelfAgent)

        self.assigned_targets = set()
        self.robot_shelf_map = {}

        for i, robot in enumerate(self.robots):
            shelf = self.shelves[i % len(self.shelves)]
            self.robot_shelf_map[robot] = shelf

        self.boxWorld = ap.Grid(self, self.p.worldSize, track_empty=True)
        self.boxWorld.add_agents(self.robots, random=True, empty=True)
        self.boxWorld.add_agents(self.boxes, random=True, empty=True)
        for box in self.boxes:
            box.position = self.boxWorld.positions[box]
        self.boxWorld.add_agents(self.shelves, random=True, empty=True)

    def setup_shelves(self, shelf_positions):
        for index, shelf in enumerate(self.shelves):
            try:
                # Validate shelf_positions[index]
                if index >= len(shelf_positions):
                    raise ValueError(f"No position provided for shelf {index + 1}")
                shelf_data = shelf_positions[index]

                if "position" not in shelf_data or not isinstance(shelf_data["position"], (list, tuple)):
                    raise ValueError(f"Invalid position data for shelf {index + 1}: {shelf_data}")

                # Extract and convert position
                position = tuple(int(round(coord)) for coord in shelf_data["position"])

                # Check grid bounds
                if not self.boxWorld.in_bounds(position):
                    raise ValueError(f"Position {position} is out of grid bounds for shelf {index + 1}")

                # Move shelf to the specified position
                self.boxWorld.move_to(shelf, position)
                print(f"Shelf {index + 1} successfully moved to position {position}")

            except Exception as e:
                print(f"Error setting position for shelf {index + 1}: {e}")



    def step(self):
        print(f"Robot {self}: Position: {self.model.boxWorld.positions[self]}, Target: {self.target}")

        for robot in self.robots:
            if not robot.is_carrying:
                robot.plan_path(self.boxes, self.shelves)
            robot.step()

        self.handle_collisions()

        for box in self.boxes:
            if box.position is None:  # La caja está siendo transportada
                continue
            box.position = self.boxWorld.positions[box]

    def handle_collisions(self):
        position_map = {}

        # Mapear posiciones
        for robot in self.robots:
            pos = self.boxWorld.positions[robot]
            if pos in position_map:
                position_map[pos].append(robot)
            else:
                position_map[pos] = [robot]

        for pos, agents in position_map.items():
            if len(agents) > 1:  # Más de un robot en la misma posición
                self.resolve_collision(agents)

        # Detectar deadlocks: si hay muchos robots bloqueados sin moverse
        blocked_robots = [robot for robot in self.robots if robot.target is None]
        if len(blocked_robots) > len(self.robots) * 0.5:  # Porcentaje bloqueado
            print("Deadlock detected. Forcing global movement.")
            self.force_global_movement()

    def force_global_movement(self):
        for robot in self.robots:
            random_pos = self.boxWorld.get_random_position()
            self.boxWorld.move_to(robot, random_pos)
            robot.target = None


    def resolve_collision(self, agents):
        agents.sort(key=lambda x: x.movements)  # Priorizar robots con menos movimientos
        for robot in agents:
            empty_pos = self.find_empty_adjacent(robot)
            if empty_pos and empty_pos not in getattr(robot, "recent_positions", []):
                self.boxWorld.move_to(robot, empty_pos)
                robot.recent_positions = getattr(robot, "recent_positions", [])[-3:] + [empty_pos]
                robot.target = None  # Obligar a recalcular objetivo
            else:
                robot.wait_time = getattr(robot, "wait_time", 0) + 1
                if robot.wait_time > 3:  # Intentar buscar de nuevo después de algunos ciclos
                    robot.target = None
                    robot.wait_time = 0


    def find_empty_adjacent(self, agent, max_distance=3):
        for distance in range(1, max_distance + 1):
            adjacent_positions = self.boxWorld.get_neighborhood(
                self.boxWorld.positions[agent], distance=distance, include_center=False
            )
            for pos in adjacent_positions:
                if self.boxWorld.is_empty(pos) and not any(
                    self.boxWorld.positions[shelf] == pos for shelf in self.shelves
                ):
                    return pos
        return None



    def update(self):
        self.positions = {
            "robots": [self.boxWorld.positions[robot] for robot in self.robots],
            "boxes": [
            {"id": i, "position": (box.position if box.position is not None else "Carried")}
            for i, box in enumerate(self.boxes)
            ],
            "shelves": [
                {"id": i, "stack": len(shelf.stack), "position": self.boxWorld.positions[shelf]}
                for i, shelf in enumerate(self.shelves)
            ],
        }

    def end(self):
        total_movements = sum(robot.movements for robot in self.robots)
        print(f"Movimientos totales: {total_movements}")