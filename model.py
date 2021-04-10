import cProfile
import sys
from typing import Tuple, Optional
from mesa import Model, Agent
from mesa.time import SimultaneousActivation
from mesa.space import ContinuousSpace, Grid
from mesa.datacollection import DataCollector
import numpy as np
from scipy.signal import convolve2d
import task_allocation
from path_planning.CBS import cbs
import path_planning.Grid as path_env


def check_collision(pos1, pos2, dist=1):
    x1, y1 = pos1
    x2, y2 = pos2
    return abs(x1 - x2) < dist or abs(y1 - y2) < dist


class Car(Agent):
    def __init__(self,
                 unique_id: int,
                 pos: np.ndarray,
                 # grid_pos: np.ndarray,
                 model: Model):
        super().__init__(unique_id, model)
        self.pos = pos
        # self.grid_pos = grid_pos
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
            self.target = self.model.task_allocator.allocate_jobs(
                self.model.tasks
            )

        # # Move towards target
        # grad = self.target.pos - self.pos
        # norm = np.linalg.norm(grad)
        # if norm > 1:
        #     grad = grad / np.linalg.norm(grad)
        #     self.pos += grad * self.speed


class Truck(Agent):
    def __init__(self,
                 unique_id: int,
                 pos: np.ndarray,
                 # grid_pos: np.ndarray,
                 model: Model):
        super().__init__(unique_id, model)
        self.pos = pos
        # self.grid_pos = grid_pos
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
            self.target = self.model.task_allocator.allocate_jobs(
                self.model.tasks
            )

        else:
            # Move using pathing
            pass

        # # Move towards target
        # grad = self.target.pos - self.pos
        # norm = np.linalg.norm(grad)
        # if norm > 1:
        #     grad = grad / np.linalg.norm(grad)
        #     self.pos += grad * self.speed


class Job(Agent):
    def __init__(
            self,
            pos: np.ndarray,
            # grid_pos: np.ndarray,
            value: int,
            priority: int
    ):
        self.pos = pos
        # self.grid_pos = grid_pos
        self.value = value
        self.priority = priority
        self.assigned = []

    def do_work(self, work):
        self.value -= work

    def assign(self, agent):
        self.assigned.append(agent)

    def step(self):
        if self.value == 0:
            self.model.tasks_left -= 1
            self.model.tasks.remove(self)
            for agent in self.assigned:
                agent.target = None


class Warehouse(Agent):
    def __init__(
            self,
            pos: np.ndarray,
            # grid_pos: np.ndarray,
    ):
        self.pos = pos
        # self.grid_pos = grid_pos

    def step(self):
        pass


class Obstacle(Agent):
    def __init__(self, pos):
        self.pos = pos
        # self.grid_pos = grid_pos
        # self.size = size


def generate_map(obstacle_map):
    with open(obstacle_map) as f:
        lines = [line.rstrip() for line in f]
        lines = lines[4:]
        lines = [[0 if c == "." else 1 for c in line] for line in lines]

    return np.array(lines, dtype=np.bool)

class DeliveryModel(Model):
    """
    Model class for the Delivery model.
    """

    def __init__(
            self,
            space_size=32,
            jobs=30,
            agents=1,
            warehouses=1,
            split=0.4,
            use_seed=True,
            seed: int = 42,
            obstacle_map: str = "maps/random-32-32-20.map",
            task_allocation: str = "RandomAllocation"
    ):
        if use_seed:
            self.random.seed(seed)
        else:
            self.random.seed(None)
        self.space_size = space_size
        self.tasks = []
        self.tasks_left = jobs
        self.warehouses = []
        self.num_agents = agents

        self.schedule = SimultaneousActivation(self)
        self.grid = Grid(space_size, space_size, torus=False)
        self.datacollector = DataCollector(
            {"tasks_left": "tasks_left"},
            {"x": lambda a: a.pos[0], "y": lambda a: a.pos[1]},
        )

        self.obstacle_matrix = generate_map(obstacle_map)
        self.obstacles = self.__set_obstacle__()
        # self.minkowski_grid = self.__calculate_minkowski__()
        self.__set_up__(agents, warehouses, split)

        self.__add_jobs__(min(2 * agents, jobs))

        self.task_allocator = getattr(
            sys.modules["task_allocation"],
            task_allocation
        )(self.random)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        if len(self.tasks) < self.num_agents * 2 and self.tasks_left > len(self.tasks):
            self.__add_jobs__(self.num_agents * 2 - len(self.tasks))

        self.schedule.step()
        print("Step")

        starts = []
        targets = []
        for agent in self.schedule.agents:
            starts.append(agent.pos)
            targets.append(agent.target.pos)
        # dimension = (self.grid.width, self.grid.height)
        #
        # agents = [
        #     {
        #         'start': agent.pos,
        #         'goal': agent.target.pos,
        #         'name': agent.unique_id
        #      }
        #     for agent in self.schedule.agents
        # ]
        #
        # obstacles = [obs.pos for obs in self.obstacles]
        #
        # env = Environment(dimension, agents, obstacles)

        # Searching
        grid = path_env.Grid(self.obstacle_matrix)
        paths = cbs(grid, starts, targets)
        print(paths)

        # self.schedule.step()
        # self.datacollector.collect(self)
        # if self.task_left == 0:
        #     self.running = False

    def __set_obstacle__(self):
        obstacles = []
        for i, j in zip(*np.where(self.obstacle_matrix == 1)):
            obs = Obstacle((i, j))
            obstacles.append(obs)
            self.grid.place_agent(obs, (i, j))
        return obstacles

    def __set_up__(self, agents, warehouses, split):

        # Pick empty spots for warehouses
        conv = convolve2d(self.obstacle_matrix, np.ones((3, 3)), mode="valid")
        free_indices = np.argwhere(conv == 0)
        samples = self.random.choices(free_indices, k=warehouses)

        for sample in samples:
            i, j = sample + 1
            warehouse = Warehouse((i, j))
            self.grid.place_agent(warehouse, (i, j))

        # Pick empty spots for agents
        samples = self.random.choices(list(self.grid.empties), k=agents)

        for a, sample in enumerate(samples):
            i, j = sample
            if a < split * agents:
                # Add Truck agent
                agent = Truck(a, (i, j), self)
            else:
                # Add Car agent
                agent = Car(a, (i, j), self)
            self.grid.place_agent(agent, (i, j))
            self.schedule.add(agent)

    def __add_jobs__(self, jobs):
        # Set up jobs
        samples = self.random.choices(list(self.grid.empties), k=jobs)

        for sample in samples:
            i, j = sample
            job = Job((i, j), self.random.randint(1, 9), self.random.randint(1, 3))
            self.tasks.append(job)
            self.grid.place_agent(job, (i, j))
