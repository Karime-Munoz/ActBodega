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
            self.target = min(boxes, key=lambda box: self.model.boxWorld.get_distance(self, box))
        else:
            self.target = min(shelves, key=lambda shelf: self.model.boxWorld.get_distance(self, shelf))

    def step(self):
        if self.target:
            next_position = self.model.boxWorld.get_path(self, self.target)
            if next_position:
                # Asegúrate de que la posición Y permanezca fija
                fixed_position = (next_position[0], 0, next_position[2])  # Y = 0
                self.model.boxWorld.move_to(self, fixed_position)
                self.movements += 1

        # Lógica de carga y descarga
        if self.model.boxWorld.positions[self] == self.model.boxWorld.positions[self.target]:
            if not self.is_carrying:
                self.is_carrying = True  # Recoger caja
            else:
                self.is_carrying = False  # Dejar caja
                self.target = None



# BOX AGENT
class BoxAgent(ap.Agent):
    def setup(self):
        self.agentType = 1
        self.position = None  

    def set_position(self, position):
        self.position = position

    def step(self):
        pass  # Las cajas no hacen nada en este modelo


# SHELF AGENT
class ShelfAgent(ap.Agent):
    def setup(self):
        self.agentType = 2

    def step(self):
        pass


# WAREHOUSE MODEL
class WarehouseModel(ap.Model):
    def setup(self):
        self.robots = ap.AgentList(self, self.p.robotAgents, RobotAgent)
        self.boxes = ap.AgentList(self, self.p.boxAgents, BoxAgent)
        self.shelves = ap.AgentList(self, self.p.shelfAgents, ShelfAgent)

        self.boxWorld = ap.Grid(self, self.p.worldSize, track_empty=True)
        self.boxWorld.add_agents(self.robots, random=True, empty=True)
        self.boxWorld.add_agents(self.boxes, random=True, empty=True)
        self.boxWorld.add_agents(self.shelves, random=True, empty=True)

    def step(self):
        for robot in self.robots:
            if not robot.is_carrying:
                robot.plan_path(self.boxes, self.shelves)
            robot.step()

        self.handle_collisions()

    def handle_collisions(self):
        position_map = {}
        for robot in self.robots:
            pos = self.boxWorld.positions[robot]
            if pos in position_map:
                position_map[pos].append(robot)
            else:
                position_map[pos] = [robot]

        for pos, agents in position_map.items():
            if len(agents) > 1:
                self.resolve_collision(agents)

    def resolve_collision(self, agents):
        for robot in agents:
            new_position = self.find_empty_adjacent(robot)
            if new_position:
                self.boxWorld.move_to(robot, new_position)

    def find_empty_adjacent(self, agent):
        adjacent_positions = self.boxWorld.get_neighborhood(
            self.boxWorld.positions[agent], distance=1, include_center=False
        )
        for pos in adjacent_positions:
            if self.boxWorld.is_empty(pos):
                return pos
        return None

    def update(self):
        self.positions = {
            "robots": [self.boxWorld.positions[robot] for robot in self.robots],
            "boxes": [self.boxWorld.positions[box] for box in self.boxes],
            "shelves": [self.boxWorld.positions[shelf] for shelf in self.shelves],
        }

    def end(self):
        total_movements = sum(robot.movements for robot in self.robots)
        print(f"Movimientos totales: {total_movements}")
