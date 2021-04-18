from typing import Tuple
import numpy as np
from mesa import Agent, Model
from mesa.space import MultiGrid
import path_planning.Grid as path_env
from path_planning.Astar import astar


def contains_agent(grid: MultiGrid, pos: Tuple[int, int]):
    objs = grid.iter_cell_list_contents(pos)
    return any(map(lambda obj: issubclass(type(obj), Agent), objs))


class Warehouse:
    def __init__(
            self,
            pos: np.ndarray,
    ):
        self.pos = pos
        self.name = f"Warehouse {pos}"


class Car(Agent):
    def __init__(self,
                 unique_id: int,
                 pos: Tuple[int, int],
                 model: Model):
        super().__init__(unique_id, model)
        self.name = f"Car {unique_id}"
        self.pos = pos
        self.curr_load = 0
        self.max_load = 1
        self.target = None
        self.pathing = None
        self.is_resupplying = False

    def step(self):
        if self.target is None:
            if self.curr_load <= self.max_load * 0.5:
                self.target = self.model.find_closest_warehouse(self.pos)
                self.is_resupplying = True
            else:
                # Assign target
                self.target = self.model.allocation[self]
                self.target.assign(self)

            self.pathing = astar(
                path_env.Grid(self.model.obstacle_matrix),
                self.pos,
                self.target.pos
            )[1:]

        if self.model.collision:
            new_pos = self.pathing[0]
            if contains_agent(self.model.grid, new_pos):
                neighbor = self.model.grid.get_neighborhood(self.pos, moore=False)
                neighbor = list(filter(lambda pos: not contains_agent(self.model.grid, pos), neighbor))
                if self.model.random.randint(0, 1) == 1 or len(neighbor) == 0:
                    return
                else:
                    divert = self.model.random.choice(neighbor)
                    self.pathing = [divert, self.pos] + self.pathing

        self.model.grid.move_agent(self, self.pathing[0])
        self.pathing = self.pathing[1:]

        if self.pos == self.target.pos:
            if type(self.target) is Warehouse:
                self.curr_load = self.max_load
                self.is_resupplying = False
            else:
                work = min(self.curr_load, self.target.value)
                finished_task = self.target.do_work(work, self)
                if finished_task:
                    self.model.allocation_flag = True
                self.curr_load -= work

            self.target = None


class Truck(Agent):
    def __init__(self,
                 unique_id: int,
                 pos: np.ndarray,
                 model: Model):
        super().__init__(unique_id, model)
        self.name = f"Truck {unique_id}"
        self.pos = pos
        self.curr_load = 0
        self.max_load = 3
        self.target = None
        self.pathing = None
        self.is_waiting = True
        self.is_resupplying = False

    def step(self):
        if self.target is None:
            if self.curr_load <= self.max_load * 0.5:
                self.target = self.model.find_closest_warehouse(self.pos)
                self.is_resupplying = True
            else:
                # Assign target
                self.target = self.model.allocation[self]
                self.target.assign(self)

            self.pathing = astar(
                path_env.Grid(self.model.obstacle_matrix),
                self.pos,
                self.target.pos
            )[1:]

        self.is_waiting = not self.is_waiting

        if self.is_waiting:
            return

        if self.model.collision:
            new_pos = self.pathing[0]
            if contains_agent(self.model.grid, new_pos):
                neighbor = self.model.grid.get_neighborhood(self.pos, moore=False)
                neighbor = list(filter(lambda pos: not contains_agent(self.model.grid, pos), neighbor))
                if self.model.random.randint(0, 1) == 1 or len(neighbor) == 0:
                    return
                else:
                    divert = self.model.random.choice(neighbor)
                    self.pathing = [divert, self.pos] + self.pathing

        self.model.grid.move_agent(self, self.pathing[0])
        self.pathing = self.pathing[1:]

        if self.pos == self.target.pos:
            if type(self.target) is Warehouse:
                self.curr_load = self.max_load
                self.is_resupplying = False
            else:
                work = min(self.curr_load, self.target.value)
                finished_task = self.target.do_work(work, self)
                if finished_task:
                    self.model.allocation_flag = True
                self.curr_load -= work

            self.target = None
