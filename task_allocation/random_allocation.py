from task_allocation.allocation import Allocation


class RandomAllocation(Allocation):
    def __init__(self, randomizer, agents, jobs):
        super().__init__()
        if len(agents) == len(jobs):
            matching = randomizer.sample(jobs, k=len(agents))
        else:
            matching = randomizer.choices(jobs, k=len(agents))
        self.allocation = {
            agent: job
            for agent, job in zip(agents, matching)
        }

    def get_allocation(self):
        return self.allocation
