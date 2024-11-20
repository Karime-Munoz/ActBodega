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


    def step(self):
        if self.target:
            next_position = self.model.boxWorld.get_path(self, self.target)
            if next_position:
                if not any(
                self.model.boxWorld.positions[shelf] == next_position 
                for shelf in self.model.shelves
            ):
                    fixed_position = (next_position[0], 0, next_position[2])  # Y = 0
                    self.model.boxWorld.move_to(self, fixed_position)
                    self.movements += 1

            #Lógica de carga y descarga
            if self.model.boxWorld.positions[self] == self.model.boxWorld.positions[self.target]:
                if isinstance(self.target, BoxAgent) and not self.is_carrying:
                    self.is_carrying = True # Recoger caja
                    self.target.position = None
                    self.model.boxWorld.remove_agent(self.target)
                    self.target = None   
            
                elif isinstance(self.target, ShelfAgent) and self.is_carrying:
                    self.is_carrying = False
                    shelf = self.target
                    shelf.add_box(self.target)  # Apilar caja en el estante
                    self.target = None

                    self.plan_path(self.model.boxes, self.model.shelves)
        else:
            self.plan_path(self.model.boxes, self.model.shelves)




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
        for robot in self.robots:
            if not robot.is_carrying:
                robot.plan_path(self.boxes, self.shelves)
            robot.step()

        self.handle_collisions()

    def handle_collisions(self):
        position_map = {}
        
        #Robots al mapa
        for robot in self.robots:
            pos = self.boxWorld.positions[robot]
            if pos in position_map:
                position_map[pos].append(robot)
            else:
                position_map[pos] = [robot]

        #Estantes al mapa
        for shelf in self.shelves:
            pos = self.boxWorld.positions[shelf]
            if pos in position_map:
                position_map[pos].append(shelf)
            else:
                position_map[pos] = [shelf]

        for pos, agents in position_map.items():
            if len(agents) > 1:
                self.resolve_collision(agents)

    def resolve_collision(self, agents):
        for robot in agents:
            empty_pos = self.find_empty_adjacent(robot)
            if empty_pos:
                self.boxWorld.move_to(robot, empty_pos)
            robot.target = None  # Obligarlos a reevaluar su objetivo

    def find_empty_adjacent(self, agent):
        adjacent_positions = self.boxWorld.get_neighborhood(
            self.boxWorld.positions[agent], distance=1, include_center=False
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