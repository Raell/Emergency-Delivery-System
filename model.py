from typing import Tuple
from mesa import Model, Agent
from mesa.time import SimultaneousActivation
from mesa.space import ContinuousSpace
from mesa.datacollection import DataCollector
import numpy as np


def check_collision(pos1, pos2, dist=1):
    x1, y1 = pos1
    x2, y2 = pos2
    return abs(x1 - x2) < dist or abs(y1 - y2) < dist


class Car(Agent):
    def __init__(self, unique_id: int, pos: np.ndarray, model: Model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.speed = 0.1
        self.curr_load = 0
        self.max_load = 1
        self.target = None

    def pick_up(self, load):
        self.curr_load += load

    def drop_off(self, load):
        self.curr_load -= load

    def step(self):
        if self.target is None:
            # Assign target
            self.target = self.model.random.choice(self.model.tasks)

        # Move towards target
        grad = self.target.pos - self.pos
        norm = np.linalg.norm(grad)
        if norm > 1:
            grad = grad / np.linalg.norm(grad)
            self.pos += grad * self.speed


class Truck(Agent):
    def __init__(self, unique_id: int, pos: np.ndarray, model: Model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.speed = 0.04
        self.curr_load = 0
        self.max_load = 3
        self.target = None

    def pick_up(self, load):
        self.curr_load += load

    def drop_off(self, load):
        self.curr_load -= load

    def step(self):
        if self.target is None:
            # Assign target
            self.target = self.model.random.choice(self.model.tasks)

        # Move towards target
        grad = self.target.pos - self.pos
        norm = np.linalg.norm(grad)
        if norm > 1:
            grad = grad / np.linalg.norm(grad)
            self.pos += grad * self.speed


class Job(Agent):
    def __init__(self, unique_id: int, pos: Tuple[int, int], value: int, priority: int, model: Model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.value = value
        self.priority = priority

    def do_work(self, work):
        self.value -= work

    def step(self):
        #  Move towards target
        if self.value == 0:
            self.model.tasks_left -= 1
            self.model.tasks.remove(self)


class Warehouse(Agent):
    def __init__(self, unique_id: int, pos: Tuple[int, int], model: Model):
        super().__init__(unique_id, model)
        self.pos = pos

    def step(self):
        pass


class DeliveryModel(Model):
    """
    Model class for the Delivery model.
    """

    def __init__(self, space_size=20, jobs=10, agents=5, warehouses=1, split=0.4):

        self.space_size = space_size
        self.tasks = []
        self.task_left = jobs
        self.warehouses = []

        self.schedule = SimultaneousActivation(self)
        self.space = ContinuousSpace(space_size, space_size, torus=False)
        self.datacollector = DataCollector(
            {"tasks_left": "tasks_left"},
            {"x": lambda a: a.pos[0], "y": lambda a: a.pos[1]},
        )

        # Set up agents
        for i in range(agents):
            # Agents have a fixed diameter of 1
            x = self.random.random() * (self.space.x_max - 1) + 0.5
            y = self.random.random() * (self.space.y_max - 1) + 0.5
            pos = np.array([x, y])

            while True:
                # Check if new position collides with other agents
                has_collision = any(
                    map(
                        lambda a: check_collision(a.pos, pos),
                        self.schedule.agents
                    )
                )

                if not has_collision:
                    break

                x = self.random.random() * (self.space.x_max - 1) + 0.5
                y = self.random.random() * (self.space.y_max - 1) + 0.5
                pos = np.array([x, y])

            if i < split * agents:
                # Add Truck agent
                agent = Truck(i, pos, self)

            else:
                # Add Car agent
                agent = Car(i, pos, self)

            self.space.place_agent(agent, pos)
            self.schedule.add(agent)

        # Set up jobs
        for val in range(jobs):
            x = self.random.random() * (self.space.x_max - 1.5) + 0.75
            y = self.random.random() * (self.space.y_max - 1.5) + 0.75
            pos = np.array([x, y])

            while True:
                # Check if new position collides with other agents
                has_collision = any(
                    map(
                        lambda a: check_collision(a.pos, pos, self.space_size/20),
                        self.tasks
                    )
                )

                if not has_collision:
                    break

                x = self.random.random() * (self.space.x_max - 1) + 0.5
                y = self.random.random() * (self.space.y_max - 1) + 0.5
                pos = np.array([x, y])

            job = Job(agents + val, pos, self.random.randint(1, 9), self.random.randint(1, 3), self)
            self.tasks.append(job)
            self.space.place_agent(job, pos)
            self.schedule.add(job)

        # Set up warehouses
        for w in range(warehouses):
            # Agents have a fixed diameter of 1
            x = self.random.random() * (self.space.x_max - 1) + 0.5
            y = self.random.random() * (self.space.y_max - 1) + 0.5
            pos = np.array([x, y])

            while True:
                # Check if new position collides with other agents
                has_collision = any(
                    map(
                        lambda a: check_collision(a.pos, pos, self.space_size/100),
                        self.warehouses
                    )
                )

                has_collision = has_collision or any(
                    map(
                        lambda a: check_collision(a.pos, pos, self.space_size/20),
                        self.tasks
                    )
                )

                if not has_collision:
                    break

                x = self.random.random() * (self.space.x_max - 1) + 0.5
                y = self.random.random() * (self.space.y_max - 1) + 0.5
                pos = np.array([x, y])

            warehouse = Warehouse(agents + jobs + w, pos, self)
            self.warehouses.append(warehouse)
            self.space.place_agent(warehouse, pos)
            self.schedule.add(warehouse)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
        if self.task_left == 0:
            self.running = False


# class SchellingAgent(Agent):
#     """
#     Schelling segregation agent
#     """
#
#     def __init__(self, pos, model, agent_type):
#         """
#         Create a new Schelling agent.
#
#         Args:
#            unique_id: Unique identifier for the agent.
#            x, y: Agent initial location.
#            agent_type: Indicator for the agent's type (minority=1, majority=0)
#         """
#         super().__init__(pos, model)
#         self.pos = pos
#         self.type = agent_type
#
#     def step(self):
#         similar = 0
#         for neighbor in self.model.grid.neighbor_iter(self.pos):
#             if neighbor.type == self.type:
#                 similar += 1
#
#         # If unhappy, move:
#         if similar < self.model.homophily:
#             self.model.grid.move_to_empty(self)
#         else:
#             self.model.happy += 1
#

# class Schelling(Model):
#     """
#     Model class for the Schelling segregation model.
#     """
#
#     def __init__(self, height=20, width=20, density=0.8, minority_pc=0.2, homophily=3):
#         """"""
#
#         self.height = height
#         self.width = width
#         self.density = density
#         self.minority_pc = minority_pc
#         self.homophily = homophily
#
#         self.schedule = RandomActivation(self)
#         self.grid = SingleGrid(width, height, torus=True)
#
#         self.happy = 0
#         self.datacollector = DataCollector(
#             {"happy": "happy"},  # Model-level count of happy agents
#             # For testing purposes, agent's individual x and y
#             {"x": lambda a: a.pos[0], "y": lambda a: a.pos[1]},
#         )
#
#         # Set up agents
#         # We use a grid iterator that returns
#         # the coordinates of a cell as well as
#         # its contents. (coord_iter)
#         for cell in self.grid.coord_iter():
#             x = cell[1]
#             y = cell[2]
#             if self.random.random() < self.density:
#                 if self.random.random() < self.minority_pc:
#                     agent_type = 1
#                 else:
#                     agent_type = 0
#
#                 agent = SchellingAgent((x, y), self, agent_type)
#                 self.grid.position_agent(agent, (x, y))
#                 self.schedule.add(agent)
#
#         self.running = True
#         self.datacollector.collect(self)
#
#     def step(self):
#         """
#         Run one step of the model. If All agents are happy, halt the model.
#         """
#         self.happy = 0  # Reset counter of happy agents
#         self.schedule.step()
#         # collect data
#         self.datacollector.collect(self)
#
#         if self.happy == self.schedule.get_agent_count():
#             self.running = False
