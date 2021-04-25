from copy import copy

from agents import Truck
from task_allocation.allocation import Allocation
import numpy as np
from scipy.optimize import linear_sum_assignment


def generate_matrix(agents, jobs):
    cost_matrix = np.zeros((len(agents), len(jobs)))

    priority_scale = {
        1: 0.4,
        2: 1,
        3: 3
    }

    for i, agent in enumerate(agents):
        for j, job in enumerate(jobs):
            current_pos = agent.pos if not agent.is_resupplying else agent.target.pos
            dist = np.sum(np.abs(np.array(current_pos) - np.array(job.pos)))
            if type(agent) is Truck:
                dist *= 2
            finish_job = 0.8 if agent.curr_load >= job.value else 1
            cost_matrix[i, j] = dist * finish_job * priority_scale[job.priority]

    return cost_matrix


class HungarianMethod(Allocation):
    def __init__(self, randomizer, agents, jobs):
        super().__init__()
        # self.job_list = copy(jobs)
        self.job_list = sorted(
            jobs,
            key=lambda j: (j.priority, -j.value)
        )[:len(agents)]
        self.agents = agents
        cost_matrix = generate_matrix(self.agents, self.job_list)

        if len(agents) != len(self.job_list):
            # Assume jobs <= agents
            # Clone highest priority job to fill matrix
            # If multiple jobs of same priority choose highest value
            num_clones = len(agents) - len(jobs)
            job_order = sorted(
                enumerate(jobs),
                key=lambda j: (j[1].priority, -j[1].value)
            )
            indices = [i[0] for i in job_order[:num_clones]]
            new_cols = cost_matrix[:, indices]
            while num_clones > 0:
                cost_matrix = np.concatenate((cost_matrix, new_cols[:, :num_clones]), axis=1)
                self.job_list += [i[1] for i in job_order[:num_clones]]
                num_clones -= len(job_order)

        self.allocation = self.__calculate_allocation__(cost_matrix)

    def __calculate_allocation__(self, cost_matrix):
        indices = linear_sum_assignment(cost_matrix)
        assignment = {self.agents[i]: self.job_list[j] for i, j in zip(*indices)}
        return assignment

    def get_allocation(self):
        return self.allocation
