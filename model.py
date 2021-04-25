import sys
from typing import Tuple

import numpy as np
from mesa import Model, Agent
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from scipy.signal import convolve2d
import task_allocation
from agents import Car, Truck, Warehouse
from metrics.metrics import PrioritisedTaskTime


class Job:
    def __init__(
            self,
            pos: np.ndarray,
            value: int,
            priority: int,
            model: Model
    ):
        self.name = f"Job {priority}-{pos}"
        self.pos = pos
        self.value = value
        self.priority = priority
        self.assigned = []
        self.model = model
        self.time_waiting = 0
        self.is_available = False

    def do_work(self, work, agent):
        self.value -= work
        self.assigned.remove(agent)
        return self.value == 0

    def assign(self, agent):
        self.assigned.append(agent)

    def step(self):
        if self.is_available:
            self.time_waiting += 1
        if self.value == 0:
            self.model.score.process_completed_task(self)
            self.model.tasks_left -= 1
            self.model.available_tasks.remove(self)
            self.model.grid.remove_agent(self)
            for agent in self.assigned:
                agent.target = None


class Obstacle(Agent):
    def __init__(self, pos):
        self.pos = pos


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
            allocation: str = "HungarianMethod",
            collision=True
    ):
        if use_seed:
            self.random.seed(seed)
        else:
            self.random.seed(None)
        self.space_size = space_size
        self.tasks_left = jobs
        self.warehouses = []
        self.num_agents = agents
        self.agents = []
        self.collision = collision

        self.allocation_flag = True
        self.allocator = getattr(
            sys.modules["task_allocation"],
            allocation
        )
        self.allocation = None

        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(space_size, space_size, torus=False)
        self.datacollector = DataCollector(
            {"tasks_left": "tasks_left"},
            {"x": lambda a: a.pos[0], "y": lambda a: a.pos[1]},
        )

        self.obstacle_matrix = generate_map(obstacle_map)
        self.obstacles = self.__set_obstacle__()
        self.__set_up__(agents, warehouses, split)

        self.hidden_tasks = self.__preload_jobs__()
        # self.available_tasks = self.__add_jobs__(min(2*agents, jobs))
        self.available_tasks = self.__add_jobs__(min(10, jobs))



        self.task_allocator = None
        self.score = PrioritisedTaskTime()

        self.running = True
        self.datacollector.collect(self)

    def __preload_jobs__(self):
        jobs = []
        samples = self.random.choices(list(self.grid.empties), k=self.tasks_left)

        for sample in samples:
            i, j = sample
            job = Job((i, j), self.random.randint(1, 9), self.random.randint(1, 3), self)
            jobs.append(job)
        return jobs

    def find_closest_warehouse(self, pos):
        min_dist = np.inf
        closest = None
        for w in self.warehouses:
            dist = np.sum(np.abs(np.array(w.pos) - np.array(pos)))
            if dist < min_dist:
                min_dist = dist
                closest = w
        return closest

    def step(self):
        # if len(self.available_tasks) < 2*self.num_agents and self.tasks_left > len(self.available_tasks):
        if len(self.available_tasks) < 10 and self.tasks_left > len(self.available_tasks):
            self.available_tasks += self.__add_jobs__(self.num_agents - len(self.available_tasks))

        if self.allocation_flag:
            self.allocation_flag = False
            self.allocation = self.allocator(
                self.random,
                self.agents,
                self.available_tasks
            ).get_allocation()

        self.schedule.step()

        for j in self.available_tasks:
            j.step()

        self.datacollector.collect(self)
        if self.tasks_left == 0:
            self.running = False
            print(self.score.get_score())
            print(self.score.get_avg_wait_time())

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
            self.warehouses.append(warehouse)

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
            self.agents.append(agent)

    def __add_jobs__(self, jobs):
        new_jobs = self.hidden_tasks[:jobs]
        self.hidden_tasks = self.hidden_tasks[jobs:]
        for job in new_jobs:
            job.is_available = True
            self.grid.place_agent(job, job.pos)
        return new_jobs
